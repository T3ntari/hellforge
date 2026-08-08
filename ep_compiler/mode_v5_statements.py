"""v5 statement-level features: include, !fn macros, print, assert, prog, perc.

All of these are backward-compatible additions — they only activate on lines
that could not parse in any earlier version, and the core line parsers never
see them (they are consumed or expanded before parsing).

Pipeline placement:
  - resolve_includes  → text-level, before version detection (includes may
                        carry version markers or macros)
  - process_v5_pre    → text-level, after includes: !fn definitions and uses
  - process_v5_lines  → line-level, AFTER loop unrolling + math preprocessing
                        so print/assert/prog/perc can use $vars and loop vars
                        (and print inside loop bodies fires per iteration)
"""

import os
import re
import random

INCLUDE_RE = re.compile(r'^\s*include\s+"([^"]+)"\s*$', re.I)
FN_DEF_RE = re.compile(r'^!fn\s+(\w+)\s*\(([^)]*)\)\s*=\s*(.+)$', re.I)
FN_USE_RE = re.compile(r'^!(\w+)\s*\(([^)]*)\)\s*$')
PRINT_RE = re.compile(r'^\s*print\s+(.+)$', re.I)
ASSERT_RE = re.compile(r'^\s*assert\s+(.+?)\s*(?:,\s*"([^"]*)")?\s*$', re.I)
PROG_RE = re.compile(r'^\s*prog\s*\(([^)]+)\)\s*$', re.I)
PERC_RE = re.compile(r'^\s*perc\s*\(\s*(\w+)\s*\)\s*$', re.I)

MAX_INCLUDE_DEPTH = 16

# GM percussion map: name -> MIDI note (channel 9 forced)
PERCUSSION = {
    "kick": 36, "bass_drum": 36, "snare": 38, "clap": 39,
    "hihat": 42, "hihat_closed": 42, "openhat": 46, "hihat_open": 46,
    "tom_low": 41, "tom_mid": 45, "tom_high": 50,
    "crash": 49, "ride": 51,
    "tambourine": 54, "cowbell": 56, "shaker": 82,
}

# Chord quality aliases for prog(): root name -> (root, quality)
_QUAL_ALIASES = {
    "maj": "major", "m": "minor", "min": "minor", "dim": "dim",
    "aug": "aug", "dom7": "dom7", "maj7": "maj7", "min7": "min7",
    "dim7": "dim7", "sus2": "sus2", "sus4": "sus4", "7": "7",
}


# ── include ─────────────────────────────────────

def resolve_includes(text, base_dir=None, _depth=0, _seen=None):
    """Inline `include "file.e"` lines. Recursion depth- and cycle-guarded.
    base_dir: directory of the file being compiled (falls back to cwd)."""
    if _depth > MAX_INCLUDE_DEPTH:
        raise ValueError(f"include: maximum depth {MAX_INCLUDE_DEPTH} exceeded")
    if _seen is None:
        _seen = set()
    out = []
    for line in text.split("\n"):
        m = INCLUDE_RE.match(line)
        if not m:
            out.append(line)
            continue
        rel = m.group(1)
        candidates = []
        if base_dir:
            candidates.append(os.path.join(base_dir, rel))
        candidates.append(os.path.abspath(rel))
        resolved = next((p for p in candidates if os.path.isfile(p)), None)
        if resolved is None:
            raise FileNotFoundError(f"include: cannot find '{rel}'")
        real = os.path.realpath(resolved)
        if real in _seen:
            raise ValueError(f"include: circular include of '{rel}'")
        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            child = f.read()
        _seen.add(real)
        out.append(resolve_includes(child, os.path.dirname(real), _depth + 1, _seen))
        _seen.discard(real)
    return "\n".join(out)


# ── !fn parameterized macros ────────────────────

def _norm_arg(arg):
    """Normalize a macro argument for textual substitution.
    '{expr}' args become '(expr)' so they compose inside {expr} bodies;
    numbers, note names and $vars pass through unchanged."""
    a = arg.strip()
    if a.startswith("{") and a.endswith("}") and len(a) > 1:
        inner = a[1:-1].strip()
        return f"({inner})" if inner else a
    return a


def _expand_fn_body(body, param_list, args):
    """Substitute $1..$n and named $params in a macro body with args."""
    expanded = body
    for idx, val in enumerate(args):
        val = _norm_arg(val)
        expanded = re.sub(rf'\${idx}\b', val, expanded)
        if idx < len(param_list):
            expanded = re.sub(rf'\${re.escape(param_list[idx])}\b', val, expanded)
    return expanded


def process_v5_pre(text):
    """Collect !fn definitions (consumed from the text). Returns (text, fns).
    Definitions are text-level; USES are expanded post-unroll so loop and
    scope variables in the arguments resolve correctly."""
    fns = {}
    out = []
    for line in text.split("\n"):
        d = FN_DEF_RE.match(line)
        if d:
            name, params, body = d.group(1), d.group(2), d.group(3)
            param_list = [p.strip() for p in params.split(",") if p.strip()]
            fns[name] = (param_list, body)
            continue
        out.append(line)
    return "\n".join(out), fns


# ── print / assert / prog / perc (line-level, post-unroll) ──

def _note_name(value):
    """N60 → 'C4'; 'C4' → 'C4'; else None."""
    m = re.match(r'^N(\d+)$', value.strip(), re.I)
    if m:
        try:
            from .events import midi_to_name
            return midi_to_name(int(m.group(1)))
        except Exception:
            return None
    return None


def _safe_cond(expr):
    """Evaluate a compile-time condition (numbers, $vars already resolved,
    {expr} already resolved). Restricted namespace — no builtins."""
    s = expr.strip()
    if not s:
        return False
    s = s.replace("^", "**")
    try:
        return bool(eval(s, {"__builtins__": {}}, {}))
    except Exception:
        return False


def process_v5_lines(lines, bpm=120, ll_state=None, fns=None):
    """Post-loop statement pass. Returns (new_lines, printed_messages).
    Consumes print/assert/prog/perc and expands !fn uses; passes everything
    else through."""
    ll_state = ll_state or {}
    fns = fns or {}
    out = []
    printed = []
    for line in lines:
        stripped = line.strip()

        m = PRINT_RE.match(line)
        if m:
            payload = m.group(1).strip()
            if payload.startswith('"') and payload.endswith('"'):
                printed.append(payload[1:-1])
            else:
                nm = _note_name(payload)
                if nm:
                    printed.append(nm)
                elif payload.lower() in ("midi", "events"):
                    printed.append(("__stats__", payload.lower()))
                else:
                    printed.append(payload)
            continue

        m = ASSERT_RE.match(line)
        if m:
            cond, msg = m.group(1).strip(), m.group(2)
            if not _safe_cond(cond):
                raise AssertionError(msg or f"assert failed: {cond}")
            continue

        u = FN_USE_RE.match(stripped)
        if u and u.group(1) in fns:
            param_list, body = fns[u.group(1)]
            args = [a.strip() for a in u.group(2).split(",")] if u.group(2).strip() else []
            out.append(_expand_fn_body(body, param_list, args))
            continue

        m = PROG_RE.match(line)
        if m:
            for chord in re.split(r"[,\s]+", m.group(1).strip()):
                chord = chord.strip()
                if not chord:
                    continue
                out.append(_prog_chord_line(chord))
            continue

        m = PERC_RE.match(line)
        if m:
            note = PERCUSSION.get(m.group(1).lower())
            if note is None:
                raise ValueError(f"perc: unknown drum '{m.group(1)}' "
                                 f"(available: {', '.join(sorted(PERCUSSION))})")
            out.append(f"play note({_midi_name(note)}) @ch:9 @dur:q @vel:f")
            continue

        out.append(line)
    return out, printed


def _prog_chord_line(spec):
    """'C:q', 'Am:h', 'G:maj7:q', 'F' → human chord line."""
    root = spec
    dur = "q"
    qual = "major"
    if ":" in spec:
        parts = spec.split(":")
        root = parts[0]
        if len(parts) >= 2:
            tail = parts[1].strip()
            if tail in ("w", "h", "q", "e", "s", "t"):
                dur = tail
            elif tail.lower() in _QUAL_ALIASES or tail.lower() in (
                    "major", "minor", "dim", "aug", "dom7", "maj7", "min7",
                    "dim7", "sus2", "sus4", "7"):
                qual = tail.lower()
        if len(parts) >= 3:
            dur = parts[2].strip() or dur
    # 'Am' → A minor, 'Cmaj' → C major
    m = re.match(r'^([A-Ga-g][#b]?)(maj|min|m|dim|aug|7|dom7|maj7|min7|dim7|sus2|sus4)$', root)
    if m and len(root) > 1:
        root, suf = m.group(1), m.group(2).lower()
        qual = _QUAL_ALIASES.get(suf, suf)
    return f"play chord({root}, {qual}) @dur:{dur} @vel:m"


def _midi_name(midi):
    from .events import midi_to_name
    return midi_to_name(midi)
