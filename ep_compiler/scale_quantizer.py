"""Scale quantizer — snaps MIDI notes to the nearest valid scale degree.
Vectorized with NumPy for performance on large event lists."""

from .directives import KEY_SCALES
import numpy as np

# Cache of scale semitone sets for fast lookup
SCALE_SEMITONES = {name: sorted(set(notes)) for name, notes in KEY_SCALES.items()}

# Pre-compute lookup tables per scale for O(1) quantization
_LOOKUP_TABLES = {}


def _build_lookup(scale_name):
    """Build a vectorized lookup table: for each of 12 semitones, the nearest in-scale semitone."""
    semitones = SCALE_SEMITONES.get(scale_name)
    if not semitones:
        return None
    semi_arr = np.array(semitones, dtype=np.int32)
    table = np.zeros(12, dtype=np.int32)
    for semi in range(12):
        table[semi] = semi_arr[np.argmin(np.abs(semi_arr - semi))]
    return table


def quantize_events(events, scale_name):
    """Snap all MIDI note numbers in events to the nearest scale degree.
    Vectorized via NumPy. scale_name: e.g., 'A_minor', 'C_Major'.
    """
    semitones = SCALE_SEMITONES.get(scale_name)
    if not semitones:
        return events

    # Build or fetch lookup table
    if scale_name not in _LOOKUP_TABLES:
        _LOOKUP_TABLES[scale_name] = _build_lookup(scale_name)
    lookup = _LOOKUP_TABLES[scale_name]

    if len(events) < 50:
        # Small batch: use simple loop (avoids numpy overhead)
        for e in events:
            midi = e.get("midi", 60)
            semi = midi % 12
            octave = (midi // 12) * 12
            snapped = octave + lookup[semi]
            if snapped < 0:
                snapped += 12
            elif snapped > 127:
                snapped -= 12
            e["midi"] = int(snapped)
    else:
        # Large batch: vectorized
        midis = np.array([e.get("midi", 60) for e in events], dtype=np.int32)
        semis = midis % 12
        octaves = (midis // 12) * 12
        snapped = octaves + lookup[semis]
        # Clamp to valid MIDI range
        snapped = np.clip(snapped, 0, 127)
        for i, e in enumerate(events):
            e["midi"] = int(snapped[i])

    return events


def available_scales():
    """Return list of valid scale names."""
    return list(SCALE_SEMITONES.keys())
