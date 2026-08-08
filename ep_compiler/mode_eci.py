""".eci format — toggleable mode directives within a single file.
@mode machine → T0 N60 D500 V0.8
@mode human  → play note(C4) @dur:q @vel:mf
@mode auto   → auto-detect per line (default)
@mode strict → fail on unparseable lines
"""
import re
from .compile import compile_v1
from .events import (
    validate_events,
    sort_events,
)
from .comments import strip_comments

MODE_RE = re.compile(r'@mode\s+(machine|human|auto|strict)', re.I)

# Auto-detect signature patterns for disambiguation
MACHINE_SIG_RE = re.compile(r'^T\d+')
HUMAN_SIG_RE = re.compile(r'play\s+(?:note|chord)\s*\(')
V3_NOTE_RE = re.compile(r'^[A-G]#?b?\d+\s+[whqest]')
MACRO_DEF_RE = re.compile(r'^!\w+\s*=')
PROBABILITY_RE = re.compile(r'^\?\d+\.\d+\s+T')
COMMENT_RE = re.compile(r'^\s*//')


class ECIError(Exception):
    """Raised when .eci strict mode encounters unparseable content."""


def compile_eci(text, bpm=120, ll_state=None):
    """Compile .eci text with toggleable modes. Returns (events, bpm).
    Supports @mode machine|human|auto|strict."""
    from .directives import (
        parse_directives,
        DEFAULT_LL_STATE,
    )
    from .mode_v1_machine import parse_machine_line
    from .mode_v1_human import parse_human_line
    from .comments import strip_line

    text = strip_comments(text)

    if ll_state is None:
        ll_state = dict(DEFAULT_LL_STATE)
    ll_state = parse_directives(text, ll_state)
    bpm = ll_state.get("bpm", bpm) or bpm

    events = []
    cursor = 0
    current_mode = "auto"
    silent_fail_count = 0
    MAX_SILENT_FAIL = 10

    for line in text.split("\n"):
        raw = line
        line = strip_line(line).strip()
        if not line:
            continue

        # Check for mode switch
        m = MODE_RE.match(line)
        if m:
            current_mode = m.group(1).lower()
            silent_fail_count = 0
            continue

        parsed = False

        if current_mode == "machine":
            ev = parse_machine_line(line, ll_state)
            if ev:
                events.append(ev)
                end = ev["timestamp"] + ev["duration"]
                if end > cursor:
                    cursor = end
                parsed = True

        elif current_mode == "human":
            ev_list, new_cursor = parse_human_line(line, cursor, bpm, ll_state)
            if ev_list:
                events.extend(ev_list)
                cursor = new_cursor
                parsed = True

        elif current_mode == "strict":
            # Try machine, then human; fail if neither matches
            from .mode_v1_machine import parse_machine_line as pm
            ev = pm(line, ll_state)
            if ev:
                events.append(ev)
                end = ev["timestamp"] + ev["duration"]
                if end > cursor:
                    cursor = end
                parsed = True
            else:
                ev_list, new_cursor = parse_human_line(line, cursor, bpm, ll_state)
                if ev_list:
                    events.extend(ev_list)
                    cursor = new_cursor
                    parsed = True
            if not parsed:
                raise ECIError(f"Strict mode: unparseable line '{line[:60]}'")

        else:  # auto
            # Use signature-based routing to avoid misclassification drift
            if MACHINE_SIG_RE.match(line):
                ev = parse_machine_line(line, ll_state)
                if ev:
                    events.append(ev)
                    end = ev["timestamp"] + ev["duration"]
                    if end > cursor:
                        cursor = end
                    parsed = True
            elif HUMAN_SIG_RE.match(line):
                ev_list, new_cursor = parse_human_line(line, cursor, bpm, ll_state)
                if ev_list:
                    events.extend(ev_list)
                    cursor = new_cursor
                    parsed = True
            elif V3_NOTE_RE.match(line) or MACRO_DEF_RE.match(line) or PROBABILITY_RE.match(line):
                # Route to v3 preprocessor via the main compile pipeline
                from .compile import compile_source
                sub_ev, _ = compile_source(line, bpm=bpm)
                if sub_ev:
                    for e in sub_ev:
                        e["timestamp"] += cursor
                    events.extend(sub_ev)
                    last = max(e["timestamp"] + e["duration"] for e in sub_ev)
                    cursor = max(cursor, last)
                    parsed = True
            else:
                # Fallback: try machine first, then human
                ev = parse_machine_line(line, ll_state)
                if ev:
                    events.append(ev)
                    end = ev["timestamp"] + ev["duration"]
                    if end > cursor:
                        cursor = end
                    parsed = True
                else:
                    ev_list, new_cursor = parse_human_line(line, cursor, bpm, ll_state)
                    if ev_list:
                        events.extend(ev_list)
                        cursor = new_cursor
                        parsed = True

        if not parsed:
            silent_fail_count += 1
            if silent_fail_count >= MAX_SILENT_FAIL:
                print(f"  [eci] warning: {silent_fail_count} consecutive unparseable lines under @mode {current_mode}")

    events = sort_events(events)
    events, _ = validate_events(events)
    return events, bpm
