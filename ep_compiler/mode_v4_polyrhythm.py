"""v4 Polyrhythm/Tuplet processor: nested triplets, Euclidean rhythms, polyrhythms, key mods.

Supports pipe-chords: [C4|E4|G4] = all notes simultaneous at each step."""

import re
from collections import deque
from .events import name_to_midi

RITARD_RE = re.compile(r'ritard(?:ando)?\(([\d.]+)\s*bars?\)\s*->\s*(\d+)', re.I)
KEY_MOD_RE = re.compile(r'@key\s+(\w[\w#]*)', re.I)
CURVE_RE = re.compile(r'@tempo\s+(\d+)\s*->\s*(\d+)', re.I)
EUCLID_RE = re.compile(r'(?:\[([^\]]+)\])?\s*E\((\d+),(\d+)\)', re.I)
POLY_RE = re.compile(r'\[([^\]]+)\]\s*\((\d+):(\d+)\)', re.I)
SHORTHAND_POLY_RE = re.compile(r'(?:CH(\d+)\s+)?(\d+):(\d+)\s+([A-Ga-g]#?b?\d+(?:\|[A-Ga-g]#?b?\d+)*)\s+([whqest])', re.I)


def _bjorklund(pulses, steps):
    """Bjorklund algorithm: distribute `pulses` across `steps` as evenly as possible.
    Returns a list of ints where 1 = pulse, 0 = rest."""
    if pulses >= steps:
        return [1] * steps
    if pulses == 0:
        return [0] * steps
    pattern = []
    remainders = [[1]] * pulses + [[0]] * (steps - pulses)
    while len(remainders) > 1:
        merged = []
        i, j = 0, len(remainders) // 2
        while i < len(remainders) // 2 and j < len(remainders):
            merged.append(remainders[i] + remainders[j])
            i += 1
            j += 1
        remainders = merged + remainders[i:] + remainders[j:]
    return remainders[0] if remainders else [1] * pulses


def _split_entries(notes_str):
    """'C4|E4|G4' -> [['C4','E4','G4']] (chord), 'C4 D4' -> [['C4'],['D4']]."""
    entries = []
    for group in re.split(r"\s+", notes_str.strip()):
        if not group:
            continue
        parts = [p for p in group.split("|") if p]
        entries.append(parts)
    return entries


def _expand_group(notes_text, total_slots, bpm, depth=0):
    """Expand a group of notes (possibly nested) into E language lines.
    total_slots = how many equal-time divisions to split the beat into.
    Returns list of strings like ['T0 N60 D125 V0.8', ...]"""
    beat_ms = 60000 / bpm
    slot_ms = beat_ms / total_slots

    # First, recursively expand any nested groups [...]/N inside this group
    # Find the innermost nested group
    nested_pattern = re.compile(r'\[([^\[\]]+)\]\s*/(\d+)')
    while True:
        m = nested_pattern.search(notes_text)
        if not m:
            break
        inner = m.group(1)
        divisor = int(m.group(2))
        expanded = _expand_group(inner, divisor, bpm, depth + 1)
        joined = "\n".join(expanded)
        notes_text = notes_text[:m.start()] + f'{{NESTED}}\n{joined}\n{{END}}' + notes_text[m.end():]

    # Now extract all tokens from the (possibly expanded) group text
    # They can be note names (C4, D#5) or nested markers
    tokens = []
    for part in re.split(r'[\s,]+', notes_text):
        part = part.strip()
        if not part:
            continue
        if part.startswith('{NESTED}'):
            tokens.append(('nested', part))
        elif re.match(r'^[A-G]#?b?\d+$', part, re.I):
            tokens.append(('note', part))
        else:
            # Might be a rest marker
            if part.lower() == 'r' or part.lower() == 'rest':
                tokens.append(('rest', None))

    # Distribute tokens across slots
    lines = []
    for i, (tok_type, tok_val) in enumerate(tokens):
        ts = i * slot_ms
        dur = max(1, int(slot_ms * 0.9))
        if tok_type == 'note':
            midi = name_to_midi(tok_val)
            lines.append(f"T{int(ts)} N{midi} D{dur} V0.8")
        elif tok_type == 'rest':
            pass  # skip, add silence
        elif tok_type == 'nested' and tok_val:
            # Shift nested expanded lines by ts
            pass  # already inlined

    # If we have nested content, we need to handle it differently
    # Re-parse the full notes_text for nested markers that were inlined
    return lines if not any('{NESTED}' in notes_text for _ in [1]) else _flatten_nested(notes_text, bpm)


def _flatten_nested(text, bpm):
    """Flatten nested groups: extract {NESTED} blocks and interleave with direct notes."""
    lines = []
    # Split on {NESTED} markers
    parts = re.split(r'\{NESTED\}\n(.*?)\n\{END\}', text, flags=re.DOTALL)
    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Direct notes
            for tok in re.findall(r'[A-G]#?b?\d{1,2}(?!\d)', part, re.I):
                midi = name_to_midi(tok)
                lines.append(f"T0 N{midi} D100 V0.8")
        else:
            # Already expanded nested content — add with proper timing
            for line in part.strip().split('\n'):
                if line.strip():
                    lines.append(line)
    return lines


def process_polyrhythms(text, bpm=120):
    """Preprocess text: expand nested triplets, Euclidean rhythms, polyrhythms, ritard, key mods."""
    lines = text.split('\n')
    result = []

    def _expand_simple_triplet(m):
        """Expand [C4 D4 E4]/3 style triplets."""
        notes_str, divisor = m.group(1), int(m.group(2))
        entries = _split_entries(notes_str)
        if not entries:
            return m.group(0)
        beat_ms = 60000 / bpm
        spacing = beat_ms / divisor
        expanded = []
        for i, entry in enumerate(entries):
            ts = i * spacing
            for note in entry:
                midi = name_to_midi(note)
                expanded.append(f"T{int(ts)} N{midi} D{int(spacing * 0.9)} V0.8")
        return "\n".join(expanded)

    def _expand_euclidean(m):
        """Expand E(5,4) or [C4 E4 G4] E(5,4) — Euclidean rhythm.
        Pipe entries are chords."""
        notes_str = m.group(1)
        pulses, steps = int(m.group(2)), int(m.group(3))
        pattern = _bjorklund(pulses, steps)

        entries = _split_entries(notes_str or "") if notes_str else [["60"]]
        beat_ms = 60000 / bpm
        # Total time = steps beats, divided into pulses equal slots
        total_ms = beat_ms * steps
        slot_ms = total_ms / pulses

        entry_idx = 0
        expanded = []
        # Play notes at evenly spaced intervals regardless of pattern
        for i in range(pulses):
            entry = entries[entry_idx % len(entries)]
            entry_idx += 1
            ts = i * slot_ms
            for note in entry:
                if note.startswith('N'):
                    midi = int(note[1:])
                else:
                    midi = name_to_midi(note)
                expanded.append(f"T{int(ts)} N{midi} D{int(slot_ms * 0.9)} V0.8")
        return "\n".join(expanded)

    def _expand_polyrhythm(m):
        """Expand [C4 D4 E4 F4 G4] (5:4) — 5 steps in space of 4 beats.
        Pipe entries [C4|E4|G4] = chord (all notes simultaneous at that step)."""
        notes_str = m.group(1)
        num_notes = int(m.group(2))
        span_beats = int(m.group(3))
        entries = _split_entries(notes_str)
        if not entries:
            return m.group(0)
        beat_ms = 60000 / bpm
        total_ms = beat_ms * span_beats
        spacing = total_ms / num_notes
        expanded = []
        for i in range(num_notes):
            entry = entries[i % len(entries)]
            ts = i * spacing
            for note in entry:
                midi = name_to_midi(note)
                expanded.append(f"T{int(ts)} N{midi} D{int(spacing * 0.9)} V0.8")
        return "\n".join(expanded)

    def _expand_simple_slots(content, divisor, bpm):
        """Distribute note entries across `divisor` equal slots.
        Pipe entries are chords."""
        entries = _split_entries(content)
        if not entries:
            return []
        beat_ms = 60000 / bpm
        spacing = beat_ms / divisor
        result = []
        for i, entry in enumerate(entries):
            ts = i * spacing
            for note in entry:
                midi = name_to_midi(note)
                result.append(f"T{int(ts)} N{midi} D{int(spacing * 0.9)} V0.8")
        return result

    for raw_line in lines:
        line = raw_line.strip()
        original = raw_line

        # Shorthand polyrhythm: [CH<n>] <a>:<b> <note|notes> <dur>   (e.g. "CH0 3:2 C4|E4 e")
        # = <a> steps of the note/chord evenly spaced across <b> beats.
        while True:
            m = SHORTHAND_POLY_RE.search(line)
            if not m:
                break
            ch, a, b, note_spec, dur_code = m.groups()
            a, b = int(a), int(b)
            beat_ms = 60000 / bpm
            total_ms = beat_ms * b
            spacing = total_ms / a
            dur_beats = {'w': 4, 'h': 2, 'q': 1, 'e': 0.5, 's': 0.25, 't': 0.125}[dur_code]
            dur_ms = int(dur_beats * beat_ms * 0.9)
            notes = [n for n in note_spec.split("|") if n]
            ch_prefix = f"CH{ch} " if ch else ""
            expanded_lines = []
            for i in range(a):
                ts = int(i * spacing)
                for note in notes:
                    midi = name_to_midi(note)
                    expanded_lines.append(f"{ch_prefix}T{ts} N{midi} D{dur_ms} V0.8")
            line = line[:m.start()] + "\n".join(expanded_lines) + line[m.end():]

        # Euclidean rhythm: E(5,4) or [C4 E4 G4] E(5,4)
        while True:
            m = EUCLID_RE.search(line)
            if not m:
                break
            replacement = _expand_euclidean(m)
            line = line[:m.start()] + replacement + line[m.end():]

        # Polyrhythm: [notes] (5:4)
        while True:
            m = POLY_RE.search(line)
            if not m:
                break
            replacement = _expand_polyrhythm(m)
            line = line[:m.start()] + replacement + line[m.end():]

        # Innermost-first group expansion: repeatedly find and expand [...]/N
        # This handles both simple [C4 D4 E4]/3 AND nested [C4 [D4 E4]/3 G4]/4
        inner_pat = re.compile(r'\[([^\[\]]+)\]\s*/(\d+)')
        # First expand all innermost groups
        while True:
            m = inner_pat.search(line)
            if not m:
                break
            content, divisor = m.group(1), int(m.group(2))
            expanded = _expand_simple_slots(content, divisor, bpm)
            if expanded:
                line = line[:m.start()] + "\n".join(expanded) + line[m.end():]
            else:
                line = line[:m.start()] + line[m.end():]

        # Now expand any remaining top-level [...]/N groups (if nesting created new ones)
        top_pat = re.compile(r'\[([^\[\]]+)\]\s*/(\d+)')
        while True:
            m = top_pat.search(line)
            if not m:
                break
            content, divisor = m.group(1), int(m.group(2))
            expanded = _expand_simple_slots(content, divisor, bpm)
            if expanded:
                line = line[:m.start()] + "\n".join(expanded) + line[m.end():]
            else:
                line = line[:m.start()] + line[m.end():]

        # Polyrhythm markers as comments
        line = re.sub(r'\((\d+):(\d+)\)', r'// polyrhythm \1:\2', line)

        # Ritardando
        rm = RITARD_RE.search(line)
        if rm:
            target_bpm = float(rm.group(2))
            line = line[:rm.start()] + f"@bpm {target_bpm}  // ritard" + line[rm.end():]

        # Tempo curves
        cm = CURVE_RE.search(line)
        if cm:
            start, end = float(cm.group(1)), float(cm.group(2))
            line = line[:cm.start()] + f"@bpm {(start+end)/2:.0f}  // tempo curve" + line[cm.end():]

        result.append(line if line != original else original)

    return '\n'.join(result)
