const NOTE_TO_SEMITONE = {
  'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3,
  'E': 4, 'F': 5, 'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8,
  'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11
};

const CHORD_INTERVALS = {
  'major':  [0, 4, 7],
  'minor':  [0, 3, 7],
  'dim':    [0, 3, 6],
  'aug':    [0, 4, 8],
  'sus2':   [0, 2, 7],
  'sus4':   [0, 5, 7],
  'dom7':   [0, 4, 7, 10],
  'maj7':   [0, 4, 7, 11],
  'min7':   [0, 3, 7, 10],
  'dim7':   [0, 3, 6, 9],
  'm7b5':   [0, 3, 6, 10],
};

const QUALITY_ALIASES = {
  'M': 'major', 'MAJ': 'major', 'Maj': 'major',
  'maj': 'major', 'major': 'major', '': 'major',
  'm': 'minor', 'MIN': 'minor', 'Min': 'minor',
  'min': 'minor', 'minor': 'minor',
  'dim': 'dim', 'o': 'dim',
  'aug': 'aug', '+': 'aug',
  '7': 'dom7', 'dom7': 'dom7',
  'maj7': 'maj7', 'M7': 'maj7',
  'min7': 'min7', 'm7': 'min7',
  'dim7': 'dim7',
  'm7b5': 'm7b5',
};

const VELOCITY_NAMES = {
  'ppp': 16, 'pp': 33, 'p': 49,
  'mp': 64, 'mf': 80, 'f': 96,
  'ff': 112, 'fff': 126,
  'soft': 49, 'normal': 80, 'loud': 112,
  'silent': 0, 'max': 127,
};

const DUR_MAP = {
  'whole': 4, 'w': 4, '1n': 4,
  'half': 2, 'h': 2, '2n': 2,
  'quarter': 1, 'q': 1, '4n': 1,
  'eighth': 0.5, 'e': 0.5, '8n': 0.5,
  'sixteenth': 0.25, 's': 0.25, '16n': 0.25,
  'thirtysecond': 0.125, 't': 0.125, '32n': 0.125,
};

export function noteToMidi(pitch, octave) {
  const semitone = NOTE_TO_SEMITONE[pitch];
  if (semitone === undefined) throw new Error(`Unknown note: ${pitch}`);
  return semitone + (parseInt(octave) + 1) * 12;
}

export function midiToName(midi) {
  const octave = Math.floor(midi / 12) - 1;
  const semitone = midi % 12;
  const names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  return names[semitone] + octave;
}

export function resolveQuality(name) {
  if (QUALITY_ALIASES[name] !== undefined) return QUALITY_ALIASES[name];
  const lower = name.toLowerCase().replace(/[^a-z0-9+]/, '');
  return QUALITY_ALIASES[lower] || lower;
}

export function getChordSemitones(rootMidi, quality) {
  const intervals = CHORD_INTERVALS[quality];
  if (!intervals) throw new Error(`Unknown chord quality: ${quality}`);
  return intervals.map(i => rootMidi + i);
}

export function parseDuration(dur, bpm) {
  if (dur === undefined || dur === null) return null;
  const str = String(dur).toLowerCase().replace(/n$/, '');

  const match = str.match(/^(\d+\.?\d*)(ms)?$/);
  if (match) return parseFloat(match[1]);

  let beats = DUR_MAP[str] || DUR_MAP[str.replace(/\.$/, '')];
  if (beats !== undefined) {
    const dotted = String(dur).endsWith('.');
    if (dotted) beats *= 1.5;
    return (beats * 60000) / bpm;
  }
  return null;
}

export function parseVelocity(val) {
  if (val === undefined || val === null) return null;
  const str = String(val).toLowerCase();
  if (str in VELOCITY_NAMES) return VELOCITY_NAMES[str];
  const num = parseFloat(str);
  if (!isNaN(num)) {
    if (num <= 1) return Math.round(num * 127);
    return Math.round(Math.max(0, Math.min(127, num)));
  }
  return null;
}

export function parseStrum(val) {
  if (!val) return null;
  const match = String(val).match(/^(up|down|random)\s*\(?\s*(\d+)\s*ms\s*\)?$/i);
  if (match) {
    return { direction: match[1].toLowerCase(), time: parseInt(match[2]) };
  }
  return null;
}
