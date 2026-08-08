""".enx format — Enhanced root index. Plays .ei files in order
with tempo overrides and delays between entries. Strips comments,
detects circular references via DAG.

Syntax:
  #ENX v1
  project "Album Name"
  composer "AI"

  order "song1/song1.ei"
  order "song2/song2.ei" at 2000ms
  order "song3/song3.ei" tempo 140

  section "Intro" {
      order "intro.ei" tempo 80
  }
"""
import os
import re
from .comments import strip_comments
from .graph import CircularReferenceError

ENX_HEADER_RE = re.compile(r'#ENX\s+v(\d+)', re.I)
ENX_ORDER_RE = re.compile(r'order\s+"([^"]+)"(?:\s+at\s+(\d+)ms?)?(?:\s+tempo\s+([\d.]+))?', re.I)
ENX_SECTION_RE = re.compile(r'section\s+"([^"]+)"\s*\{', re.I)
ENX_PROJECT_RE = re.compile(r'project\s+"([^"]+)"', re.I)
ENX_COMPOSER_RE = re.compile(r'composer\s+"([^"]+)"', re.I)


def parse_enx(path):
    """Parse a .enx file. Returns list of (ei_path, delay_ms, tempo_override) tuples."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return _parse_enx_text(text, os.path.dirname(os.path.abspath(path)))


def _parse_enx_text(text, base_dir):
    """Parse raw .enx text (comments stripped). Returns list of (resolved_path, delay_ms, tempo_override)."""
    text = strip_comments(text)
    orders = []
    in_section = False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ENX_SECTION_RE.match(line):
            in_section = True
            continue
        if line == "}":
            in_section = False
            continue
        m = ENX_ORDER_RE.match(line)
        if m:
            rel = m.group(1)
            delay = int(m.group(2)) if m.group(2) else 0
            tempo = float(m.group(3)) if m.group(3) else None
            full = os.path.normpath(os.path.join(base_dir, rel))
            orders.append((full, delay, tempo))
    return orders


def read_enx_meta(path):
    """Read .enx metadata without parsing orders. Returns dict with project, composer, text."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = ENX_PROJECT_RE.search(text)
    project = m.group(1) if m else ""
    m = ENX_COMPOSER_RE.search(text)
    composer = m.group(1) if m else ""
    return {"project": project, "composer": composer, "text": text}


def _compile_order(path, bpm, graph):
    """Compile a single ordered file, dispatching by extension.
    Avoids circular import by doing lazy imports."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".enx":
        return compile_enx(path, bpm, graph)
    elif ext == ".ei":
        from .e_runtime import compile_ei_file
        return compile_ei_file(path, bpm)
    elif ext == ".eci":
        from .compile import compile_eci as _ceci
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return _ceci(text, bpm)
    elif ext in (".e", ".eic"):
        from .compile import compile_source
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        return compile_source(text, bpm)
    return [], bpm


def compile_enx(path, bpm_override=None, graph=None):
    """Compile a .enx file into events. Returns (events, bpm).
    Handles nested .enx references (via _compile_order dispatch).
    Uses optional graph for cross-format cycle detection."""
    from .events import (
        sort_events,
        validate_events,
    )

    orders = parse_enx(path)
    all_events = []
    global_cursor = 0
    current_bpm = bpm_override or 120

    for order_path, delay, tempo in orders:
        bpm = tempo or current_bpm
        if graph:
            try:
                graph.enter(order_path)
            except CircularReferenceError:
                raise
        try:
            ev, bp = _compile_order(order_path, bpm, graph)
        finally:
            if graph:
                graph.exit()
        if tempo:
            current_bpm = tempo
        for e in ev:
            e["timestamp"] += global_cursor + delay
        if ev:
            global_cursor = max(e["timestamp"] + e["duration"] for e in ev)
        all_events.extend(ev)

    all_events = sort_events(all_events)
    all_events, _ = validate_events(all_events)
    return all_events, current_bpm
