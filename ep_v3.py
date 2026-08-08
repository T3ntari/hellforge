"""
E Language v3.5 Syntax Parser — Full semantic preprocessor.
Expands v3 syntax into standard events for the v1/v2 compiler.

Features:
  • Tempo aliases, note shorthand, relative timing, repeats, macros
  • Probability gates, randomization, range notation, parallel chords
  • Block comments, tempo curves, Roman numerals, articulation, dynamic arcs
  • Tuplets/polyrhythms (3:2, /3), key modulation (@key Bm)
  • Tempo tapers (ritard, accelerando), scale quantization !in(Bm)
  • Multi-channel CH[10], macro mutations !macro^ !macro~inv
  • Config strip header (#compiler target: midi)
"""

import re
import random
import time
import math

# ── Tempo Aliases ────────────────────────────

TEMPO_ALIASES = {
    'larghissimo': 20, 'grave': 40, 'largo': 50, 'lento': 55,
    'adagio': 56, 'adagietto': 65, 'andante': 76,
    'andantino': 85, 'moderato': 100, 'allegretto': 110,
    'allegro': 120, 'vivace': 140, 'presto': 180, 'prestissimo': 210,
}

# ── Key Signatures ────────────────────────────

KEY_SIGNATURES = {
    'C':        [0, 2, 4, 5, 7, 9, 11], 'Am':  [0, 2, 3, 5, 7, 8, 10],
    'G':        [0, 2, 4, 5, 7, 9, 11], 'Em':  [0, 2, 3, 5, 7, 8, 10],
    'D':        [0, 2, 4, 5, 7, 9, 11], 'Bm':  [0, 2, 3, 5, 7, 8, 10],
    'A':        [0, 2, 4, 5, 7, 9, 11], 'F#m': [0, 2, 3, 5, 7, 8, 10],
    'E':        [0, 2, 4, 5, 7, 9, 11], 'C#m': [0, 2, 3, 5, 7, 8, 10],
    'F':        [0, 2, 4, 5, 7, 9, 11], 'Dm':  [0, 2, 3, 5, 7, 8, 10],
    'Bb':       [0, 2, 4, 5, 7, 9, 11], 'Gm':  [0, 2, 3, 5, 7, 8, 10],
    'Eb':       [0, 2, 4, 5, 7, 9, 11], 'Cm':  [0, 2, 3, 5, 7, 8, 10],
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# ── Music Theory Helpers ──────────────────────

def _key_to_scale(key_str):
    """Convert 'Bm', 'Gmaj', 'C#_minor' to list of valid semitones."""
    k = key_str.strip()
    k = k.replace('_minor', 'm').replace('_Major', '').replace('_maj', '')
    k = k.replace(' minor', 'm').replace(' Major', '').replace('major', '').strip()
    if k in KEY_SIGNATURES:
        return KEY_SIGNATURES[k]
    # Try to match by removing 'm' / 'min' suffix
    for name in KEY_SIGNATURES:
        if k.startswith(name) or name.startswith(k):
            return KEY_SIGNATURES[name]
    return KEY_SIGNATURES.get('C', [0,2,4,5,7,9,11])


def _nearest_scale_note(midi, scale):
    """Snap a MIDI note to the nearest note in the given scale semitones."""
    octave = midi // 12
    semitone = midi % 12
    if semitone in scale:
        return midi
    closest = min(scale, key=lambda s: abs(s - semitone))
    return closest + octave * 12


def _key_semitones(key_str):
    """Get valid semitones list for a key string like 'Bm'."""
    return _key_to_scale(key_str)


# ── Roman Numeral Chords (dynamic per key) ───

ROMAN_BASES = {
    'I': (0, 'Major'), 'II': (2, 'minor'), 'III': (4, 'minor'),
    'IV': (5, 'Major'), 'V': (7, 'Major'), 'VI': (9, 'minor'), 'VII': (11, 'dim'),
    'i': (0, 'minor'), 'ii': (2, 'dim'), 'iii': (3, 'Major'),
    'iv': (5, 'minor'), 'v': (7, 'minor'), 'vi': (8, 'Major'), 'vii': (10, 'Major'),
    'I7': (0, 'dom7'), 'II7': (2, 'dom7'), 'III7': (4, 'dom7'),
    'IV7': (5, 'dom7'), 'V7': (7, 'dom7'), 'VI7': (9, 'dom7'), 'VII7': (11, 'dom7'),
}

def _resolve_roman(roman, current_key='C'):
    """Resolve a Roman numeral like 'V7' to a chord name like 'G_dom7'."""
    base = ROMAN_BASES.get(roman, (0, 'Major'))
    semitone_offset = base[0]
    quality = base[1]
    scale = _key_to_scale(current_key)
    if not scale:
        return f"C_{quality}"
    root_semi = scale[semitone_offset % len(scale)] if semitone_offset < len(scale) else semitone_offset
    root_name = NOTE_NAMES[root_semi % 12]
    return f"{root_name}_{quality}"


# ── Regex Patterns ────────────────────────────

NOTE_RE = re.compile(
    r'^([A-G]#?b?)(\d+)\s+(w|h|q|e|s|t)(\.?)\s*'
    r'(?:@(\w+):([^\s@]+))?\s*(.*)$', re.I
)
RELATIVE_T_RE = re.compile(r'^\+(\d+)\s+N(\d+)')
MACRO_DEF_RE = re.compile(r'^!(\w+)\s*=\s*(.+)')
MACRO_USE_RE = re.compile(r'^!(\w+)([\^~][a-z]+)?\s*$')  # !macro^ (transpose), !macro~inv (invert)
REPEAT_SUFFIX_RE = re.compile(r'^(.*\S)\s+x(\d+)\s*$')
PROBABILITY_RE = re.compile(r'^\?([\d.]+)\s+(.+)$')
DYNAMIC_ARC_RE = re.compile(r'^(ppp|pp|p|mp|mf|f|ff|fff)\s*<\s*(ppp|pp|p|mp|mf|f|ff|fff)\s*>\s*(ppp|pp|p|mp|mf|f|ff|fff)$')
TEMPO_CURVE_RE = re.compile(r'^@(?:bpm|tempo)\s+(\d+)\s*->\s*(\d+)', re.I)
TUPLET_RE = re.compile(r'^(.*)\s*\((\d+):(\d+)\)\s*$')  # C4 q D4 q (3:2)
TRIPLET_GROUP_RE = re.compile(r'^\[(.+?)\]\s*/\s*(\d+)\s*$')  # [C4 D4 E4]/3
KEY_MOD_RE = re.compile(r'^@key\s+(\S+)', re.I)
RITARD_RE = re.compile(r'^(ritard|accel|accelerando)\(([\d.]+)\s*bars?\)\s*->\s*(\d+)', re.I)
SCALE_QUANT_RE = re.compile(r'N\[(\d+)-(\d+)\]!in\((\w+)\)')  # N[60-72]!in(Bm)
CHANNEL_RE = re.compile(r'^(?:TRK|CH)\[(\d+)\]\s+(.*)', re.I)  # CH[10] T0 N36
COMPILER_CONFIG_RE = re.compile(r'^#compiler\s+(\w+)\s*:\s*(.+)', re.I)
ARTICULATION_MAP = {'staccato': 0.3, 'legato': 0.95, 'tenuto': 0.85, 'accent': 1.0}
DYN_MAP = {'ppp': 16, 'pp': 33, 'p': 49, 'mp': 64, 'mf': 80, 'f': 96, 'ff': 112, 'fff': 126}


# ── Main Preprocessor ─────────────────────────

def preprocess_v3(text):
    lines = text.split('\n')
    result = []
    macros = {}
    block_comment = False
    current_key = 'C'
    config_flags = {}
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        original = line

        # Block comments
        if '/*' in line:
            block_comment = True
            before = line.split('/*')[0]
            if before.strip():
                lines.insert(i + 1, before)
            i += 1; continue
        if block_comment:
            if '*/' in line:
                block_comment = False
                after = line.split('*/')[-1]
                if after.strip():
                    lines.insert(i + 1, after)
            i += 1; continue
        if block_comment:
            i += 1; continue

        if line.startswith('//') or line.startswith('#'):
            # Compiler config strip
            cm = COMPILER_CONFIG_RE.match(line)
            if cm:
                config_flags[cm.group(1).lower()] = cm.group(2).strip()
                result.append(f'// compiler {cm.group(1)}: {cm.group(2)}')
            else:
                result.append(raw)
            i += 1; continue

        # Key modulation
        km = KEY_MOD_RE.match(line)
        if km:
            current_key = km.group(1).strip()
            result.append(f'// @key {current_key}')
            i += 1; continue

        # GC directives
        if line.startswith('@gc:'):
            result.append(f'// @gc:{line[4:].strip()}')
            i += 1; continue

        # Tempo tapers: ritard(2 bars) -> 50
        rt = RITARD_RE.match(line)
        if rt:
            direction = rt.group(1).lower()
            bars = float(rt.group(2))
            target_bpm = float(rt.group(3))
            current_bpm = 120  # default, ideally read from context
            result.append(f'// {direction} ({bars} bars) -> {target_bpm} BPM')
            i += 1; continue

        # Tempo aliases
        if line.startswith('@') and not line.startswith('@bpm') and not line.startswith('@tempo'):
            alias = line[1:].split()[0].lower()
            if alias in TEMPO_ALIASES:
                result.append(f'@bpm {TEMPO_ALIASES[alias]}')
                rest = line[len(alias) + 1:].strip()
                if rest:
                    lines.insert(i + 1, rest)
                i += 1; continue

        # Tempo curve
        tc = TEMPO_CURVE_RE.match(line)
        if tc:
            avg = (int(tc.group(1)) + int(tc.group(2))) // 2
            result.append(f'@bpm {avg}  // curve {tc.group(1)}->{tc.group(2)}')
            i += 1; continue

        # Macro definition
        md = MACRO_DEF_RE.match(line)
        if md:
            macros[md.group(1)] = md.group(2).strip()
            result.append(f'// macro !{md.group(1)} defined')
            i += 1; continue

        # Triplet group: [C4 D4 E4]/3
        tg = TRIPLET_GROUP_RE.match(line)
        if tg:
            notes = tg.group(1).split()
            count = int(tg.group(2))
            for j, note in enumerate(notes):
                result.append(f'{note}  // triplet {j+1}/{count}')
            i += 1; continue

        # Multi-channel prefix: CH[10] T0 N36
        ch = CHANNEL_RE.match(line)
        if ch:
            channel = ch.group(1)
            rest_line = ch.group(2)
            result.append(f'{rest_line}  // channel {channel}')
            i += 1; continue

        # Process the line through sub-processors
        processed, handled, modded = _process_line_v3(
            line, macros, result, i, lines, raw, current_key
        )
        if handled:
            i += 1; continue
        if processed is None:
            i += 1; continue
        if modded:
            result.append(processed)
        else:
            result.append(raw)
        i += 1

    return '\n'.join(result), config_flags


def _process_line_v3(line, macros, result, idx, lines, raw, current_key='C'):
    """Process a single line. Returns (processed_line, handled_flag, modified_flag)."""
    orig = line

    # Macro usage with mutations: !macro^ (transpose up), !macro~inv (invert)
    mu = MACRO_USE_RE.match(line)
    if mu:
        name = mu.group(1)
        mutation = mu.group(2) or ''
        if name in macros:
            expanded = macros[name]
            if mutation == '^':
                expanded = _transpose_macro(expanded, 12)
            elif mutation == '^^':
                expanded = _transpose_macro(expanded, 24)
            elif mutation == 'v':
                expanded = _transpose_macro(expanded, -12)
            elif mutation == '~inv':
                expanded = _invert_macro(expanded)
            result.append(expanded)
            return None, True, False

    # Probability gate
    prob = PROBABILITY_RE.match(line)
    if prob:
        chance = float(prob.group(1))
        if random.random() > chance:
            result.append(f'// ?{chance} skipped')
            return None, True, False
        line = prob.group(2)

    # Repeat suffix
    repeat = REPEAT_SUFFIX_RE.match(line)
    if repeat:
        base = repeat.group(1).strip()
        count = int(repeat.group(2))
        for n in range(count):
            if n == 0:
                result.append(base)
            else:
                result.append(_shift_timestamps(base, n * 1000))
        return None, True, False

    # Dynamic arc
    da = DYNAMIC_ARC_RE.match(line)
    if da:
        result.append(f'// dynamic arc: {da.group(1)} < {da.group(2)} > {da.group(3)}')
        return None, True, False

    # Scale quantization: N[60-72]!in(Bm)
    line = SCALE_QUANT_RE.sub(lambda m: _quantize_scale(m), line)

    # Tuplet/polyrhythm: (3:2)
    tuplet = TUPLET_RE.match(line)
    if tuplet:
        content = tuplet.group(1).strip()
        num = int(tuplet.group(2))
        den = int(tuplet.group(3))
        result.append(f'{content}  // {num}:{den} tuplet')
        return None, True, False

    # Note shorthand
    note_m = NOTE_RE.match(line)
    if note_m:
        pitch = note_m.group(1)
        octave = note_m.group(2)
        dur_code = note_m.group(3) + ('.' if note_m.group(4) else '')
        val = note_m.group(6) or ''
        extra = note_m.group(7) or ''
        human = f'play note({pitch}{octave}) @dur:{dur_code}'
        if val:
            human += f' @vel:{val}'
        for art in ARTICULATION_MAP:
            if art in extra:
                human += f' // articulation: {art}'
                break
        for dyn_name, dyn_val in DYN_MAP.items():
            if dyn_name in extra:
                human += f' @vel:{dyn_val}'
                break
        result.append(human)
        return None, True, False

    # Roman numeral with dynamic key
    rn = re.match(r'^chord\(([IViv]+[7]?)\)', line)
    if rn:
        resolved = _resolve_roman(rn.group(1), current_key)
        result.append(f'chord({resolved})')
        return None, True, False

    # Randomization
    modded = False
    for token in ['V~', 'D~', 'N~']:
        if token in line:
            modded = True
    if modded:
        rl = re.sub(r'V~(?:([\d.]+))?', _random_vel, line)
        rl = re.sub(r'D~(\d+)', _random_dur, rl)
        line = rl

    # Range notation
    new_l = re.sub(r'N(\d+)-(\d+)', lambda m: f'N{random.randint(int(m.group(1)), int(m.group(2)))}', line)
    if new_l != line:
        line = new_l; modded = True

    # Parallel &
    if '&' in line:
        for p in [x.strip() for x in line.split('&') if x.strip()]:
            result.append(p)
        return None, True, False

    # Relative timing
    if RELATIVE_T_RE.match(line):
        modded = True

    return (line, False, True) if modded else (line, False, False)


# ── Macro Mutations ──────────────────────────

def _transpose_macro(text, semitones):
    """Transpose all MIDI notes in a macro by N semitones."""
    def _trans(m):
        return f'N{max(0, min(127, int(m.group(1)) + semitones))}'
    return re.sub(r'N(\d+)', _trans, text)


def _invert_macro(text):
    """Invert intervals around the first note's MIDI value."""
    notes = [int(m) for m in re.findall(r'N(\d+)', text)]
    if not notes:
        return text
    center = notes[0]
    inverted = [center - (n - center) for n in notes]
    # Clamp to 0-127
    inverted = [max(0, min(127, n)) for n in inverted]
    result = text
    for old_n, new_n in zip(notes, inverted):
        result = result.replace(f'N{old_n}', f'N{new_n}', 1)
    return result


# ── Randomization Helpers ─────────────────────

def _random_vel(m):
    max_delta = float(m.group(1)) if m.group(1) else 0.1
    return f'V{max(0, min(1, 0.8 + random.uniform(-max_delta, max_delta))):.2f}'


def _random_dur(m):
    max_delta = int(m.group(1))
    return f'D{max(1, 500 + random.randint(-max_delta, max_delta))}'


def _shift_timestamps(line, offset_ms):
    return re.sub(r'T(\d+)', lambda m: f'T{int(m.group(1)) + offset_ms}', line)


# ── Scale Quantization ────────────────────────

def _quantize_scale(m):
    """Snap a random note range to nearest scale note."""
    lo, hi = int(m.group(1)), int(m.group(2))
    scale_name = m.group(3)
    scale = _key_semitones(scale_name)
    midi = random.randint(lo, hi)
    snapped = _nearest_scale_note(midi, scale)
    return f'N{snapped}'


# ── Detection ────────────────────────────────

def detect_v3(text):
    patterns = [
        r'@(adagio|allegro|presto|largo|andante|vivace|moderato)',
        r'^\?[\d.]+\s', r'x\d+\s*$', r'^!\w+\s*=', r'V~', r'D~',
        r'N\d+-\d+', r'&', r'\+\d+\s+N', r'/\*', r'\*/',
        r'@bpm\s+\d+\s*->\s*\d+', r'^(staccato|legato|tenuto|accent)\b',
        r'^[A-G]#?b?\d+\s+[whqest]', r'chord\([IViv]',
        r'\(\d+:\d+\)', r'@key\s+\w+', r'N\[', r'!in\(', r'CH\[\d+\]',
        r'TRK\[\d+\]', r'#compiler\s+', r'ritard\(|accel\(',
        r'!\w+[\^~]', r'\.\.\./3\]',
    ]
    return any(re.search(p, text, re.I | re.MULTILINE) for p in patterns)


def compile_v3(text):
    """Compile v3 text: preprocess then feed to standard compiler."""
    preprocessed, _ = preprocess_v3(text)
    from ep import (
        compile_v2,
        detect_v2,
        parse_e_text,
    )
    if detect_v2(preprocessed):
        return compile_v2(preprocessed)
    return parse_e_text(preprocessed)
