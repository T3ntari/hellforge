"""v4 Generative/Algorithmic: scale quantization, multi-channel routing, conditional macros."""

import re
import random
from .directives import KEY_SCALES
from .events import name_to_midi


def process_quantization(text):
    """Process scale quantizers: N[60-72]!in(A_minor) -> snap to scale."""
    def quantize_match(m):
        note_range = m.group(1)
        scale_name = m.group(2).replace(' ', '_')
        min_n, max_n = 0, 127
        if '-' in note_range:
            parts = note_range.split('-')
            min_n = int(parts[0])
            max_n = int(parts[1]) if len(parts) > 1 else min_n + 12
        # Pick random note in range
        raw = random.randint(min_n, max_n)
        # Snap to scale
        scale = KEY_SCALES.get(scale_name)
        if scale:
            semitone = raw % 12
            octave = (raw // 12) * 12
            # Find closest scale note
            closest = min(scale, key=lambda s: abs((s % 12) - semitone))
            snapped = octave + (closest % 12)
            # Keep in range
            if snapped < min_n:
                snapped += 12
            elif snapped > max_n:
                snapped -= 12
            return f"N{snapped}"
        return f"N{raw}"

    text = re.sub(r'N\[(\d+-\d+)\!\w+\(([^)]+)\)', quantize_match, text)
    # Also handle simple range: N[60-72]
    text = re.sub(r'N\[(\d+)-(\d+)\]', lambda m: f"N{random.randint(int(m.group(1)), int(m.group(2)))}", text)
    return text


def process_channel_routing(text):
    """Process CH[10] and TRK[piano] prefixes, normalizing them for the parser."""
    # CH[10] T0 N36 -> attach channel info (parser already handles CH[])
    # TRK[piano] -> just pass through as comment for now
    text = re.sub(r'TRK\[([^\]]+)\]', r'// track: \1', text)
    return text


def process_conditional_macros(text):
    """Process !macro[+12], !macro[-5], !macro[inv], !macro^ (transpose), !macro_inv (invert)."""
    macros = {}
    result_lines = []
    for line in text.split('\n'):
        md = re.match(r'^!(\w+)\s*=\s*(.+)', line.strip())
        if md:
            macros[md.group(1)] = md.group(2).strip()
            result_lines.append(line)
            continue

        # Macro usage with bracket modifiers: !name[+12], !name[-5], !name[inv]
        mm = re.match(r'^!(\w+)(?:\[([+-]?\d+|inv)\])?(\^|_inv)?\s*$', line.strip())
        if mm:
            name = mm.group(1)
            bracket_val = mm.group(2)
            old_mod = mm.group(3)
            if name in macros:
                content = macros[name]

                # Bracket modifier takes priority
                if bracket_val == 'inv':
                    content = _invert_macro(content)
                elif bracket_val is not None:
                    semitones = int(bracket_val)
                    content = _transpose_macro(content, semitones)
                elif old_mod == '^':
                    content = _transpose_macro(content, 12)
                elif old_mod == '_inv':
                    content = _invert_macro(content)

                result_lines.append(content)
                continue
        result_lines.append(line)

    return '\n'.join(result_lines)


def _transpose_macro(content, semitones):
    """Transpose all MIDI notes in a macro by `semitones`, clamped to 0-127."""
    return re.sub(r'N(\d+)', lambda m: f'N{max(0, min(127, int(m.group(1)) + semitones))}', content)


def _invert_macro(content):
    """Invert intervals around the first note."""
    notes = re.findall(r'N(\d+)', content)
    if not notes:
        return content
    first = int(notes[0])
    for n in notes[1:]:
        interval = int(n) - first
        new_note = first - interval
        content = content.replace(f'N{n}', f'N{max(0, min(127, new_note))}', 1)
    return content


def process_generative(text):
    """Run all v4 generative processors in order."""
    text = process_quantization(text)
    text = process_channel_routing(text)
    text = process_conditional_macros(text)
    return text
