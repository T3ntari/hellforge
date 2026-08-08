"""v3 Extended Syntax preprocessor: shorthand, macros, probability, repeat, relative timing, block comments."""

import re
import random

NOTE_RE = re.compile(
    r'^([A-G]#?b?)(\d+)\s+(w|h|q|e|s|t)(\.?)\s*(?:@(\w+):([^\s@]+))?\s*(.*)$', re.I
)
MACRO_DEF_RE = re.compile(r'^!(\w+)\s*=\s*(.+)')
MACRO_USE_RE = re.compile(r'^!(\w+)\s*$')
REPEAT_RE = re.compile(r'^(.*\S)\s+x(\d+)\s*$')
PROB_RE = re.compile(r'^\?([\d.]+)\s+(.+)$')
REL_T_RE = re.compile(r'^\+(\d+)\s+N(\d+)')
PARALLEL_RE = re.compile(r'&')
DYN_ARC_RE = re.compile(r'^(ppp|pp|p|mp|mf|f|ff|fff)\s*<\s*(ppp|pp|p|mp|mf|f|ff|fff)\s*>\s*(ppp|pp|p|mp|mf|f|ff|fff)$')
ROMAN_RE = re.compile(r'^chord\(([IViv]+[7]?)\)')
RAND_V_RE = re.compile(r'V~([\d.]*)')
RAND_D_RE = re.compile(r'D~(\d+)')
RANGE_RE = re.compile(r'N(\d+)-(\d+)')

DYN_MAP = {'ppp':16,'pp':33,'p':49,'mp':64,'mf':80,'f':96,'ff':112,'fff':126}

# ── Key-Aware Roman Numeral Resolver ─────────

# Scale semitone patterns per quality
SCALE_PATTERNS = {
    'Major': [0, 2, 4, 5, 7, 9, 11],
    'minor': [0, 2, 3, 5, 7, 8, 10],
}

# Roman numeral → scale degree index (0-based) + quality
ROMAN_DEGREES = {
    'I': (0, 'Major'), 'II': (1, 'minor'), 'III': (2, 'minor'),
    'IV': (3, 'Major'), 'V': (4, 'Major'), 'VI': (5, 'minor'), 'VII': (6, 'dim'),
    'i': (0, 'minor'), 'ii': (1, 'dim'), 'iii': (2, 'Major'),
    'iv': (3, 'minor'), 'v': (4, 'minor'), 'vi': (5, 'Major'), 'vii': (6, 'Major'),
    'I7': (0, 'dom7'), 'II7': (1, 'dom7'), 'III7': (2, 'dom7'),
    'IV7': (3, 'dom7'), 'V7': (4, 'dom7'), 'VI7': (5, 'dom7'), 'VII7': (6, 'dim7'),
}

# Root semitone for each key
KEY_ROOTS = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11,
}

NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']

# Chord quality → semitone intervals
QUALITY_INTERVALS = {
    'Major': [0, 4, 7], 'minor': [0, 3, 7], 'dim': [0, 3, 6],
    'dom7': [0, 4, 7, 10], 'dim7': [0, 3, 6, 9],
}

_current_key = 'C_Major'  # mutable state—updated by @key directive


def set_key(key_name):
    """Set current key from a name like 'Am', 'G_Major', 'C#_minor'."""
    global _current_key
    # Parse "Am" → root=A, quality=minor
    m = re.match(r'([A-G]#?b?)\s*(Major|minor|Maj|Min)?', key_name.strip(), re.I)
    if m:
        root = m.group(1).capitalize()
        qual = (m.group(2) or 'Major').lower()
        if qual.startswith('maj'): qual = 'Major'
        elif qual.startswith('min'): qual = 'minor'
        else: qual = 'Major'
        _current_key = f"{root}_{qual}"
    return _current_key


def resolve_roman(roman_numeral):
    """Resolve a Roman numeral chord to a chord name in the current key.
    e.g., chord(I) in key of Am → A_minor. chord(V7) in key of G → D_dom7."""
    if roman_numeral not in ROMAN_DEGREES:
        return 'C_Major'
    degree, quality = ROMAN_DEGREES[roman_numeral]

    # Parse current key
    km = re.match(r'([A-G]#?b?)_(Major|minor)', _current_key)
    if not km:
        return 'C_Major'
    root_semi = KEY_ROOTS.get(km.group(1), 0)
    key_type = km.group(2)

    # Get scale pattern for current key
    scale = SCALE_PATTERNS.get(key_type, SCALE_PATTERNS['Major'])

    # Root of the chord = scale[degree] semitones above key root
    chord_root_semi = (root_semi + scale[degree]) % 12
    chord_root_name = NOTE_NAMES[chord_root_semi]

    # Determine chord quality
    actual_quality = quality
    if quality == 'dim':
        actual_quality = 'dim'
    elif quality == 'dim7':
        actual_quality = 'dim7'
    elif quality == 'dom7':
        actual_quality = 'dom7'

    return f"{chord_root_name}_{actual_quality}"


# Also update the preprocessor to use resolve_roman
def preprocess_v3(text):
    """Preprocess v3 text into normalized v1/v2 text."""
    global _current_key
    macros = {}
    result = []
    block_comment = False

    # Reset key at start
    _current_key = 'C_Major'


def preprocess_v3(text):
    """Preprocess v3 text into normalized v1/v2 text."""
    macros = {}
    result = []
    block_comment = False

    for raw_line in text.split('\n'):
        line = raw_line.strip()

        if line.startswith('//') or line.startswith('#'):
            result.append(raw_line)
            continue

        # Block comments
        if '/*' in line:
            before = line.split('/*')[0]
            if before.strip(): result.append(before)
            block_comment = True
            if '*/' in line:
                after = line.split('*/')[-1]
                if after.strip(): result.append(after)
                block_comment = False
            continue
        if block_comment:
            if '*/' in line:
                after = line.split('*/')[-1]
                if after.strip(): result.append(after)
                block_comment = False
            continue

        # Macro definition
        md = MACRO_DEF_RE.match(line)
        if md:
            macros[md.group(1)] = md.group(2).strip()
            result.append(f'// macro !{md.group(1)}')
            continue

        # Macro usage
        mu = MACRO_USE_RE.match(line)
        if mu and mu.group(1) in macros:
            result.append(macros[mu.group(1)])
            continue

        # Probability gate
        prob = PROB_RE.match(line)
        if prob:
            if random.random() <= float(prob.group(1)):
                result.append(prob.group(2))
            else:
                result.append(f'// skipped ?{prob.group(1)}')
            continue

        # Repeat suffix
        rep = REPEAT_RE.match(line)
        if rep:
            base, count = rep.group(1).strip(), int(rep.group(2))
            mu = MACRO_USE_RE.match(base)
            if mu and mu.group(1) in macros:
                base = macros[mu.group(1)]
            for n in range(count):
                s = re.sub(r'T(\d+)', lambda m: f'T{int(m.group(1)) + n * 1000}', base) if n > 0 else base
                result.append(s)
            continue

        # Dynamic arc
        da = DYN_ARC_RE.match(line)
        if da:
            result.append(f'// dynamic: {da.group(1)} < {da.group(2)} > {da.group(3)}')
            continue

        # @key directive — update current key
        if line.startswith('@key'):
            key_name = line[4:].strip()
            set_key(key_name)
            result.append(raw_line)
            continue

        # Roman numeral — resolve in current key
        rn = ROMAN_RE.match(line)
        if rn:
            chord_name = resolve_roman(rn.group(1))
            result.append(f'chord({chord_name})')
            continue

        # Note shorthand: C4 q
        nm = NOTE_RE.match(line)
        if nm:
            pitch, octave, dur = nm.group(1), nm.group(2), nm.group(3) + ('.' if nm.group(4) else '')
            extra = nm.group(7) or ''
            human = f'play note({pitch}{octave}) @dur:{dur}'
            for dyn_name, dyn_val in DYN_MAP.items():
                if dyn_name in extra:
                    human += f' @vel:{dyn_val}'
                    break
            # Preserve @time: from shorthand if present
            time_m = re.search(r'@time:(\S+)', extra)
            if time_m:
                human += f' @time:{time_m.group(1)}'
            result.append(human)
            continue

        # Randomization
        line = RAND_V_RE.sub(lambda m: f'V{max(0,min(1,0.8+random.uniform(-float(m.group(1)or 0.1),float(m.group(1)or 0.1)))):.2f}', line)
        line = RAND_D_RE.sub(lambda m: f'D{max(1,500+random.randint(-int(m.group(1)),int(m.group(1))))}', line)

        # Range notation
        line = RANGE_RE.sub(lambda m: f'N{random.randint(int(m.group(1)),int(m.group(2)))}', line)

        # Parallel &
        if '&' in line:
            for p in line.split('&'):
                p = p.strip()
                if p: result.append(p)
            continue

        result.append(raw_line)

    return '\n'.join(result)


def detect_v3(text):
    """Detect v3 features."""
    patterns = [r'@(adagio|allegro|presto|largo)', r'^!\w+\s*=', r'\?\d+\.\d+\s+T',
                r'V~', r'D~', r'N\d+-\d+', r'&', r'^[A-G]#?b?\d+\s+[whqest]']
    for p in patterns:
        if re.search(p, text, re.I | re.MULTILINE):
            return True
    return False
