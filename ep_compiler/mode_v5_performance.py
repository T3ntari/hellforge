"""v5 Piano Performance features: sustain pedal, rests, articulations,
tuplets, octave shift, velocity curves, ties.

Statement-level constructs parsed before machine/human in compile_v1.
Preprocessor expands tuplets/ties in text. Post-passes apply curves/ties.
"""

import re
from .events import name_to_midi
from .syntax_check import resolve_duration

PEDAL_ON_RE = re.compile(r'^pedal\s+on\s*$', re.I)
PEDAL_OFF_RE = re.compile(r'^pedal\s+off\s*$', re.I)
REST_RE = re.compile(r'^[Rr]est\s+(\S+)\s*$')
REST_SHORT_RE = re.compile(r'^R\s+(\S+)\s*$')
TUPLET_3_RE = re.compile(r'^t(?:rip)?3?\s*\(\s*([A-Ga-g]#?b?\d+(?:\s+[A-Ga-g]#?b?\d+)*)\s*\)\s*(@.+)?$', re.I)
TUP_RE = re.compile(r'^tup\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*([A-Ga-g]#?b?\d+(?:\s*,\s*[A-Ga-g]#?b?\d+)*)\s*\)\s*(@.+)?$', re.I)
CURVE_VEL_RE = re.compile(r'@curve\s+vel\s+(\d+)\s+(\d+)(?:\s+over\s+(\d+(?:\.\d+)?)(ms|q|h|w|e|s|t))?', re.I)
TIE_SHORTHAND_RE = re.compile(r'^([A-Ga-g]#?b?\d+)~\s+(\S.*?)\s*$', re.I)


def _resolve_dur_str(dur_str, bpm):
    resolved = resolve_duration(dur_str)
    if resolved:
        return int(resolved[1] * 60000 / bpm)
    if dur_str.endswith('ms'):
        return int(float(dur_str[:-2]))
    if dur_str.replace('.', '', 1).isdigit():
        return int(float(dur_str) * 60000 / bpm)
    return 0


def _expand_triplet(notes, cursor, bpm, n, div):
    beat_ms = 60000 / bpm
    total_ms = beat_ms * div
    spacing = total_ms / n
    dur_ms = max(1, int(spacing * 0.9))
    events = []
    for i, note in enumerate(notes):
        midi = name_to_midi(note)
        events.append({
            "timestamp": int(cursor + i * spacing),
            "midi": midi,
            "duration": dur_ms,
            "velocity": 80,
            "pan": 0.0,
            "bend": 0,
        })
    return events, int(cursor + total_ms)


def create_sustain_event(timestamp, value):
    return {
        "timestamp": timestamp,
        "midi": 0,
        "duration": 1,
        "velocity": 0,
        "pan": 0.0,
        "bend": 0,
        "sustain": value,
        "pedal": True,
    }


def parse_performance_line(line, cursor, bpm, ll_state):
    """Parse a v5 performance statement line. Returns (events, new_cursor) or (None, cursor)."""
    s = line.strip()

    if PEDAL_ON_RE.match(s):
        ll_state['sustain_state'] = 127
        return [create_sustain_event(cursor, 127)], cursor
    if PEDAL_OFF_RE.match(s):
        ll_state['sustain_state'] = 0
        return [create_sustain_event(cursor, 0)], cursor

    m = REST_RE.match(s) or REST_SHORT_RE.match(s)
    if m:
        dur_str = m.group(1)
        dur_ms = _resolve_dur_str(dur_str, bpm)
        return [], cursor + max(0, dur_ms)

    m = TUP_RE.match(s)
    if m:
        n = int(m.group(1))
        div = int(m.group(2))
        notes_str = m.group(3)
        notes = re.findall(r'[A-Ga-g]#?b?\d+', notes_str)
        props = _parse_tup_props(m.group(4))
        if notes:
            events, new_cursor = _expand_triplet(notes, cursor, bpm, n, div)
            return _apply_tup_props(events, props, ll_state), new_cursor

    m = TUPLET_3_RE.match(s)
    if m:
        notes = re.findall(r'[A-Ga-g]#?b?\d+', m.group(1))
        props = _parse_tup_props(m.group(2))
        if notes:
            events, new_cursor = _expand_triplet(notes, cursor, bpm, len(notes), 2)
            return _apply_tup_props(events, props, ll_state), new_cursor

    return None, cursor


def _parse_tup_props(prop_str):
    """Parse trailing @props on tuplet statements. Returns dict with
    velocity/pan/channel/articulation/octave or empty dict."""
    out = {}
    if not prop_str:
        return out
    for m in re.finditer(r'@(\w+)\s*:\s*([^\s@]+)', prop_str):
        key, val = m.group(1).lower(), m.group(2)
        if key in ("vel", "velocity"):
            try:
                out["velocity"] = int(float(val) * 127) if float(val) <= 1.0 else int(float(val))
            except ValueError:
                from .syntax_check import resolve_velocity
                v = resolve_velocity(val)
                if v is not None:
                    out["velocity"] = v
        elif key == "pan":
            try:
                out["pan"] = float(val)
            except ValueError:
                pass
        elif key in ("ch", "channel"):
            try:
                out["channel"] = int(val)
            except ValueError:
                pass
        elif key in ("art", "articulation"):
            out["art"] = val
        elif key == "oct":
            try:
                out["octave"] = int(val)
            except ValueError:
                pass
    return out


def _apply_tup_props(events, props, ll_state):
    """Apply parsed @props (velocity/pan/channel/articulation/octave) to
    tuplet events. Global @oct from ll_state applies when no per-line @oct."""
    if not props:
        return events
    octave = props.get("octave", ll_state.get("octave") or 0)
    for e in events:
        if "velocity" in props:
            e["velocity"] = max(0, min(127, props["velocity"]))
        if "pan" in props:
            e["pan"] = max(-1.0, min(1.0, props["pan"]))
        if "channel" in props:
            e["channel"] = props["channel"]
        if octave:
            e["midi"] = max(0, min(127, e["midi"] + 12 * octave))
        if "art" in props:
            apply_articulation(e, props["art"])
    return events


def apply_articulation(event, art):
    if not art:
        return
    art = art.lower().strip()
    if art == 'staccato':
        event['duration'] = max(1, int(event.get('duration', 500) * 0.5))
    elif art == 'tenuto':
        pass
    elif art == 'legato':
        pass
    elif art == 'accent':
        event['velocity'] = min(127, event.get('velocity', 80) + 12)


def apply_velocity_curve(events, text, bpm):
    for m in CURVE_VEL_RE.finditer(text):
        v_start = int(m.group(1))
        v_end = int(m.group(2))
        window_str = m.group(3)
        window_unit = m.group(4)

        if window_str and events:
            if window_unit and window_unit != 'ms':
                dur_ms = int(float(window_str) * {"w": 4, "h": 2, "q": 1, "e": 0.5, "s": 0.25, "t": 0.125}.get(window_unit, 1) * 60000 / bpm)
            elif window_str.endswith('ms'):
                dur_ms = int(float(window_str[:-2]))
            else:
                dur_ms = int(float(window_str))
            t0 = events[0]["timestamp"]
            t_end = t0 + dur_ms
            window_events = [e for e in events if t0 <= e["timestamp"] < t_end and not e.get("pedal")]
            if len(window_events) < 2:
                window_events = [e for e in events if not e.get("pedal")][:2]
            for i, e in enumerate(window_events):
                frac = i / max(1, len(window_events) - 1)
                if not e.get("pedal"):
                    e["velocity"] = max(0, min(127, int(v_start + (v_end - v_start) * frac)))
        elif len(events) >= 2:
            non_pedal = [e for e in events if not e.get("pedal")]
            for i, e in enumerate(non_pedal):
                frac = i / max(1, len(non_pedal) - 1)
                e["velocity"] = max(0, min(127, int(v_start + (v_end - v_start) * frac)))
    return events


def apply_ties(events):
    merged = []
    i = 0
    while i < len(events):
        e = dict(events[i])
        j = i + 1
        while j < len(events) and e.get("tie") and events[j].get("midi") == e.get("midi"):
            e["duration"] = e.get("duration", 500) + events[j].get("duration", 500)
            if not events[j].get("tie"):
                e["tie"] = False
            j += 1
        merged.append(e)
        i = j
    return merged


def apply_sustain_state(events, ll_state):
    sustain_val = ll_state.get("sustain_state", 0)
    if sustain_val:
        for e in events:
            if e.get("sustain") is None:
                e["sustain"] = sustain_val


def apply_octave_shift(events, ll_state):
    default_oct = ll_state.get("octave", 0)
    for e in events:
        shift = e.get("octave", default_oct)
        if shift and e.get("midi", 0) > 0:
            e["midi"] = max(0, min(127, e["midi"] + 12 * shift))


def apply_legato(events):
    for i, e in enumerate(events):
        if e.get("art") != "legato":
            continue
        if i + 1 < len(events):
            nxt = events[i + 1]
            if nxt["timestamp"] > e["timestamp"]:
                e["duration"] = max(1, nxt["timestamp"] - e["timestamp"] + 10)


def apply_performance_post_passes(events, text, bpm, ll_state):
    apply_velocity_curve(events, text, bpm)
    events = apply_ties(events)
    apply_sustain_state(events, ll_state)
    apply_octave_shift(events, ll_state)
    apply_legato(events)
    return events


def process_performance_pre(text, bpm):
    """Preprocessor: expand ties and tuplets in raw text before compilation."""
    lines = text.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        m = TIE_SHORTHAND_RE.match(stripped)
        if m:
            note = m.group(1)
            rest_part = m.group(2)
            midi = name_to_midi(note)
            parts = rest_part.split()
            dur_strs = []
            other = []
            for p in parts:
                res = resolve_duration(p)
                if res:
                    dur_strs.append(p)
                else:
                    other.append(p)
            expanded = []
            for i, d in enumerate(dur_strs):
                dur_ms = _resolve_dur_str(d, bpm)
                extra = " ".join(other[i:]) if i == 0 else ""
                tag = " @tie" if i < len(dur_strs) - 1 else ""
                if extra:
                    expanded.append(f"play note({note}) @dur:{dur_ms}ms @vel:mf{tag} {extra}")
                else:
                    expanded.append(f"play note({note}) @dur:{dur_ms}ms @vel:mf{tag}")
            result.extend(expanded)
            continue
        result.append(line)
    return '\n'.join(result)
