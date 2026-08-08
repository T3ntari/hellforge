"""Global directives parser: @bpm, @vol, @gc, @key, tempo aliases, config strips."""

import re

# Tempo aliases
TEMPO_ALIASES = {
    'larghissimo': 20, 'grave': 40, 'largo': 50, 'lento': 55,
    'adagio': 56, 'adagietto': 65, 'andante': 76,
    'andantino': 85, 'moderato': 100, 'allegretto': 110,
    'allegro': 120, 'vivace': 140, 'presto': 180, 'prestissimo': 210,
}

# Default state
DEFAULT_LL_STATE = {
    'sr': 44100, 'bit': 16, 'quality': 'standard',
    'filter_cutoff': None, 'filter_res': None, 'filter_type': None,
    'env_attack': None, 'env_release': None, 'env_sustain': None,
    'phase': None, 'cents': None, 'swing': None,
    'sub': None, 'bass_boost': None,
    'stereo_width': 100, 'neural': False,
    'master_vol': None, 'gain_db': None,
    'mem': None,
    'seed': None,
    'key': None, 'scale': None, 'gc_strategy': 'off',
}

# Key signature → semitone map for roman numeral chords
KEY_MAP = {
    'C': 0, 'G': 7, 'D': 2, 'A': 9, 'E': 4, 'B': 11, 'F#': 6,
    'F': 5, 'Bb': 10, 'Eb': 3, 'Ab': 8, 'Db': 1, 'Gb': 6,
}

KEY_SCALES = {
    'C_Major': [0,2,4,5,7,9,11], 'C_minor': [0,2,3,5,7,8,10],
    'G_Major': [7,9,11,0,2,4,6], 'G_minor': [7,9,10,0,2,3,5],
    'D_Major': [2,4,6,7,9,11,1], 'D_minor': [2,4,5,7,9,10,0],
    'A_Major': [9,11,1,2,4,6,8], 'A_minor': [9,11,0,2,4,5,7],
    'E_Major': [4,6,8,9,11,1,3], 'E_minor': [4,6,7,9,11,0,2],
    'F_Major': [5,7,9,10,0,2,4], 'F_minor': [5,7,8,10,0,1,3],
}


def _mem_events(m):
    """Convert @mem value + suffix to an event-count budget.
    64K/64M/64G suffixes scale the raw number; plain numbers are event counts.
    Returns int budget or None."""
    try:
        n = float(m.group(1))
    except (ValueError, TypeError):
        return None
    suffix = (m.group(2) or "").lower()
    if suffix == "k":
        return max(1, int(n * 1000))
    if suffix == "m":
        return max(1, int(n * 1_000_000))
    if suffix == "g":
        return max(1, int(n * 1_000_000_000))
    return max(1, int(n))


def parse_key_directive(text, current_key=None):
    """Parse @key directive. Returns (root_semi, scale_type) or current key."""
    m = re.search(r'@key\s+(\w+)\s*(major|minor|Maj|Min)?', text, re.I)
    if not m:
        return current_key
    root_name = m.group(1).capitalize()
    typ = (m.group(2) or 'major').lower()
    if typ.startswith('maj'): typ = 'Major'
    elif typ.startswith('min'): typ = 'minor'
    else: typ = 'Major' if root_name in ('C','G','D','A','E','F','B') else 'minor'
    key_name = f"{root_name}_{typ}"
    return KEY_SCALES.get(key_name, current_key)


def parse_config_strip(text):
    """Parse #compiler directives from file header."""
    config = {}
    for m in re.finditer(r'#compiler\s+(\w+)\s*:\s*(.+)', text, re.I):
        config[m.group(1).lower()] = m.group(2).strip()
    return config


def parse_directives(text, state=None):
    """Parse all directives from text, updating state dict. Returns updated state."""
    if state is None:
        state = dict(DEFAULT_LL_STATE)

    patterns = {
        r'@(?:bpm|tempo)\s+(\d+(?:\.\d+)?)': lambda m: state.update({'bpm': float(m.group(1))}),
        r'@vol(?:ume)?\s*:\s*([\d.]+)': lambda m: state.update({'master_vol': float(m.group(1))}),
        r'@master\s*:\s*([\d.]+)': lambda m: state.update({'master_vol': float(m.group(1))}),
        r'@gain\s*:\s*([-+\d.]+)db?': lambda m: state.update({'gain_db': float(m.group(1))}),
        r'@sr\s*:\s*(\d+)': lambda m: state.update({'sr': int(m.group(1))}),
        r'@bit\s*:\s*(\d+)': lambda m: state.update({'bit': int(m.group(1))}),
        r'@quality\s*:\s*(\w+)': lambda m: state.update({'quality': m.group(1)}),
        r'@sub\s*:\s*([\d.]+)hz?': lambda m: state.update({'sub': float(m.group(1))}),
        r'@bass_boost\s*:\s*([-+\d.]+)db?': lambda m: state.update({'bass_boost': float(m.group(1))}),
        r'@stereo_width\s*:\s*(\d+)': lambda m: state.update({'stereo_width': max(0, min(200, int(m.group(1))))}),
        r'@neural\s+(on|off|true|false)': lambda m: state.update({'neural': m.group(1).lower() in ('on', 'true')}),
        r'@mem\s*:\s*(\d+)(k|m|g)?': lambda m: state.update({'mem': _mem_events(m)}),
        r'@mem\s+(\d+)(k|m|g)?': lambda m: state.update({'mem': _mem_events(m)}),
        r'@seed\s*:?\s*(\d+)': lambda m: state.update({'seed': int(m.group(1))}),
        r'@gc\s*:\s*(\w+)': lambda m: state.update({'gc_strategy': m.group(1)}),
        r'@scale\s+(\w+(?:_(?:Major|minor))?)': lambda m: state.update({'scale': m.group(1)}),
        r'@scale\s+off': lambda m: state.update({'scale': None}),
        r'@key\s+(\w[\w#]*)': lambda m: state.update({'key': parse_key_directive(f"@key {m.group(1)}")}),
        r'@oct\s*:\s*([+-]?\d+)': lambda m: state.update({'octave': int(m.group(1))}),
        r'@pedal\s*:\s*(\d+)': lambda m: state.update({'sustain_state': max(0, min(127, int(m.group(1))))}),
        r'@sustain\s*:\s*(\d+)': lambda m: state.update({'sustain_state': max(0, min(127, int(m.group(1))))}),
    }

    for line in text.split('\n'):
        line = line.strip()
        if not line or line.startswith('//') or line.startswith('#'):
            continue
        # Tempo aliases
        if line.startswith('@') and not line.startswith('@bpm') and not line.startswith('@tempo'):
            alias = line[1:].split()[0].lower()
            if alias in TEMPO_ALIASES:
                state['bpm'] = TEMPO_ALIASES[alias]
                continue
        for pattern, handler in patterns.items():
            m = re.match(pattern, line, re.I)
            if m:
                handler(m)
                break
        else:
            # Try plugin-registered directives
            try:
                from ep_core import _plugin_directives
                for pattern, handler in _plugin_directives.items():
                    m = re.match(pattern, line, re.I)
                    if m:
                        handler(m, state)
                        break
            except ImportError:
                pass

    return state
