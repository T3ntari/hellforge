"""
E Language v2 Compiler — Semantic Syntax to Events.

Translates v2 syntax (chord names, scale degrees, relative timing, blocks)
into flat events (timestamp, midi, duration, velocity).

v2 syntax:
  [Section: name]           Section header
  Key: C_Minor              Key signature
  Tempo: 120                BPM
  Time: 4/4                 Time signature
  {Chord_Block: 4_bars}     Chord progression block
    C_Major | G_Major       Chords separated by |
  play(root, dur=quarter)   Play scale degree
  arpeggio(up, dur=16th)    Arpeggio pattern
  chromatic_run(up, 2_oct)  Chromatic run
  pattern(waltz)            Rhythm pattern
"""

import re
import math

CHORD_INTERVALS = {
    'major':      [0, 4, 7],
    'minor':      [0, 3, 7],
    'dim':        [0, 3, 6],
    'aug':        [0, 4, 8],
    'dom7':       [0, 4, 7, 10],
    'maj7':       [0, 4, 7, 11],
    'min7':       [0, 3, 7, 10],
    'dim7':       [0, 3, 6, 9],
    'm7b5':       [0, 3, 6, 10],
    'sus2':       [0, 2, 7],
    'sus4':       [0, 5, 7],
    'dom9':       [0, 4, 7, 10, 14],
    'maj9':       [0, 4, 7, 11, 14],
    'min9':       [0, 3, 7, 10, 14],
    'aug7':       [0, 4, 8, 10],
    'dim7':       [0, 3, 6, 9],
    'm_maj7':     [0, 3, 7, 11],
}

QUALITY_ALIASES = {
    'M': 'major', 'maj': 'major', 'major': 'major',
    'm': 'minor', 'min': 'minor', 'minor': 'minor',
    'dim': 'dim', 'o': 'dim',
    'aug': 'aug', '+': 'aug',
    '7': 'dom7', 'dom7': 'dom7',
    'maj7': 'maj7', 'M7': 'maj7',
    'min7': 'min7', 'm7': 'min7',
    'dim7': 'dim7',
    'm7b5': 'm7b5',
    'sus2': 'sus2', 'sus4': 'sus4',
    '9': 'dom9', 'dom9': 'dom9',
    'maj9': 'maj9', 'min9': 'min9',
}

NOTE_TO_SEMI = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
    'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
    'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
}

SEMI_TO_NOTE = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

DUR_BEATS = {
    'whole': 4, 'w': 4,
    'half': 2, 'h': 2,
    'quarter': 1, 'q': 1,
    'eighth': 0.5, 'e': 0.5, '8th': 0.5,
    'sixteenth': 0.25, 's': 0.25, '16th': 0.25,
    'thirtysecond': 0.125, 't': 0.125, '32nd': 0.125,
    'sixtyfourth': 0.0625,
    'dotted_whole': 6,
    'dotted_half': 3, 'h.': 3,
    'dotted_quarter': 1.5, 'q.': 1.5,
    'dotted_eighth': 0.75, 'e.': 0.75,
    'triplet_quarter': 2/3,
    'triplet_eighth': 1/3,
    'triplet_sixteenth': 1/6,
}

DYNAMICS = {
    'ppp': 16, 'pp': 33, 'p': 49, 'mp': 64,
    'mf': 80, 'm': 90, 'f': 96, 'ff': 112, 'fff': 126,
    'soft': 49, 'normal': 80, 'loud': 112, 'max': 127, 'silent': 0,
}

KEYS = {
    'C_Major':     [0, 2, 4, 5, 7, 9, 11],
    'G_Major':     [0, 2, 4, 5, 7, 9, 11],
    'D_Major':     [0, 2, 4, 5, 7, 9, 11],
    'A_Major':     [0, 2, 4, 5, 7, 9, 11],
    'E_Major':     [0, 2, 4, 5, 7, 9, 11],
    'F_Major':     [0, 2, 4, 5, 7, 9, 11],
    'Bb_Major':    [0, 2, 4, 5, 7, 9, 11],
    'C_Minor':     [0, 2, 3, 5, 7, 8, 10],
    'A_minor':     [0, 2, 3, 5, 7, 8, 10],
    'E_minor':     [0, 2, 3, 5, 7, 8, 10],
    'D_minor':     [0, 2, 3, 5, 7, 8, 10],
    'G_minor':     [0, 2, 3, 5, 7, 8, 10],
    'C#_minor':    [0, 2, 3, 5, 7, 8, 10],
    'F#_minor':    [0, 2, 3, 5, 7, 8, 10],
}


def parse_chord_name(name):
    """Parse 'C#_minor' or 'G_dom7' or 'Bb_Major' into (root_note, quality)."""
    name = name.strip()
    # Handle formats like C#_minor, C_Major, G_dom7, A_min7
    parts = name.split('_', 1)
    if len(parts) == 2:
        note_str = parts[0]
        quality = parts[1].lower()
    else:
        # No underscore — try to parse like "C#m" or "G7"
        m = re.match(r'([A-G]#?b?)(.*)', name)
        if m:
            note_str = m.group(1)
            rest = m.group(2).lower()
            quality = QUALITY_ALIASES.get(rest, rest or 'major')
        else:
            return None, None

    # Normalize note
    if 'b' in note_str and '#' not in note_str:
        # Convert flats to sharps for lookup
        flat_map = {'Db': 'C#', 'Eb': 'D#', 'Gb': 'F#', 'Ab': 'G#', 'Bb': 'A#'}
        note_str = flat_map.get(note_str, note_str)

    quality = QUALITY_ALIASES.get(quality, quality)
    return note_str, quality


def chord_to_semitones(root_semi, quality):
    """Get MIDI note numbers for a chord quality starting from root."""
    intervals = CHORD_INTERVALS.get(quality, [0, 4, 7])
    return [root_semi + i for i in intervals]


def semi_to_midi(semi, octave=4):
    """Convert semitone + octave to MIDI number."""
    return semi + (octave + 1) * 12


def midi_from_note(note_str, octave=4):
    """Get MIDI from note name like 'C#' or 'Bb'."""
    semi = NOTE_TO_SEMI.get(note_str)
    if semi is None:
        return None
    return semi + (octave + 1) * 12


def parse_dur(dur_str):
    """Parse duration string to beats. 'quarter' -> 1, '16th' -> 0.25"""
    if not dur_str:
        return 1.0
    d = dur_str.lower().strip()
    if d in DUR_BEATS:
        return DUR_BEATS[d]
    # Try numeric
    try:
        return float(d)
    except ValueError:
        return 1.0


def parse_vel(vel_str):
    """Parse velocity string to 0-127."""
    if not vel_str:
        return 80
    v = vel_str.lower().strip()
    if v in DYNAMICS:
        return DYNAMICS[v]
    try:
        val = float(v)
        if val <= 1.0:
            return int(val * 127)
        return max(0, min(127, int(val)))
    except ValueError:
        return 80


class V2Compiler:
    def __init__(self):
        self.events = []
        self.current_section = None
        self.key = 'A_minor'
        self.tempo = 120
        self.time_sig = (4, 4)
        self.beat_ms = 500  # 60000 / 120
        self.current_chord = None  # (root_semi, quality)
        self.current_chord_midis = []
        self.cursor = 0  # current time in ms
        self.default_vel = 80
        self.default_dur = 'quarter'
        self.octave = 4
        self._dyn_remaining = 0   # notes left in active dynamics arc
        self._dyn_total = 0
        self._dyn_from = 0
        self._dyn_target = 0
        self._dyn_step = 0.0

    def set_tempo(self, bpm):
        self.tempo = float(bpm)
        self.beat_ms = 60000.0 / self.tempo

    def _vel_for_note(self):
        """Velocity for the next emitted note, advancing the active dynamics arc."""
        if self._dyn_remaining > 0:
            self._dyn_remaining -= 1
            if self._dyn_remaining == 0:
                self.default_vel = self._dyn_target
            else:
                self.default_vel = round(self._dyn_from + self._dyn_step * (self._dyn_total - self._dyn_remaining))
        return self.default_vel

    def beats_to_ms(self, beats):
        return beats * self.beat_ms

    def _set_chord(self, chord_name):
        """Set current chord from a name like 'C_Major' or 'A_minor'."""
        note_str, quality = parse_chord_name(chord_name)
        if note_str:
            root_semi = NOTE_TO_SEMI.get(note_str, 0)
            self.current_chord = (root_semi, quality)
            self.current_chord_midis = chord_to_semitones(root_semi, quality)

    def parse(self, text):
        """Parse v2 syntax text into events."""
        lines = text.split('\n')
        i = 0
        chord_block_active = False
        current_chords = []
        block_chord_idx = 0
        block_bars = 0

        while i < len(lines):
            line = lines[i].strip()
            i += 1

            if not line or line.startswith('//') or line.startswith('#'):
                continue

            # Section header
            sm = re.match(r'\[Section:\s*(.+?)\]', line, re.I)
            if sm:
                self.current_section = sm.group(1).strip()
                continue

            # Section close / block end
            if re.match(r'\{?\s*End\s*\}?\s*$', line, re.I):
                if chord_block_active and current_chords:
                    # Set first chord for subsequent melody blocks
                    self._set_chord(current_chords[0])
                chord_block_active = False
                current_chords = []
                continue

            # Key directive
            km = re.match(r'Key:\s*(\S+)', line, re.I)
            if km:
                self.key = km.group(1).strip()
                continue

            # Tempo directive
            tm = re.match(r'Tempo:\s*([\d.]+)', line, re.I)
            if tm:
                self.set_tempo(tm.group(1))
                continue

            # Time directive
            tim = re.match(r'Time:\s*(\d+)/(\d+)', line, re.I)
            if tim:
                self.time_sig = (int(tim.group(1)), int(tim.group(2)))
                continue

            # Chord block start
            cm = re.match(r'\{Chord_Block:\s*([\d.]+)[\s_]*bars?\}', line, re.I)
            if cm:
                chord_block_active = True
                block_bars = float(cm.group(1))
                current_chords = []
                block_chord_idx = 0
                continue

            if re.match(r'\{Melody_Block\}', line, re.I):
                continue

            if re.match(r'\{Bass_Block\}', line, re.I):
                continue

            # Process chord block content (chords separated by |)
            if chord_block_active:
                if '|' in line:
                    chords = [c.strip() for c in line.split('|') if c.strip()]
                    current_chords.extend(chords)
                else:
                    chord = line.strip()
                    if chord and not chord.startswith('{') and not chord.startswith('}'):
                        current_chords.append(chord)
                continue

            # Melody/Bass commands
            self._parse_command(line)

        return self.events

    def _parse_command(self, line):
        """Parse a single command line."""

        # play(root, dur=quarter, vel=mf, octave=up)
        pm = re.match(r'play\((.+?)\)', line, re.I)
        if pm:
            args = self._parse_args(pm.group(1))
            dur = parse_dur(args.get('dur', self.default_dur))
            explicit_vel = 'vel' in args
            vel = parse_vel(args.get('vel', None))
            if not explicit_vel:
                vel = self._vel_for_note()  # dynamics arc applies unless vel= overrides

            # Support play(note=C4, ...) — direct note name
            note_str = args.get('note', '')
            if note_str:
                m = re.match(r'([A-G]#?b?)(\d+)', note_str, re.I)
                if m:
                    note_name = m.group(1)
                    octave = int(m.group(2))
                    semi = NOTE_TO_SEMI.get(note_name, 0)
                    if semi is not None:
                        midi = semi + (octave + 1) * 12
                        dur_ms = self.beats_to_ms(dur)
                        self.events.append({
                            'timestamp': int(self.cursor),
                            'midi': max(0, min(127, midi)),
                            'duration': max(1, int(dur_ms)),
                            'velocity': vel,
                        })
                        self.cursor += dur_ms
                        return

            # play(root, dur=quarter, vel=mf, octave=up) — scale degree
            degree = args.get('_0', 'root')
            octave_offset = 0
            oct_str = args.get('octave', '')
            if oct_str == 'up':
                octave_offset = 1
            elif oct_str == 'down':
                octave_offset = -1
            elif oct_str:
                try:
                    octave_offset = int(oct_str) - 4
                except ValueError:
                    pass

            midis = self._degree_to_midis(degree, octave_offset)
            dur_ms = self.beats_to_ms(dur)
            for m in midis:
                self.events.append({
                    'timestamp': int(self.cursor),
                    'midi': m,
                    'duration': max(1, int(dur_ms)),
                    'velocity': vel,
                })
            self.cursor += dur_ms
            return

        # hold(dur)
        hm = re.match(r'hold\((.+?)\)', line, re.I)
        if hm:
            dur = parse_dur(hm.group(1).strip())
            self.cursor += self.beats_to_ms(dur)
            return

        # arpeggio(up, dur=16th, vel=ff)
        am = re.match(r'arpeggio\((.+?)\)', line, re.I)
        if am:
            args = self._parse_args(am.group(1))
            direction = args.get('_0', 'up').lower()
            dur = parse_dur(args.get('dur', 'sixteenth'))
            vel = parse_vel(args.get('vel', None))
            count = int(args.get('count', 0)) or len(self.current_chord_midis)

            if not self.current_chord_midis:
                return

            midis = sorted(set(self.current_chord_midis))
            # Convert semitones to MIDI notes (octave 4)
            midis = [m + 60 for m in midis]
            if direction == 'down':
                midis = list(reversed(midis))
            elif direction == 'random':
                import random
                random.shuffle(midis)

            dur_ms = self.beats_to_ms(dur)
            for m in midis[:max(count, len(midis))]:
                self.events.append({
                    'timestamp': int(self.cursor),
                    'midi': m,
                    'duration': max(1, int(dur_ms * 0.9)),
                    'velocity': vel,
                })
                self.cursor += dur_ms
            return

        # chromatic_run(up, 2_octaves, dur=16th, vel=ff)
        cr = re.match(r'chromatic_run\((.+?)\)', line, re.I)
        if cr:
            args = self._parse_args(cr.group(1))
            direction = args.get('_0', 'up').lower()
            range_str = args.get('_1', '2_octaves').lower()
            dur = parse_dur(args.get('dur', 'sixteenth'))
            vel = parse_vel(args.get('vel', None))

            # Determine range in semitones
            oct_match = re.search(r'(\d+)', range_str)
            octaves = int(oct_match.group(1)) if oct_match else 2
            semitones = octaves * 12

            # Get starting note
            if self.current_chord_midis:
                start = min(self.current_chord_midis) + 60
            else:
                start = 60  # C4

            if direction == 'down':
                start = start + semitones
                step = -1
            else:
                step = 1

            dur_ms = self.beats_to_ms(dur)
            for s in range(semitones + 1):
                m = start + s * step
                if 0 <= m <= 127:
                    self.events.append({
                        'timestamp': int(self.cursor),
                        'midi': m,
                        'duration': max(1, int(dur_ms * 0.9)),
                        'velocity': vel,
                    })
                    self.cursor += dur_ms
            return

        # glissando(from=C4, to=C6)
        gm = re.match(r'glissando\((.+?)\)', line, re.I)
        if gm:
            args = self._parse_args(gm.group(1))
            from_n = args.get('from', 'C4')
            to_n = args.get('to', 'C6')
            dur = parse_dur(args.get('dur', 'half'))

            def note_to_midi(n):
                m = re.match(r'([A-G]#?b?)(\d+)', n)
                if m:
                    return midi_from_note(m.group(1), int(m.group(2)))
                return 60

            m1 = note_to_midi(from_n)
            m2 = note_to_midi(to_n)
            step = 1 if m2 > m1 else -1
            dur_ms = self.beats_to_ms(dur) / max(1, abs(m2 - m1) + 1)

            for m in range(m1, m2 + step, step):
                self.events.append({
                    'timestamp': int(self.cursor),
                    'midi': m,
                    'duration': max(1, int(dur_ms * 0.9)),
                    'velocity': self._vel_for_note(),
                })
                self.cursor += dur_ms
            return

        # pattern(name)
        pat = re.match(r'pattern\((.+?)\)', line, re.I)
        if pat:
            name = pat.group(1).strip().lower().strip('"\'')
            self._expand_pattern(name)
            return

        # chord(C_Major) — sets current chord
        cm2 = re.match(r'chord\((.+?)\)', line, re.I)
        if cm2:
            self._set_chord(cm2.group(1).strip())
            return

        # crescendo/decrescendo — velocity arc over the next N emitted notes
        dyn = re.match(r'(crescendo|decrescendo)\((.+?)\)', line, re.I)
        if dyn:
            args = self._parse_args(dyn.group(2))
            try:
                n = max(1, int(str(args.get('_0', '8')).split('_')[0]))
            except (ValueError, TypeError):
                n = 8
            target = 112 if dyn.group(1).lower() == 'crescendo' else 40
            self._dyn_total = n
            self._dyn_remaining = n
            self._dyn_from = self.default_vel
            self._dyn_target = target
            self._dyn_step = (target - self.default_vel) / float(n)
            return

        # cluster(N_octaves, dur=...)
        cl = re.match(r'cluster\((.+?)\)', line, re.I)
        if cl:
            args = self._parse_args(cl.group(1))
            oct_range = int(args.get('_0', '3').split('_')[0]) if args.get('_0') else 3
            dur = parse_dur(args.get('dur', 'sixteenth'))
            vel = parse_vel(args.get('vel', None))
            base = 48  # C3
            dur_ms = self.beats_to_ms(dur)
            for m in range(base, base + oct_range * 12):
                self.events.append({
                    'timestamp': int(self.cursor),
                    'midi': m,
                    'duration': max(1, int(dur_ms * 0.5)),
                    'velocity': vel,
                })
            self.cursor += dur_ms
            return

    def _parse_args(self, args_str):
        """Parse function arguments into dict. 'up, dur=16th, vel=ff' -> {_0: 'up', dur: '16th', vel: 'ff'}"""
        result = {}
        parts = re.split(r',\s*', args_str)
        for i, p in enumerate(parts):
            p = p.strip()
            if '=' in p:
                k, v = p.split('=', 1)
                result[k.strip().lower()] = v.strip().strip('"\'')
            else:
                result[f'_{i}'] = p.strip().strip('"\'')
        return result

    def _degree_to_midis(self, degree, octave_offset=0):
        """Convert scale degree to MIDI notes. 'root' -> chord root, 'third' -> chord third, etc."""
        if not self.current_chord_midis:
            return [60 + octave_offset * 12]

        degree_map = {
            'root': 0, '1': 0, 'r': 0,
            'third': 1, '3': 1, 't': 1,
            'fifth': 2, '5': 2,
            'seventh': 3, '7': 3,
            'ninth': 4, '9': 4,
            'octave': 0,
        }

        idx = degree_map.get(degree.lower(), 0)
        if degree.lower() == 'octave':
            semi = self.current_chord_midis[0] + 12
            return [semi + 60]  # Add C4 offset

        if idx < len(self.current_chord_midis):
            semi = self.current_chord_midis[idx]
            return [semi + 60 + octave_offset * 12]  # Convert to MIDI with octave
        return [60]

    def _expand_pattern(self, name):
        """Expand named rhythm patterns."""
        patterns = {
            'waltz': ['quarter', 'quarter', 'quarter'],
            'four_on_floor': ['quarter', 'quarter', 'quarter', 'quarter'],
            'syncopated': ['eighth', 'eighth', 'quarter', 'eighth'],
            '16th_roll': ['sixteenth', 'sixteenth', 'sixteenth', 'sixteenth'],
            'oom_pah': ['quarter', 'rest', 'quarter'],
            'walk_up': ['quarter', 'quarter', 'quarter', 'quarter'],
            'walk_down': ['quarter', 'quarter', 'quarter', 'quarter'],
        }

        durs = patterns.get(name, ['quarter'])
        for d in durs:
            if d == 'rest':
                self.cursor += self.beats_to_ms(1.0)
            else:
                dur_beats = parse_dur(d)
                midis = self.current_chord_midis[:1] if self.current_chord_midis else [60]
                for m in midis:
                    self.events.append({
                        'timestamp': int(self.cursor),
                        'midi': m,
                        'duration': max(1, int(self.beats_to_ms(dur_beats))),
                        'velocity': self._vel_for_note(),
                    })
                self.cursor += self.beats_to_ms(dur_beats)
