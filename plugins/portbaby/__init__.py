"""Portbaby v1.0.0 — Syntax version porting for E Language.
Converts projects between v1 machine, v1 human, v2, v3, and v4 syntax.
Reports loss percentage. Generates proper multi-file project structure."""

import os
import sys

VERSION = "1.0.0"
author = "Tentari"
description = "Syntax version porting for E Language"


def register(api):
    api.add_command("portbaby", _cmd, "Portbaby: portbaby <file> --to <version> [--project] [--report]")
    api.add_command("pb", _cmd, "Portbaby alias: pb <file> --to <version>")
    api.add_help_section("Portbaby Commands", [
        ("portbaby <file> --to <version>", "Convert file to target syntax version (v1/v2/v3/v4)"),
        ("portbaby <file> --to v1_human", "Convert to v1 human-readable syntax"),
        ("portbaby <file> --to v1_machine", "Convert to v1 machine token syntax"),
        ("portbaby <file> --to v3 --project", "Convert to v3 with multi-file project structure"),
        ("portbaby <file> --report", "Show loss percentage without converting"),
        ("portbaby update <project.ei>", "Update old project to latest syntax"),
        ("portbaby batch <glob> --to v3", "Batch convert multiple files"),
    ])
    api.add_boot_step("Portbaby ready", "done")


# Available version targets
VALID_TARGETS = {"v1_machine", "v1_human", "v1", "v2", "v3", "v4", "v4_human"}
VERSION_ORDER = {"v1_machine": 0, "v1_human": 1, "v1": 2, "v2": 3, "v3": 4, "v4": 5}


def _resolve_version(name):
    """Resolve version name to canonical form."""
    name = name.lower().replace("-", "_")
    if name in ("machine", "v1_machine", "v1machine"):
        return "v1_machine"
    if name in ("human", "v1_human", "v1human"):
        return "v1_human"
    if name in ("v1",):
        return "v1_human"
    if name in ("v2", "semantic"):
        return "v2"
    if name in ("v3", "shorthand"):
        return "v3"
    if name in ("v4", "latest", "current"):
        return "v4"
    if name in ("v4_human", "v4human"):
        return "v4_human"
    return None


def _cmd(args):
    if not args:
        print("  Usage: portbaby <spec> --to <version> [--project] [--report] [--recursive]")
        print(f"  Versions: v1_machine, v1_human, v2, v3, v4, v4_human")
        print(f"  <spec>: file | dir | / (all) | glob | multiple specs")
        print(f"  Flags: --project  Generate multi-file project structure")
        print(f"         --report   Show conversion report only")
        print(f"         --recursive  Include subdirectories for dirs and '/'")
        print(f"  Examples:")
        print(f"    portbaby song.e --to v3")
        print(f"    portbaby song.e --to v1_human")
        print(f"    portbaby project.ei --to v4 --project")
        print(f"    portbaby song.e --to v3 --report")
        print(f"    portbaby samples/v4-current --to v3")
        print(f"    portbaby / --to v4 --recursive")
        return

    # Flags
    rest = [a for a in args if not a.startswith("--")]
    recursive = "--recursive" in args
    show_report = "--report" in args
    make_project = "--project" in args

    target_ver = None
    if "--to" in args:
        idx = args.index("--to")
        if idx + 1 < len(args):
            target_ver = _resolve_version(args[idx + 1])
    if not target_ver:
        print(f"  Specify target version: --to v3")
        return

    # Smart path resolution (files, dirs, '/', globs, multiple specs)
    try:
        from ep_compiler.paths import resolve_inputs, batch_suffix
    except ImportError:
        resolve_inputs = None

    specs = rest if rest else ["/"]
    if resolve_inputs:
        sources = resolve_inputs(specs, recursive=recursive)
    else:
        sources = [s.strip("\"'") for s in specs if os.path.exists(s.strip("\"'"))]

    if not sources:
        print(f"  Not found: {' '.join(specs)}")
        return
    if len(sources) > 1:
        print(f"  {len(sources)} file(s) matched.")

    from .converter import convert_file

    for source in sources:
        if target_ver == "v1" and _resolve_version("v1") == "v1_human":
            pass
        result = convert_file(source, target_ver, make_project=make_project, show_report=show_report)

        if result and not show_report:
            output = result.get("output", "")
            if output:
                print(f"  ✓ Converted: {source} → {target_ver}")
                print(f"  Output: {output}")
            else:
                # Fallback naming for batch safety
                tag = target_ver.replace("_", "")
                print(f"  ✓ Converted: {source} → {batch_suffix(source, tag)}")
            if "report" in result:
                _print_report(result["report"])


def _print_report(report):
    """Print a conversion report."""
    print(f"\n  Conversion Report:")
    print(f"    Source version: {report.get('source_ver', '?')}")
    print(f"    Target version: {report.get('target_ver', '?')}")
    print(f"    Loss: {report.get('loss_pct', 0)}%")
    if report.get('issues'):
        for issue in report['issues'][:5]:
            print(f"    \u26a0 {issue}")
    print(f"    Events: {report.get('events_in', 0)} \u2192 {report.get('events_out', 0)}")
