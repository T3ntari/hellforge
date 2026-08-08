// v5 — Piano Performance demo: the canonical HELLFORGE syntax
// v5 = v4 + piano performance features (pedal, rests, articulations,
// tuplets, octave shift, velocity curves, ties)
@bpm 100
@key C Major
@sr:48000
@bit:24
@quality:high
@vol:0.7
@curve vel 60 115

pedal on
play note(C4) @dur:q @vel:mf @art:staccato
play note(E4) @dur:q @vel:mp @art:legato
t3(G4 C5 E5) @vel:f
rest e
play chord(C, major) @dur:h @vel:f @art:tenuto
pedal off

@oct:+1
play note(C4~) @dur:q @vel:mf
play note(C4~) @dur:q @vel:mf
@oct:0
play note(E5) @dur:h @vel:ff @art:accent
