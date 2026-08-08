"""#HUMAN mode parser: play note(C4) @dur:q @vel:mf syntax.

Strict: unknown @properties, unknown qualities/words report typed problems
via ep_compiler.syntax_check instead of failing silently or defaulting to major."""

import re

from .events import name_to_midi
from .directives import parse_directives
from .syntax_check import (
    check_human_line,
    resolve_duration,
    resolve_velocity,
    resolve_quality,
    HUMAN_PROP_RE,
)

last_problems = []

DUR_MAP = {
    'w': 4, 'h': 2, 'q': 1, 'e': 0.5, 's': 0.25, 't': 0.125,
    'whole': 4, 'half': 2, 'quarter': 1, 'eighth': 0.5,
    'sixteenth': 0.25, 'thirtysecond': 0.125,
}

VEL_MAP = {
    'ppp': 16, 'pp': 33, 'p': 49, 'mp': 64, 'mf': 80,
    'm': 90, 'f': 96, 'ff': 112, 'fff': 126,
    'soft': 49, 'normal': 80, 'loud': 112, 'max': 127, 'silent': 0,
}

QUAL_MAP = {
    'major': [0, 4, 7], 'minor': [0, 3, 7], 'dim': [0, 3, 6], 'aug': [0, 4, 8],
    'dom7': [0, 4, 7, 10], 'maj7': [0, 4, 7, 11], 'min7': [0, 3, 7, 10],
    'dim7': [0, 3, 6, 9], 'sus2': [0, 2, 7], 'sus4': [0, 5, 7],
    'm': [0, 3, 7], 'm7': [0, 3, 7, 10], '7': [0, 4, 7, 10],
    'maj': [0, 4, 7], 'min': [0, 3, 7],
}


def parse_human_props(prop_str, bpm, problems=None, line_no=0, line=""):
    """Parse @dur:q @vel:mf etc. into a dict. Unknown/bad values → problems."""
    out = {}
    for m in HUMAN_PROP_RE.finditer(prop_str or ""):
        key, val = m.group(1).lower(), m.group(2)
        if key in ('dur', 'duration'):
            resolved = resolve_duration(val)
            if resolved:
                out['dur_ms'] = int(resolved[1] * 60000 / bpm)
            elif val.endswith('ms'):
                out['dur_ms'] = float(val[:-2])
            elif val.replace('.', '', 1).isdigit():
                out['dur_ms'] = float(val) * 60000 / bpm
            else:
                if problems is not None:
                    problems.append(_prob("E054", line_no, _col(line, m.group(0)),
                                          len(m.group(0)),
                                          f"Unknown duration: {val}"))
        elif key in ('vel', 'velocity'):
            v = resolve_velocity(val)
            if v is not None:
                out['vel'] = v
            elif problems is not None:
                problems.append(_prob("E055", line_no, _col(line, m.group(0)),
                                      len(m.group(0)),
                                      f"Unknown velocity: {val}"))
        elif key == 'pan':
            try: out['pan'] = float(val)
            except ValueError: pass
        elif key == 'bend':
            try: out['bend'] = int(val)
            except ValueError: pass
        elif key in ('ch', 'channel'):
            try: out['channel'] = int(val)
            except ValueError: pass
        elif key == 'track':
            out['track'] = val
        elif key in ('time', 'ts', 'timestamp'):
            try:
                if val.endswith('s') and not val.endswith('ms'):
                    out['timestamp'] = int(float(val[:-1]) * 1000)
                elif val.endswith('ms'):
                    out['timestamp'] = int(float(val[:-2]))
                elif '.' in val:
                    out['timestamp'] = int(float(val) * 1000)
                else:
                    out['timestamp'] = int(val)
            except (ValueError, IndexError): pass
        elif key in ('note', 'sustain'):
            out['note'] = val
        elif key in ('vol', 'volume'):
            try: out['master_vol'] = float(val)
            except ValueError: pass
        elif key == 'master':
            try: out['master_vol'] = float(val)
            except ValueError: pass
        elif key == 'gain':
            try: out['gain_db'] = float(val.replace('db', ''))
            except (ValueError, AttributeError): pass
        elif key == 'strum':
            try:
                t = float(val) if val.replace('.', '', 1).isdigit() else 0.02
                out['strum'] = {"time": t}
            except ValueError:
                pass
    return out


def _prob(code, line, char, length, msg):
    return {"code": code, "line": line, "char": char,
            "length": max(1, length), "message": msg}


def _col(s, needle):
    idx = s.find(needle)
    return idx if idx >= 0 else 0


def parse_human_line(line, cursor, bpm, ll_state):
    """Parse a #HUMAN line. Returns (events, new_cursor) or (None, cursor).
    Problems (with code/line/char/length) are appended to last_problems."""
    problems = []
    kind = check_human_line(line, problems, 0)
    if kind is None:
        last_problems.extend(problems)
        return None, cursor

    kind, note_or_root, quality, props = kind

    # Strict problems from syntax_check (missing dur/vel, unknown quality...)
    last_problems.extend(problems)

    if kind == "note":
        note_str = note_or_root
        midi = name_to_midi(note_str) if re.match(r"^[A-Ga-g]#?b?\d+$", note_str) else None
        if midi is None:
            return None, cursor
        prop_dict = parse_human_props(_props_of(line), bpm)
        dur_ms = prop_dict.get("dur_ms") or (60000 / bpm)
        vel = prop_dict.get("vel") or 80
        ts = prop_dict.get("timestamp", cursor)
        ev = {
            "timestamp": ts, "midi": midi,
            "duration": int(dur_ms), "velocity": vel,
            "pan": prop_dict.get("pan", 0.0), "bend": prop_dict.get("bend", 0),
            "master_vol": prop_dict.get("master_vol", ll_state.get("master_vol")),
            "gain_db": prop_dict.get("gain_db", ll_state.get("gain_db")),
            "channel": prop_dict.get("channel"),
            "track": prop_dict.get("track"),
        }
        new_cursor = ts + int(dur_ms)
        return [ev], max(cursor, new_cursor)

    # chord
    root_str, quality = note_or_root, quality
    intervals = QUAL_MAP.get((quality or "").lower(), [0, 4, 7])
    root_midi = name_to_midi(root_str + "4")
    prop_dict = parse_human_props(_props_of(line), bpm)
    dur_ms = prop_dict.get("dur_ms") or (60000 / bpm)
    vel = prop_dict.get("vel") or 80
    strum = prop_dict.get("strum")
    ts = prop_dict.get("timestamp", cursor)
    events = []
    for i, interval in enumerate(intervals):
        offset = i * strum["time"] if strum else 0
        events.append({
            "timestamp": ts + offset, "midi": root_midi + interval,
            "duration": max(1, int(dur_ms) - offset), "velocity": vel,
            "pan": prop_dict.get("pan", 0.0), "bend": prop_dict.get("bend", 0),
            "master_vol": prop_dict.get("master_vol", ll_state.get("master_vol")),
            "channel": prop_dict.get("channel"),
            "track": prop_dict.get("track"),
        })
    new_cursor = ts + int(dur_ms)
    return events, max(cursor, new_cursor)


def _props_of(line):
    """Extract the @... section of a human line."""
    idx = line.find("@")
    return line[idx:] if idx >= 0 else ""
