{
  function flatten(arr) {
    return [].concat.apply([], arr.filter(x => x !== null));
  }
}

// ===== TOP LEVEL =====

HumanStart = _ s:HumanStatement* _ {
  return flatten(s);
}

MachineStart = _ s:MachineStatement* _ {
  return flatten(s);
}

// ===== HUMAN MODE =====

HumanStatement = PlayNote / PlayChord / HumanComment

HumanComment = _ "//" [^\n]* { return null; }

PlayNote = _ "play"i _ "note(" _ note:NoteWithOctave _ ")" _ props:(_ Prop)* _ {
  return { type: 'play_note', note: note, props: (props||[]).map(x => x[1]) };
}

PlayChord = _ "play"i _ "chord(" _ root:ChordRoot _ "," _ quality:Quality _ ")" _ props:(_ Prop)* _ {
  return { type: 'play_chord', root: root, quality: quality, props: (props||[]).map(x => x[1]) };
}

NoteWithOctave = pitch:Pitch oct:Octave { return pitch + oct; }

ChordRoot = pitch:Pitch oct:Octave? { return pitch + (oct || '4'); }

Quality = qual:$([a-zA-Z0-9+#]+) { return qual; }

Prop = "@" name:PropName _ ":" _ value:PropValue {
  return { name: name.toLowerCase(), value: value };
}

PropName = "dur"i / "vel"i / "velocity"i / "strum"i / "pedal"i

PropValue = $[^ \t\n\r@]+

// ===== MACHINE MODE =====

MachineStatement = MachineEvent / MachineComment

MachineComment = _ "//" [^\n]* { return null; }

MachineEvent = _ T:Timestamp _ N:NoteNum _ D:Duration? _ V:Velocity? _ fx:(_ Fx)* _ {
  let props = [];
  if (D !== null) props.push({ name: 'dur', value: String(D) });
  if (V !== null) props.push({ name: 'vel', value: String(V) });
  const fxList = fx.map(x => x[1]);
  for (const f of fxList) props.push(f);

  return {
    type: 'machine_event',
    timestamp: T,
    midi: N,
    props: props,
    fx: fxList.reduce((acc, f) => { acc[f.name] = f.value; return acc; }, {})
  };
}

Timestamp = "T"i d:[0-9]+ { return parseInt(d.join(''), 10); }

NoteNum = "N"i d:[0-9]+ { return parseInt(d.join(''), 10); }

Duration = "D"i d:[0-9]+ { return parseInt(d.join(''), 10); }

Velocity = "V"i v:[0-9.]+ { return parseFloat(v.join('')); }

Fx = pb:PitchBend / pan:Pan

PitchBend = "P[bend:"i d:SignedInt "]" {
  return { name: 'bend', value: d };
}

Pan = "S[pan:"i v:SignedFloat "]" {
  return { name: 'pan', value: v };
}

// ===== SHARED =====

Pitch = "C#" / "Db" / "D#" / "Eb" / "F#" / "Gb" / "G#" / "Ab" / "A#" / "Bb"
      / "c#" / "db" / "d#" / "eb" / "f#" / "gb" / "g#" / "ab" / "a#" / "bb"
      / [A-G] / [a-g]

Octave = d:[0-9]+ { return d.join(''); }

Int = d:[0-9]+ { return parseInt(d.join(''), 10); }

SignedInt = sign:"-"? d:[0-9]+ {
  return parseInt((sign||'') + d.join(''), 10);
}

Float = int:Int "." frac:[0-9]+ {
  return parseFloat(int + '.' + frac.join(''));
} / Int

SignedFloat = sign:"-"? int:[0-9]+ "." frac:[0-9]+ {
  return parseFloat((sign||'') + int.join('') + '.' + frac.join(''));
} / SignedInt

_ = [ \t\n\r]*
