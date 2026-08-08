"""Core conversion engine — parses source, dispatches to version converter, emits output."""

import os
import sys
import tempfile
from ep_compiler.compile import (
    compile_source,
    detect_syntax_version,
    compile_file as compile_auto,
)
from ep_compiler.import_midi import events_to_e_source


def convert_file(path, target_ver, make_project=False, show_report=False):
    """Convert a single file to target version. Returns result dict."""
    ext = os.path.splitext(path)[1].lower()
    source_text = None
    events = []
    bpm = 120

    # Parse source to events
    if ext in (".e", ".ei", ".eci", ".enx", ".eic"):
        events, bpm = compile_auto(path)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            source_text = f.read()
    else:
        print(f"  Unsupported format: {ext}")
        return None

    source_ver = detect_syntax_version(source_text) if source_text else "v1"
    # Normalize version names
    ver_map = {"v1_machine": "v1_machine", "v1_human": "v1_human", "v1": "v1_human",
               "v3": "v3", "v2": "v2", "v4": "v4"}
    source_ver_norm = ver_map.get(source_ver, "v1_human")

    if not events:
        print(f"  No events found in {path}")
        return None

    report = {
        "source_ver": source_ver_norm,
        "target_ver": target_ver,
        "events_in": len(events),
        "events_out": 0,
        "loss_pct": 0,
        "issues": [],
    }

    if show_report:
        from .loss_calculator import calculate_loss
        loss_info = calculate_loss(source_ver_norm, target_ver, events)
        report.update(loss_info)
        return {"report": report}

    # Convert events to target version source
    if target_ver == "v1_machine":
        output_text = events_to_e_source(events, bpm, human=False)
    elif target_ver in ("v1_human", "v1"):
        output_text = events_to_e_source(events, bpm, human=True)
    else:
        # v4_human uses a different converter
        if target_ver == "v4_human":
            from .v1_to_v4 import convert_human
            output_text = convert_human(events, bpm, source_text or "")
        else:
            output_text = _route_conversion(source_ver_norm, target_ver, events, bpm, source_text or "")

    if not output_text:
        print(f"  Conversion failed: {source_ver_norm} \u2192 {target_ver}")
        return None

    report["events_out"] = len(events)
    from .loss_calculator import calculate_loss
    loss_info = calculate_loss(source_ver_norm, target_ver, events)
    report.update(loss_info)

    # Handle project generation
    output_path = None
    if make_project and target_ver in ("v2", "v3", "v4"):
        from .project_builder import build_project
        output_path = build_project(path, output_text, events, bpm, target_ver, source_ver_norm)
    else:
        base = os.path.splitext(path)[0]
        output_path = f"{base}_{target_ver}.e"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)

    return {"output": output_path, "report": report}


def _route_conversion(source_ver, target_ver, events, bpm, source_text):
    """Route to the appropriate version converter module."""
    converters = {
        ("v1_machine", "v2"): "v1_to_v2",
        ("v1_human", "v2"): "v1_to_v2",
        ("v1_machine", "v3"): "v1_to_v3",
        ("v1_human", "v3"): "v1_to_v3",
        ("v1_machine", "v4"): "v1_to_v4",
        ("v1_human", "v4"): "v1_to_v4",
        ("v2", "v1_machine"): "v2_to_v1",
        ("v2", "v1_human"): "v2_to_v1",
        ("v2", "v3"): "v2_to_v3",
        ("v2", "v4"): "v2_to_v4",
        ("v3", "v1_machine"): "v3_to_v1",
        ("v3", "v1_human"): "v3_to_v1",
        ("v3", "v2"): "v3_to_v2",
        ("v3", "v4"): "v3_to_v4",
        ("v4", "v3"): "v4_to_v3",
        ("v4", "v2"): "v4_to_v2",
        ("v4", "v1_machine"): "v4_to_v1",
        ("v4", "v1_human"): "v4_to_v1",
    }

    key = (source_ver, target_ver)
    module_name = converters.get(key)
    if not module_name:
        # Try reverse conversion (v3 ↔ v1 via events)
        if target_ver in ("v1_machine", "v1_human", "v1"):
            return events_to_e_source(events, bpm, human=(target_ver != "v1_machine"))
        return None

    try:
        mod = __import__(f"plugins.portbaby.{module_name}", fromlist=[""])
        return mod.convert(events, bpm, source_text)
    except Exception as e:
        # Fallback: emit as v1_human
        print(f"  \u26a0 {module_name} converter error: {e}")
        return events_to_e_source(events, bpm, human=True)
