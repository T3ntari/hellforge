"""Event data structures, creation, and validation for E Language."""

import re

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']


def create_event(timestamp=0, midi=60, duration=500, velocity=80,
                 pan=0.0, bend=0, **kwargs):
    """Create a standardized event dict with defaults."""
    return {
        "timestamp": max(0, int(timestamp)),
        "midi": max(0, min(127, int(midi))),
        "duration": max(1, int(duration)),
        "velocity": max(0, min(127, int(velocity))),
        "pan": max(-1.0, min(1.0, float(pan))),
        "bend": max(-64, min(64, int(bend))),
        **kwargs,
    }


def midi_to_name(midi):
    """Convert MIDI number to note name (e.g., 60 -> C4)."""
    return f"{NOTE_NAMES[midi % 12]}{midi // 12 - 1}"


def name_to_midi(name):
    """Convert note name to MIDI (e.g., C4 -> 60)."""
    match = re.match(r'^([A-G]#?b?)(\d+)$', name)
    if not match:
        return 60
    pitch, octave = match.group(1), int(match.group(2))
    semi = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'F':5,
            'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11}.get(pitch, 0)
    return semi + (octave + 1) * 12


def validate_events(events):
    """Validate events. Removes out-of-range and zero-duration events. Returns (cleaned, removed_count)."""
    cleaned = []
    for e in events:
        midi = e.get("midi", -1)
        if midi < 0 or midi > 127:
            continue
        if e.get("duration", 0) <= 0:
            continue
        e["velocity"] = max(0, min(127, e.get("velocity", 80)))
        cleaned.append(e)
    return cleaned, len(events) - len(cleaned)


def sort_events(events):
    """Sort events by timestamp."""
    return sorted(events, key=lambda e: (e["timestamp"], e["midi"]))
