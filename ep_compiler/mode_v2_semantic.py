"""v2 Semantic Syntax — compiles and emits v2 chord/section/degree format."""

import re

# Import the v2 compiler (local copy — legacy tools/v2compiler.py removed)
from ._v2compiler import (
    V2Compiler,
    KEYS,
    NOTE_TO_SEMI,
    SEMI_TO_NOTE,
    CHORD_INTERVALS,
    QUALITY_ALIASES,
)
from ._v2compiler import (
    parse_chord_name,
    chord_to_semitones,
    midi_from_note,
    parse_dur,
    parse_vel,
    DUR_BEATS,
)


def compile_v2(text):
    """Compile v2 semantic syntax text to events. Returns (events, bpm)."""
    compiler = V2Compiler()
    compiler.parse(text)
    events = sorted(compiler.events, key=lambda e: (e["timestamp"], e["midi"]))
    bpm = compiler.tempo
    return events, bpm


def detect_v2(text):
    """Check if text looks like v2 semantic syntax."""
    patterns = [r'\[Section:', r'Key:\s*\w+_\w+', r'\{Chord_Block:',
                r'arpeggio\(', r'chromatic_run\(']
    for p in patterns:
        if re.search(p, text, re.I):
            return True
    return False


def events_to_v2(events, bpm, source_ver="v1"):
    """Convert flat events to v2 semantic text.
    Returns v2 source code compatible with compile_v2()."""
    from ep_compiler.events import midi_to_name

    sorted_ev = sorted(events, key=lambda e: e["timestamp"])
    beat_ms = 60000 / bpm if bpm > 0 else 500

    lines = []
    if source_ver != "v2":
        lines.append("// Ported from {} by Portbaby".format(source_ver))
    lines.append("[Section: Main]")
    lines.append("  Key: C_Major")
    lines.append("  Tempo: {}".format(int(bpm)))
    lines.append("  Time: 4/4")
    lines.append("")

    # Detect chord changes by grouping events close in time
    chords = []
    current_chord = []
    chord_start = 0

    for e in sorted_ev:
        if not current_chord or e["timestamp"] - chord_start < beat_ms * 0.5:
            if not current_chord:
                chord_start = e["timestamp"]
            current_chord.append(e)
        else:
            if current_chord:
                chords.append(list(current_chord))
            current_chord = [e]
            chord_start = e["timestamp"]
    if current_chord:
        chords.append(list(current_chord))

    # Generate chord block
    if chords:
        num_bars = max(1, len(chords))
        lines.append("  {{Chord_Block: {}_bars}}".format(num_bars))

        chord_names = []
        for group in chords:
            # Determine chord from the notes in this group
            if len(group) >= 2:
                semis = sorted(set(e["midi"] % 12 for e in group))
                root_semi = semis[0] if semis else 0
                root_note = SEMI_TO_NOTE[root_semi % 12]
                # Guess quality from intervals present
                intervals = sorted((s - root_semi) % 12 for s in semis)
                quality = "major"
                if 3 in intervals and 7 not in intervals:
                    quality = "minor"
                elif 3 in intervals and 10 in intervals:
                    quality = "minor"
                elif 4 in intervals and 10 in intervals:
                    quality = "dom7"
                chord_names.append("{}_{}".format(root_note, quality))
            else:
                # Single note — use as root
                root_semi = group[0]["midi"] % 12
                root_note = SEMI_TO_NOTE[root_semi]
                chord_names.append("{}_{}".format(root_note, "major"))

        # Write chord line
        chord_line = "    " + " | ".join(chord_names)
        lines.append(chord_line)
        lines.append("  {End}")
        lines.append("")

    # Generate melody block
    lines.append("  {Melody_Block}")
    for e in sorted_ev[:50]:
        note_name = SEMI_TO_NOTE[e["midi"] % 12]
        octave = e["midi"] // 12 - 1
        dur_beats = e["duration"] / beat_ms if beat_ms > 0 else 1
        # Find closest duration code
        dur_code = "quarter"
        min_diff = 999
        for code, beats in DUR_BEATS.items():
            if abs(beats - dur_beats) < min_diff and not code.startswith("dotted") and not code.startswith("triplet"):
                min_diff = abs(beats - dur_beats)
                dur_code = code
        vel = e["velocity"]
        if vel >= 112:
            vel_code = "ff"
        elif vel >= 96:
            vel_code = "f"
        elif vel >= 80:
            vel_code = "mf"
        elif vel >= 64:
            vel_code = "mp"
        elif vel >= 49:
            vel_code = "p"
        else:
            vel_code = "pp"

        lines.append("    play(note={}{}, dur={}, vel={})".format(note_name, octave, dur_code, vel_code))

    if len(sorted_ev) > 50:
        lines.append("    // ... {} more notes".format(len(sorted_ev) - 50))

    lines.append("  {End}")
    lines.append("{End}")

    return "\n".join(lines)
