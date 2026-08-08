"""HELLFORGE shared syntax validation — single source of truth for parsers + linter.

Lexicons for every word the language understands, plus typed line validators
that return (parsed, problems[]) where each problem has:
  code, line, char, length, message

Consumed by mode_v1_machine, mode_v1_human (strict parsing) and lint.py
(static analysis) so they can never drift apart.

Words are additive: numeric and word forms both work (T0 N60 / T0 N C4).
"""

import re

# ── Lexicons ──

DUR_CODES = {"w", "h", "q", "e", "s", "t"}
DUR_WORDS = {
    "whole": "w", "semibreve": "w",
    "half": "h", "minim": "h",
    "quarter": "q", "crotchet": "q",
    "eighth": "e", "quaver": "e",
    "sixteenth": "s", "semiquaver": "s",
    "thirtysecond": "t", "demisemiquaver": "t",
}
VEL_CODES = {"ppp": 16, "pp": 33, "p": 49, "mp": 64, "mf": 80,
             "f": 96, "ff": 112, "fff": 126}
VEL_WORDS = {
    "pianissimo": 33, "piano": 49, "mezzo": 64, "mezzoforte": 80,
    "mezzo-forte": 80, "forte": 96, "fortissimo": 112,
    "soft": 49, "normal": 80, "loud": 112, "max": 127, "silent": 0,
}
CHORD_QUALITIES = {
    "major": [0, 4, 7], "minor": [0, 3, 7], "dim": [0, 3, 6],
    "aug": [0, 4, 8], "dom7": [0, 4, 7, 10], "maj7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10], "dim7": [0, 3, 6, 9], "sus2": [0, 2, 7],
    "sus4": [0, 5, 7], "m": [0, 3, 7], "m7": [0, 3, 7, 10],
    "7": [0, 4, 7, 10], "maj": [0, 4, 7], "min": [0, 3, 7],
}
CHORD_ALIASES = {"maj": "major", "min": "minor", "m": "minor", "m7": "min7"}
DIRECTIVE_NAMES = {"bpm", "tempo", "key", "scale", "vol", "volume", "gc", "dur",
                   "vel", "ch", "prob", "probability", "curve", "mode", "random",
                   "pan", "reverb", "delay", "time", "ts", "timestamp", "note",
                   "sustain", "master", "gain", "track", "strict", "mem"}
MACHINE_TOKENS = {"T", "N", "D", "V", "CH", "TRK", "P", "S", "F", "E", "Z"}
MATH_FUNCS = {"sin", "cos", "sqrt", "pow", "round", "floor", "abs", "min",
              "max", "quadratic", "solve_linear"}
LOOP_KEYWORDS = {"for", "repeat", "while", "to", "step", "do", "if", "else"}
PROJECT_KEYWORDS = {"inherit", "track", "title", "composer", "artist", "album",
                    "genre", "project", "include", "section", "play", "tempo"}
NOTE_RE = re.compile(r"^[A-Ga-g]#?b?\d+$")
NOTE_NAME_RE = re.compile(r"^[A-Ga-g]#?b?$")


def resolve_duration(word):
    """word -> ('q', 'quarter', beats) or None. Accepts codes, words, dotted."""
    w = word.lower().rstrip(".")
    dotted = word.endswith(".") or w.endswith(".")
    if w.endswith("."):
        w = w[:-1]
    if w in DUR_CODES:
        beats = {"w": 4, "h": 2, "q": 1, "e": 0.5, "s": 0.25, "t": 0.125}[w]
    elif w in DUR_WORDS:
        code = DUR_WORDS[w]
        beats = {"w": 4, "h": 2, "q": 1, "e": 0.5, "s": 0.25, "t": 0.125}[code]
    else:
        return None
    if dotted:
        beats *= 1.5
    return w, beats


def resolve_velocity(word):
    """word -> velocity int or None. Accepts codes, words, numerics."""
    w = word.lower()
    if w in VEL_CODES:
        return VEL_CODES[w]
    if w in VEL_WORDS:
        return VEL_WORDS[w]
    try:
        if "." in w:
            return round(float(w) * 127)
        return int(w)
    except ValueError:
        return None


def resolve_quality(word):
    """word -> canonical quality or None."""
    w = word.lower()
    if w in CHORD_QUALITIES:
        return CHORD_ALIASES.get(w, w)
    return None


def resolve_note(name):
    """Note name -> (midi, ok). Accepts 'C4', 'Bb3', 'C#' (octave 4 default)."""
    from .events import name_to_midi
    if NOTE_RE.match(name or ""):
        return name_to_midi(name), True
    if NOTE_NAME_RE.match(name or ""):
        return name_to_midi(name + "4"), True
    return None, False


def resolve_directive(name):
    return name.lower() in DIRECTIVE_NAMES


def is_machine_word(word):
    """Top-level word in a machine line (T, N, D, V, CH, etc.)."""
    return word.upper() in MACHINE_TOKENS


# ── Line validators ──

# Anchored machine regex — no trailing garbage allowed.
# CH accepted as both CH[0] and CH0.
_MACHINE_ANCHORED = re.compile(
    r"^(?:CH(?:\[)?(?P<channel>\d+)(?:\])?\s*)?"
    r"(?:TRK\[(?P<track>[^\]]+)\]\s*)?"
    r"T(?P<ts>\d+)\s+"
    r"(?:N(?P<midi>\d+)|N\s+(?P<midi_name>[A-Ga-g]#?b?\d*))\s*"
    r"(?:\s+D(?P<dur>\d+)|(?:\s+D\s+(?P<dur_word>[A-Za-z.]+)))?"
    r"(?:\s+V(?P<vel>-?[\d.]+)|(?:\s+V\s+(?P<vel_word>[A-Za-z]+))|(?:\s+(?P<bare_vel>-?[\d.]+)))?"
    r"(?:\s+P\[bend:(?P<bend>-?\d+)\])?"
    r"(?:\s+S\[pan:(?P<pan>-?[\d.]+)\])?"
    r"(?:\s+F\[c:(?P<filter_cutoff>[\d.]+(?:hz)?)\])?"
    r"(?:\s+F\[r:(?P<filter_res>[\d.]+)\])?"
    r"(?:\s+F\[t:(?P<filter_type>\w+)\])?"
    r"(?:\s+E\[a:(?P<env_attack>[\d.]+(?:ms)?)\])?"
    r"(?:\s+E\[r:(?P<env_release>[\d.]+(?:ms)?)\])?"
    r"(?:\s+E\[s:(?P<env_sustain>[\d.]+)\])?"
    r"(?:\s+Z\[ph:(?P<phase>[\d.]+)\])?"
    r"(?:\s+Z\[pt:(?P<cents>-?\d+)\])?"
    r"(?:\s+Z\[sw:(?P<swing>[\d.]+(?:ms)?)\])?"
    r"\s*$"
)

_MACHINE_LEGACY = re.compile(
    r"^(?:CH\[(?P<channel>\d+)\]\s*)?T(?P<ts>\d+)\s+N(?P<midi>\d+)"
    r"(?:\s+D(?P<dur>\d+))?(?:\s+V(?P<vel>[\d.]+))?\s*$"
)


def _strip_line_comment(s):
    """Strip trailing comments from a line: // ... and # ... (E++ style).
    Braces-protected // (floor division) is kept."""
    out = []
    depth = 0
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        if ch == "/" and depth == 0 and i + 1 < len(s) and s[i + 1] == "/":
            return s[:i].rstrip()
        if ch == "#" and depth == 0 and (i == 0 or s[i - 1].isspace()):
            return s[:i].rstrip()
        i += 1
    return s


def check_machine_line(line, problems, line_no=0, bpm=120):
    """Validate a machine line. Returns parsed groups dict or None.
    Appends problems (with char/length) for every violation.
    bpm is used to convert word-form durations (D q -> ms)."""
    s = _strip_line_comment(line.strip())
    m = _MACHINE_ANCHORED.match(s)
    if not m:
        # Report why it failed
        if not re.match(r"^T\d", s):
            problems.append(_mk("E051", line_no, 0, len(s),
                                "Machine line must start with T (timestamp)"))
        else:
            problems.append(_mk("E056", line_no, 0, len(s),
                                f"Invalid machine line: {s[:40]}"))
        return None

    g = m.groupdict()

    # Timestamp
    try:
        ts = int(g["ts"])
    except (TypeError, ValueError):
        problems.append(_mk("E052", line_no, _col(s, f"T{g['ts']}"),
                            len(f"T{g['ts']}"), "T timestamp must be a non-negative integer"))
        return None

    # Note
    if g["midi"] is not None:
        midi = int(g["midi"])
        if not (0 <= midi <= 127):
            problems.append(_mk("E053", line_no, _col(s, f"N{g['midi']}"),
                                len(f"N{g['midi']}"), f"N (note) value must be 0-127 (N{midi})"))
    elif g["midi_name"]:
        name = g["midi_name"]
        midi, ok = resolve_note(name)
        if not ok:
            problems.append(_mk("E060", line_no, _col(s, name), len(name),
                                f"Unknown note name: {name}"))
    else:
        problems.append(_mk("E053", line_no, _col(s, "N"), 1,
                            "Machine line missing N (note)"))
        return None

    # Duration
    dur_ms = None
    if g["dur"] is not None:
        dur_ms = int(g["dur"])
        if dur_ms < 1:
            problems.append(_mk("E054", line_no, _col(s, f"D{g['dur']}"),
                                len(f"D{g['dur']}"), "D (duration) must be positive"))
    elif g["dur_word"]:
        resolved = resolve_duration(g["dur_word"])
        if resolved is None:
            problems.append(_mk("E054", line_no, _col(s, g["dur_word"]),
                                len(g["dur_word"]),
                                f"Unknown duration word: {g['dur_word']}"))
        else:
            dur_ms = int(resolved[1] * 60000 / max(1, bpm))
    else:
        dur_ms = 500

    # Velocity
    vel = None
    if g["vel"] is not None:
        try:
            v = float(g["vel"])
            if "." in g["vel"]:
                problems.append(_mk("W019", line_no, _col(s, f"V{g['vel']}"),
                                    len(f"V{g['vel']}"),
                                    f"Float velocity will be rounded (V{g['vel']})"))
            vel = round(v * 127) if v <= 1.0 else int(v)
            if vel < 0 or vel > 127:
                problems.append(_mk("E055", line_no, _col(s, f"V{g['vel']}"),
                                    len(f"V{g['vel']}"), f"V (velocity) must be 0-127 (V{vel})"))
        except ValueError:
            problems.append(_mk("E055", line_no, _col(s, f"V{g['vel']}"),
                                len(f"V{g['vel']}"), "Invalid velocity value"))
    elif g["vel_word"]:
        vel = resolve_velocity(g["vel_word"])
        if vel is None:
            problems.append(_mk("E055", line_no, _col(s, g["vel_word"]),
                                len(g["vel_word"]),
                                f"Unknown velocity word: {g['vel_word']}"))
    elif g["bare_vel"] is not None:
        # Bare trailing numeric (legacy: 'T0 N60 D100 80') = velocity
        try:
            v = float(g["bare_vel"])
            vel = round(v * 127) if v <= 1.0 else int(v)
            if vel < 0 or vel > 127:
                problems.append(_mk("E055", line_no, _col(s, g["bare_vel"]),
                                    len(g["bare_vel"]),
                                    f"V (velocity) must be 0-127 (V{vel})"))
        except ValueError:
            problems.append(_mk("E055", line_no, _col(s, g["bare_vel"]),
                                len(g["bare_vel"]), "Invalid velocity value"))
    else:
        vel = 80

    g["_ts"] = ts
    g["_midi"] = midi
    g["_dur"] = dur_ms
    g["_vel"] = vel
    return g


def _mk(code, line, char, length, msg):
    return {"code": code, "line": line, "char": char,
            "length": max(1, length), "message": msg}


def _col(s, needle):
    idx = s.find(needle)
    return idx if idx >= 0 else 0


# ── Human line validation ──

HUMAN_NOTE_RE = re.compile(r"play\s+note\(\s*([A-Ga-g]#?b?\d*)\s*\)(\s+@.+)?$", re.I)
HUMAN_CHORD_RE = re.compile(r"play\s+chord\(\s*([A-Ga-g]#?b?)\s*,\s*(\w+)\s*\)(\s+@.+)?$", re.I)
HUMAN_PROP_RE = re.compile(r"@(\w+)\s*:\s*([^\s@]+)")


def check_human_line(line, problems, line_no=0):
    """Validate a human line (play note / play chord). Returns
    (kind, note_str, quality, prop_dict) or None if not a human line."""
    s = line.strip()
    m = HUMAN_NOTE_RE.match(s)
    if m:
        note_str = m.group(1)
        props = _check_props(m.group(2) or "", problems, line_no, s)
        midi, ok = resolve_note(note_str)
        if not ok:
            problems.append(_mk("E060", line_no, _col(s, note_str), len(note_str),
                                f"Unknown note name: {note_str}"))
        if "dur" not in props and "duration" not in props:
            problems.append(_mk("E062", line_no, _col(s, "play"), 4,
                                "Missing @dur on play note"))
        if "vel" not in props and "velocity" not in props:
            problems.append(_mk("E063", line_no, _col(s, "play"), 4,
                                "Missing @vel on play note"))
        return ("note", note_str, None, props)

    m = HUMAN_CHORD_RE.match(s)
    if m:
        root, quality = m.group(1), m.group(2)
        props = _check_props(m.group(3) or "", problems, line_no, s)
        q = resolve_quality(quality)
        if q is None:
            problems.append(_mk("E059", line_no, _col(s, quality), len(quality),
                                f"Unknown chord quality: {quality}"))
        return ("chord", root, quality, props)

    return None


def _check_props(prop_str, problems, line_no, s):
    """Validate @key:value pairs. Unknown keys → E057. Bad values → typed errors."""
    out = {}
    for m in HUMAN_PROP_RE.finditer(prop_str):
        key = m.group(1).lower()
        val = m.group(2)
        if key not in DIRECTIVE_NAMES:
            problems.append(_mk("E057", line_no, _col(s, m.group(0)),
                                len(m.group(0)),
                                f"Unknown property @{key} (did you mean a known directive?)"))
            continue
        if key in ("dur", "duration"):
            if resolve_duration(val) is None and not val.endswith("ms") \
               and not val.replace(".", "").isdigit():
                problems.append(_mk("E054", line_no, _col(s, m.group(0)),
                                    len(m.group(0)),
                                    f"Unknown duration: {val}"))
            elif val.replace(".", "", 1).isdigit() and float(val) <= 0:
                problems.append(_mk("E054", line_no, _col(s, m.group(0)),
                                    len(m.group(0)),
                                    f"D (duration) must be positive ({val})"))
            out[key] = val
        elif key in ("vel", "velocity"):
            v = resolve_velocity(val)
            if v is None:
                problems.append(_mk("E055", line_no, _col(s, m.group(0)),
                                    len(m.group(0)),
                                    f"Unknown velocity: {val}"))
            elif v < 0 or v > 127:
                problems.append(_mk("E055", line_no, _col(s, m.group(0)),
                                    len(m.group(0)),
                                    f"V (velocity) must be 0-127 ({val})"))
            out[key] = val
        elif key == "pan":
            try:
                p = float(val)
                if not (-1.0 <= p <= 1.0):
                    problems.append(_mk("E040", line_no, _col(s, m.group(0)),
                                        len(m.group(0)),
                                        f"@pan must be -1.0 to 1.0 ({val})"))
            except ValueError:
                problems.append(_mk("E040", line_no, _col(s, m.group(0)),
                                    len(m.group(0)), f"Invalid @pan value: {val}"))
            out[key] = val
        elif key == "bend":
            try:
                b = int(val)
                if not (-64 <= b <= 64):
                    problems.append(_mk("E041", line_no, _col(s, m.group(0)),
                                        len(m.group(0)),
                                        f"@bend must be -64 to 64 ({val})"))
            except ValueError:
                problems.append(_mk("E041", line_no, _col(s, m.group(0)),
                                    len(m.group(0)), f"Invalid @bend value: {val}"))
            out[key] = val
        elif key in ("ch", "channel"):
            try:
                c = int(val)
                if not (0 <= c <= 15):
                    problems.append(_mk("E043", line_no, _col(s, m.group(0)),
                                        len(m.group(0)),
                                        f"@ch must be 0-15 ({val})"))
            except ValueError:
                problems.append(_mk("E043", line_no, _col(s, m.group(0)),
                                    len(m.group(0)), f"Invalid @ch value: {val}"))
            out[key] = val
        else:
            out[key] = val
    return out


# ── v2 semantic validators ──

_V2_PLAY_RE = re.compile(r"play\(([^,\)]+)\s*,\s*([^,\)]+)\s*,\s*([^,\)]+)\s*\)", re.I)
_V2_ARPS_RE = re.compile(r"arpeggio\(([^)]*)\)", re.I)
_V2_CHROM_RE = re.compile(r"chromatic_run\(([^)]*)\)", re.I)
_V2_KEY_RE = re.compile(r"Key:\s*([A-Ga-g]#?b?)_([A-Za-z]+)")
_NOTE_TOKEN_RE = re.compile(r"[A-Ga-g]#?b?\d+")
_V2_CHORD_QUAL = {"major", "minor", "dim", "aug", "dom7", "maj7", "min7",
                  "dim7", "sus2", "sus4", "m", "m7", "7"}


def check_semantic_line(line, problems, line_no=0):
    """Validate v2 semantic constructs. Returns kind or None.
    play(C4, q, mf) / arpeggio(C4, G4, D5) / chromatic_run(C4, C5) / Key: C_Major"""
    s = line.strip()
    m = _V2_PLAY_RE.match(s)
    if m:
        note, dur, vel = m.group(1), m.group(2).strip(), m.group(3).strip()
        midi, ok = resolve_note(note)
        if not ok:
            problems.append(_mk("E060", line_no, _col(s, note), len(note),
                                f"Unknown note name: {note}"))
        if resolve_duration(dur) is None and not dur.replace(".", "").isdigit():
            problems.append(_mk("E054", line_no, _col(s, dur), len(dur),
                                f"Unknown duration: {dur}"))
        if resolve_velocity(vel) is None or resolve_velocity(vel) > 127:
            problems.append(_mk("E055", line_no, _col(s, vel), len(vel),
                                f"Unknown velocity: {vel}"))
        return "play"
    m = _V2_ARPS_RE.match(s)
    if m:
        notes = _NOTE_TOKEN_RE.findall(m.group(1))
        for n in notes:
            if not _valid_note(n):
                problems.append(_mk("E060", line_no, _col(s, n), len(n),
                                    f"Unknown note name: {n}"))
        return "arpeggio"
    m = _V2_CHROM_RE.match(s)
    if m:
        notes = _NOTE_TOKEN_RE.findall(m.group(1))
        if len(notes) < 2:
            problems.append(_mk("E061", line_no, _col(s, "chromatic_run"), 13,
                                "chromatic_run needs two notes (start, end)"))
        for n in notes:
            if not _valid_note(n):
                problems.append(_mk("E060", line_no, _col(s, n), len(n),
                                    f"Unknown note name: {n}"))
        return "chromatic_run"
    m = _V2_KEY_RE.match(s)
    if m:
        scale = m.group(2).lower()
        if scale not in _SCALES:
            problems.append(_mk("E065", line_no, _col(s, m.group(0)),
                                len(m.group(0)),
                                f"Unknown scale: {m.group(2)}"))
        return "key"
    if s.startswith("[Section:") or s.startswith("[section:"):
        return "section"
    return None


_SCALES = {"major", "minor", "harmonicminor", "melodicminor", "pentatonic",
           "blues", "dorian", "phrygian", "lydian", "mixolydian", "locrian",
           "chromatic", "wholehalf", "halfwhole"}


def _valid_note(n):
    midi, ok = resolve_note(n)
    return ok


# ── v3 validator ──

_V3_NOTE_RE = re.compile(
    r"^([A-Ga-g]#?b?\d+)\s+([A-Za-z.]+|\d+)\s*([A-Za-z0-9.]+)?$"
)
_V3_MACRO_RE = re.compile(r"^!([a-zA-Z_]\w*)\s*=\s*(.+)$")


def check_v3_line(line, problems, line_no=0):
    """Validate v3 extended constructs. Returns kind or None.
    C4 q / C4 q mf / !macro = value"""
    s = line.strip()
    m = _V3_NOTE_RE.match(s)
    if m and _valid_note(m.group(1)):
        note, dur, vel = m.group(1), m.group(2), m.group(3)
        midi, ok = resolve_note(note)
        if not ok:
            problems.append(_mk("E060", line_no, _col(s, note), len(note),
                                f"Unknown note name: {note}"))
        if resolve_duration(dur) is None and not dur.replace(".", "", 1).isdigit():
            problems.append(_mk("E054", line_no, _col(s, dur), len(dur),
                                f"Unknown duration: {dur}"))
        if vel:
            v = resolve_velocity(vel)
            if v is None or v > 127:
                problems.append(_mk("E055", line_no, _col(s, vel), len(vel),
                                    f"Unknown velocity: {vel}"))
        return "note"
    m = _V3_MACRO_RE.match(s)
    if m:
        return "macro"
    return None
