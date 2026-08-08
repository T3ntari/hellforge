#!/usr/bin/env python3
"""HELLFORGE LSP Bridge — JSON-RPC bridge between the VS Code extension and the
real E compiler. Provides context-aware completions, hover docs, diagnostics,
symbols, and definitions using the actual compiler, not a reimplementation.

Protocol: one JSON object per line (JSON-RPC-ish):
  {"method": "get_completions", "params": {"text": ..., "line": N, "char": C}}
  {"method": "get_hover", "params": {"text": ..., "line": N, "char": C}}
  {"method": "get_diagnostics", "params": {"text": ...}}
  {"method": "get_symbols", "params": {"text": ...}}
  {"method": "get_definition", "params": {"text": ..., "line": N, "char": C}}
  {"method": "get_format", "params": {"text": ...}}
Response: {"result": ...} or {"error": ...}

Performance notes:
  - text.split("\n") is computed once per request and passed down.
  - Hover docs are a module-level constant (not rebuilt per keystroke).
  - Context detection strips comments so comments never trigger autocomplete.
"""

import os
import re
import sys
import json

# ── HELLFORGE root detection (works installed as a VSIX or from source) ──

_COMMON_ROOTS = [
    "~/Downloads/E/piano-dsl",
    "~/Downloads/E",
    "~/piano-dsl",
    "~/hellforge",
    "~/projects/hellforge",
    "C:/hellforge",
    "C:/E",
    "D:/piano-dsl",
    "D:/hellforge",
    "D:/E",
]


def _expand_home(p):
    if p.startswith("~/"):
        home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or ""
        return os.path.join(home, p[2:])
    return p


def _is_root(d):
    return any(os.path.isfile(os.path.join(d, m)) for m in ("ep.py", "run.py", "eshell.py"))


def _find_project_root():
    """Locate the real HELLFORGE project root for compiler imports.
    Tries: cwd parents → HELLFORGE_HOME → file location parents → common paths."""
    # 1. Walk up from cwd
    d = os.path.abspath(os.getcwd())
    for _ in range(12):
        if _is_root(d):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # 2. Env var
    env = os.environ.get("HELLFORGE_HOME")
    if env and _is_root(env):
        return env
    # 3. Walk up from this file (tools/ or server/resources/)
    d = os.path.dirname(os.path.abspath(__file__))
    for _ in range(10):
        if _is_root(d):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # 4. Common paths
    for c in _COMMON_ROOTS:
        p = _expand_home(c)
        if _is_root(p):
            return p
    return None


PROJECT = _find_project_root()
if PROJECT and PROJECT not in sys.path:
    sys.path.insert(0, PROJECT)

from ep_compiler.compile import compile_source
from ep_compiler.math_engine import (
    build_ast,
    ast_to_dict,
    find_expressions,
    is_var_definition,
    parse_var_definition,
)

DIRECTIVES = ["@bpm", "@tempo", "@key", "@scale", "@vol", "@volume", "@gc",
              "@dur", "@vel", "@ch", "@prob", "@probability", "@curve", "@mode",
              "@random", "@pan", "@reverb", "@delay"]
KEYWORDS = ["play", "note", "chord", "for", "repeat", "while", "to", "step",
            "do", "if", "else", "inherit", "track", "title", "composer"]
MATH_FUNCS = ["sin", "cos", "sqrt", "pow", "round", "floor", "abs", "min",
              "max", "quadratic", "solve_linear"]
CHORD_QUALITIES = ["major", "minor", "dom7", "min7", "Maj7", "maj7", "dim",
                   "dim7", "aug", "aug7", "sus2", "sus4", "m7b5", "add9",
                   "maj9", "min9", "dom9", "maj6", "min6"]
DURATIONS = ["w", "h", "q", "e", "s", "t"]
VELOCITIES = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
MODES = ["#MACHINE", "#HUMAN", "#V2", "#V3", "#V4"]

# LSP SymbolKind / CompletionItemKind constants (vscode-languageserver-protocol).
# Named so raw numbers never appear in symbol/completion payloads.
SYMBOL_FILE = 1
SYMBOL_MODULE = 2
SYMBOL_NAMESPACE = 3
SYMBOL_CLASS = 5
SYMBOL_METHOD = 6
SYMBOL_PROPERTY = 7
SYMBOL_VARIABLE = 13
SYMBOL_FUNCTION = 12

ITEM_KEYWORD = 14
ITEM_FUNCTION = 3
ITEM_METHOD = 6
ITEM_VARIABLE = 6
ITEM_CONSTANT = 15
ITEM_STRING = 17

# Hover docs — module-level constant so it is NOT rebuilt on every keystroke.
DOCS = {
    "T": "Timestamp in milliseconds. T0 = start, T500 = half a second in.",
    "N": "MIDI note number 0-127. N60 = middle C (C4). N72 = C5.",
    "D": "Duration in milliseconds. How long the note rings.",
    "V": "Velocity 0-127. Volume of the note. V80 = moderate.",
    "CH": "MIDI channel 0-15. Use for multiple instruments.",
    "play": "Human-mode command. play note(C4) @dur:q @vel:mf",
    "note": "Play a single note. play note(C4) @dur:q @vel:mf",
    "chord": "Play a chord. play chord(C, major) @dur:h @vel:mf",
    "for": "Loop: for $i = 0 to 7 { ... } — repeats with $i = 0..7",
    "repeat": "Repeat a block N times: repeat 4 { ... }",
    "while": "Loop while condition: while $i < 8 { ... }",
    "inherit": "Include a sub-file: inherit \"parts/melody.e\"",
    "track": "Album track entry in .enx files: track \"name\" 120",
    "sin": "sin(x) — sine wave. sin(0)=0, sin(pi/2)=1.",
    "cos": "cos(x) — cosine wave. cos(0)=1.",
    "sqrt": "sqrt(x) — square root.",
    "pow": "pow(a, b) — a raised to power b.",
    "round": "round(x) — nearest integer.",
    "floor": "floor(x) — round down.",
    "abs": "abs(x) — absolute value.",
    "min": "min(a, b) — smaller of two.",
    "max": "max(a, b) — larger of two.",
    "quadratic": "quadratic(a, b, c) — solves ax² + bx + c = 0.",
    "solve_linear": "solve_linear(m, x, c) — m * x + c.",
    "@bpm": "Tempo in beats per minute. @bpm 120",
    "@tempo": "Alias for @bpm.",
    "@key": "Musical key. @key C_Major",
    "@scale": "Scale for quantization. @scale C_Major",
    "@vol": "Master volume 0-1. @vol 0.8",
    "@dur": "Duration code: w h q e s t",
    "@vel": "Velocity code: ppp pp p mp mf f ff fff",
    "@ch": "MIDI channel: @ch 1",
    "@prob": "Probability 0-1 of each note playing. @prob 0.5",
    "@curve": "Tempo/dynamic curve. @curve bpm from 80 to 160 over 8",
    "@pan": "Stereo pan -1 (left) to 1 (right). @pan 0.5",
    "@reverb": "Reverb amount 0-1. @reverb 0.4",
    "@delay": "Delay effect amount 0-1. @delay 0.3",
}

_LINE_COMMENT_RE = re.compile(r"//.*$")
_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)


def _split_lines(text):
    """Split text into lines once, shared by all helpers."""
    return text.split("\n")


def _strip_comments(line):
    """Remove // and /* */ comments from a single line.
    Used for context detection so comments never trigger autocomplete."""
    s = _LINE_COMMENT_RE.sub("", line)
    s = _BLOCK_COMMENT_RE.sub("", s)
    return s


def _midi_name(midi):
    """MIDI number -> note name like 'C4'. Returns '' if out of range."""
    if 0 <= midi <= 127:
        return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"
    return ""


def get_symbols(text, lines=None):
    """Extract variables, modes, and sections from source text.
    lines: pre-split lines to avoid re-splitting (performance)."""
    if lines is None:
        lines = _split_lines(text)
    symbols = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # $var definitions
        if is_var_definition(stripped):
            name, expr = parse_var_definition(stripped)
            if name:
                symbols.append({"name": f"${name}", "kind": SYMBOL_VARIABLE, "line": i,
                                "detail": f"${name} = {expr}"})
        # Mode directives
        m = re.match(r"^#([A-Z0-9]+)", stripped)
        if m:
            symbols.append({"name": m.group(1), "kind": SYMBOL_METHOD, "line": i,
                            "detail": m.group(1)})
        # Sections
        m = re.match(r"^\[(Section|Intro|Verse|Chorus|Bridge|Outro)[:\]]", stripped, re.I)
        if m:
            symbols.append({"name": m.group(0), "kind": SYMBOL_MODULE, "line": i,
                            "detail": stripped})
        # inherit/track metadata
        m = re.match(r"^(inherit|track)\s+[\"']?([^\"']+)", stripped)
        if m:
            symbols.append({"name": f"{m.group(1)} {m.group(2)}", "kind": SYMBOL_MODULE, "line": i,
                            "detail": stripped})
    return symbols


def get_completions(text, line, char):
    """Context-aware completion list. Split once, reuse for symbols."""
    lines = _split_lines(text)
    current = lines[line][:char] if line < len(lines) else ""
    word = re.search(r"([@#$\w]+)$", current)
    prefix = word.group(1) if word else ""

    items = []

    # After '@' → directives
    if prefix.startswith("@"):
        for d in DIRECTIVES:
            if d.startswith(prefix):
                items.append({"label": d, "kind": ITEM_METHOD, "detail": "Directive",
                              "insertText": d})
        return items

    # After '#' → modes
    if prefix.startswith("#"):
        for m in MODES:
            if m.startswith(prefix):
                items.append({"label": m, "kind": ITEM_METHOD, "detail": "Syntax mode",
                              "insertText": m})
        return items

    # After '$' → defined variables (reuse the same pre-split lines)
    if prefix.startswith("$"):
        for sym in get_symbols(text, lines):
            if sym["kind"] == SYMBOL_VARIABLE and sym["name"].startswith(prefix):
                items.append({"label": sym["name"], "kind": ITEM_VARIABLE, "detail": sym["detail"],
                              "insertText": sym["name"]})
        return items

    # Comment-aware context detection: strip comments first so a comment like
    # "// play chord ideas" never triggers chord-quality suggestions.
    code_before = _strip_comments(current)
    if "play chord" in code_before:
        for q in CHORD_QUALITIES:
            if q.startswith(prefix):
                items.append({"label": q, "kind": ITEM_CONSTANT, "detail": "Chord quality",
                              "insertText": q})
        return items

    if "play note" in code_before:
        for n in NOTE_NAMES:
            for oct in range(2, 7):
                label = f"{n}{oct}"
                if label.startswith(prefix):
                    items.append({"label": label, "kind": ITEM_CONSTANT,
                                  "detail": f"Note {label}", "insertText": label})
        return items

    # Math functions if inside a {$expr} block
    if "{" in current and "}" not in current[char:]:
        for f in MATH_FUNCS:
            if f.startswith(prefix):
                items.append({"label": f"{f}()", "kind": ITEM_FUNCTION, "detail": "Math function",
                              "insertText": f"{f}(${{1}})"})
        return items

    # Generic keywords
    for k in KEYWORDS:
        if k.startswith(prefix):
            items.append({"label": k, "kind": ITEM_KEYWORD, "detail": "Keyword",
                          "insertText": k})
    for d in DIRECTIVES:
        if d.startswith(prefix):
            items.append({"label": d, "kind": ITEM_METHOD, "detail": "Directive",
                          "insertText": d})
    for q in CHORD_QUALITIES:
        if q.startswith(prefix):
            items.append({"label": q, "kind": ITEM_CONSTANT, "detail": "Chord quality",
                          "insertText": q})
    for v in VELOCITIES:
        if v.startswith(prefix):
            items.append({"label": v, "kind": ITEM_CONSTANT, "detail": "Velocity",
                          "insertText": v})
    for d in DURATIONS:
        if d.startswith(prefix):
            items.append({"label": d, "kind": ITEM_CONSTANT, "detail": "Duration",
                          "insertText": d})
    return items


def _token_at(lines, line, char):
    """Get the token (word) at a position.
    lines: pre-split lines. Splits machine tokens like N60 into ('N', '60')."""
    if line >= len(lines):
        return None
    current = lines[line]
    if char > len(current):
        char = len(current)
    start = char
    while start > 0 and (current[start-1].isalnum() or current[start-1] in "_$@#."):
        start -= 1
    end = char
    while end < len(current) and (current[end].isalnum() or current[end] in "_$@#."):
        end += 1
    token = current[start:end]
    return {"token": token, "start": start, "end": end, "line": line}


def get_hover(text, line, char):
    """Hover documentation for tokens. Uses module-level DOCS constant."""
    lines = _split_lines(text)
    tok = _token_at(lines, line, char)
    if not tok or not tok["token"]:
        return None
    t = tok["token"]

    # MIDI number → note name
    if re.match(r"^\d+$", t):
        name = _midi_name(int(t))
        if name:
            return {"text": f"MIDI {int(t)} = {name}", "detail": "Note number"}

    if t in DOCS:
        return {"text": DOCS[t], "detail": "HELLFORGE E Language"}

    # Machine token N60, D500, V80, T1000
    m = re.match(r"^(T|N|D|V)(\d+\.?\d*)$", t)
    if m:
        kind, val = m.group(1), m.group(2)
        if kind == "N":
            name = _midi_name(int(float(val)))
            if name:
                return {"text": f"Note {name} (MIDI {int(float(val))})",
                        "detail": DOCS.get("N", "Note")}
        if kind in DOCS:
            return {"text": f"{kind}{val} — {DOCS[kind]}", "detail": "Machine token"}

    # $var hover
    if t.startswith("$"):
        for sym in get_symbols(text, lines):
            if sym["name"] == t:
                return {"text": sym["detail"], "detail": "Variable"}

    # @directive hover
    if t.startswith("@") and t in DOCS:
        return {"text": DOCS[t], "detail": "Directive"}

    return None


def get_diagnostics(text):
    """Compile and return error diagnostics (line, char, message).
    Uses the full HELLFORGE linter (errors + warnings + info).
    Linting runs unconditionally — nothing is unreachable."""
    errors = []

    # Full linter pass (fatal/error/warning/info diagnostics with columns)
    lines = _split_lines(text)
    try:
        from ep_compiler.lint import lint_source
        for d in lint_source(text):
            diag_line = d.get("line", 0)
            diag_char = d.get("char", 0)
            diag_len = d.get("length", 1)
            if diag_char == 0 and diag_len <= 1:
                # whole-line squiggle when no precise column was computed
                diag_len = len(lines[diag_line]) if diag_line < len(lines) and lines[diag_line] else 1
            errors.append({
                "line": diag_line,
                "char": diag_char,
                "length": max(1, diag_len),
                "message": f"[{d.get('code','?')}] {d['message']}",
                "severity": d.get("severity", 2),
            })
    except Exception as e:
        errors.append({"line": 0, "char": 0, "length": 1,
                       "message": f"Linter error: {e}", "severity": 1})

    # Compile to catch hard errors (fallback if linter misses something)
    try:
        compile_source(text)
    except Exception as e:
        msg = str(e)
        m = re.search(r"line\s+(\d+)", msg, re.I)
        line = int(m.group(1)) - 1 if m else 0
        length = len(lines[max(0, min(line, len(lines)-1))]) if lines else 1
        errors.append({"line": max(0, line), "char": 0, "length": max(1, length),
                       "message": msg, "severity": 1})

    return errors


def get_definition(text, line, char):
    """Find definition location for $var or inherit path."""
    lines = _split_lines(text)
    tok = _token_at(lines, line, char)
    if not tok or not tok["token"]:
        return None
    t = tok["token"]
    if t.startswith("$"):
        name = t
        for i, ln in enumerate(lines):
            if is_var_definition(ln.strip()):
                vname, _ = parse_var_definition(ln.strip())
                if f"${vname}" == name:
                    return {"line": i, "char": 0}
    return None


def get_format(text):
    """Simple formatter: normalize whitespace, pad machine lines."""
    lines = _split_lines(text)
    out = []
    for ln in lines:
        stripped = ln.strip()
        if not stripped:
            out.append("")
            continue
        # Normalize: single spaces between tokens in machine lines
        if re.match(r"^T\d+", stripped):
            tokens = re.findall(r"(T\d+|N\d+|D\d+|V[\d.]+|CH\[\d+\])", stripped)
            if tokens:
                out.append(" ".join(tokens))
                continue
        out.append(stripped)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def handle(method, params):
    if method == "get_symbols":
        return {"result": get_symbols(params.get("text", ""))}
    if method == "get_completions":
        return {"result": get_completions(params.get("text", ""),
                                          params.get("line", 0),
                                          params.get("char", 0))}
    if method == "get_hover":
        return {"result": get_hover(params.get("text", ""),
                                    params.get("line", 0),
                                    params.get("char", 0))}
    if method == "get_diagnostics":
        return {"result": get_diagnostics(params.get("text", ""))}
    if method == "get_definition":
        return {"result": get_definition(params.get("text", ""),
                                         params.get("line", 0),
                                         params.get("char", 0))}
    if method == "get_format":
        return {"result": get_format(params.get("text", ""))}
    if method == "get_runtime_config":
        from ep_compiler.runtime_config import get_runtime_config
        return {"result": get_runtime_config()}
    if method == "apply_runtime_config":
        from ep_compiler.runtime_config import apply_runtime_config
        return {"result": apply_runtime_config(params.get("config", {}))}
    if method == "convert_syntax":
        return {"result": _convert_syntax_request(params)}
    if method == "export_midi":
        return {"result": _export_midi_request(params)}
    if method == "convert_to_eic":
        return {"result": _convert_to_eic_request(params)}
    return {"error": f"Unknown method: {method}"}


def _export_midi_request(params):
    """Compile a source file to MIDI (ep.py compile equivalent).
    params: {path} -> writes {path base}.mid"""
    try:
        from ep_compiler.cli import compile_file as cli_compile_file
    except Exception as e:
        return {"ok": False, "error": str(e)}
    path = params.get("path", "")
    if not os.path.exists(path):
        return {"ok": False, "error": f"File not found: {path}"}
    try:
        cli_compile_file(path, output=os.path.splitext(path)[0] + ".mid")
        out = os.path.splitext(path)[0] + ".mid"
        if not os.path.exists(out):
            return {"ok": False, "error": "MIDI export produced no output"}
        return {"ok": True, "output": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _convert_to_eic_request(params):
    """Convert a source file to a .eic bundle at the chosen syntax version.
    params: {path, target: v1|v2|v3|v4}"""
    path = params.get("path", "")
    target = params.get("target", "v4")
    # 1. Convert to the version's .e source via portbaby
    res = _convert_syntax_request({"path": path, "target": target})
    if not res.get("ok"):
        return res
    out_e = res.get("output") or ""
    if not out_e or not os.path.exists(out_e):
        return {"ok": False, "error": "syntax conversion produced no output"}
    # 2. Wrap into .eic bundle
    try:
        from ep_compiler.formats import export_eic
        out_eic = os.path.splitext(path)[0] + "_" + target + ".eic"
        export_eic(out_e, out_eic)
        if os.path.exists(out_eic):
            return {"ok": True, "output": out_eic, "target": target}
        return {"ok": False, "error": "eic export failed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _convert_syntax_request(params):
    """Convert a source file to target syntax via portbaby.
    params: {path, target: v1|v2|v3|v4}"""
    try:
        from plugins.portbaby.converter import convert_file
        from ep_compiler.compile import detect_syntax_version
    except Exception as e:
        return {"ok": False, "error": f"portbaby unavailable: {e}"}
    path = params.get("path", "")
    target = params.get("target", "v4")
    ver_map = {"v1": "v1_machine", "v2": "v2", "v3": "v3", "v4": "v4"}
    conv = ver_map.get(target, target)
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        src_text = f.read()
    try:
        if detect_syntax_version(src_text) == conv or (conv == "v1_machine" and detect_syntax_version(src_text) == "v1_human"):
            # same version — passthrough
            out = os.path.splitext(path)[0] + "_" + target + ".e"
            with open(out, "w", encoding="utf-8") as f:
                f.write(src_text)
            return {"ok": True, "output": out, "target": target}
        result = convert_file(path, conv, make_project=False, show_report=False)
        out = (result or {}).get("output") or ""
        return {"ok": True, "output": out, "target": target}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    """Line-delimited JSON-RPC server."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            method = req.get("method", "")
            params = req.get("params", {})
            resp = handle(method, params)
            resp["id"] = req.get("id")
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stdout.write(json.dumps({"error": str(e)}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
