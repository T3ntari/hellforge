// =====================================================================
// Aurora Nocturne — a complete v5 piano piece in C major
//   A: Intro      (bars 1-8)   pp -> mp, sparse, swell curve
//   B: Theme      (bars 9-16)  mf, singable melody over rolling left hand
//   B': Restate   (bars 17-24) f, the theme returns emphatic
//   C: Interlude  (bars 25-32) p, the night deepens into A minor
//   D: Climax     (bars 33-40) ff -> fff, chords, runs, heartbeat drums
//   E: Coda       (bars 41-48) the theme once more, then dissolves
// 48 bars x 4 beats @ 78 bpm ~= 2:28
// =====================================================================
@bpm 78
@key C major
@seed 7
@vol:0.8
@master:0.85
@curve vel 38 90 over 20q          // the intro swells from pp toward mp

print "Aurora Nocturne — a night in C major"

// !fn — a staccato ornament macro used through the piece
!fn spark(n, v) = play note($n) @dur:e @vel:$v @art:staccato

// ── A · INTRO (bars 1-8) ──────────────────────────────────────────────
pedal on

// bar 1 — foundation C
play note(C3) @dur:w @vel:pp @art:tenuto

// bar 2 — fifth, then a soft high C held by a tie
play note(G3) @dur:h @vel:pp @art:tenuto
play note(C4) @dur:q @vel:pp @tie
play note(C4) @dur:q @vel:pp

// bar 3 — falling phrase into the middle register
play note(E4) @dur:q. @vel:pp
play note(D4) @dur:e @vel:pp
play note(B3) @dur:h @vel:ppp

// bar 4 — rolling C then Am arpeggios
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:pp }
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:pp }

// bar 5 — F then G rolls, breathing a little louder
for $n in [F2 C3 A3 C3] { play note($n) @dur:e @vel:pp }
for $n in [G2 D3 B3 D3] { play note($n) @dur:e @vel:p }

// bar 6 — the theme's first notes whisper in
rest e
!spark(B4, p)
play note(C5) @dur:q @vel:p
play note(D5) @dur:q @vel:mp
play note(E5) @dur:q @vel:mp

// bar 7 — shimmer, building toward the theme
!spark(G4, mp)
!spark(G4, mp)
play note(E5) @dur:q @vel:mp
play note(G5) @dur:h @vel:mp @art:tenuto

// bar 8 — settle back down; a seeded ornament closes the intro
play note(C5) @dur:q. @vel:mp
play note(B4) @dur:e @vel:mp
play note(G4) @dur:q @vel:p
$fin = pick(E4 G4 C5)
play note($fin) @dur:q @vel:pp

pedal off

// ── B · THEME (bars 9-16) ─────────────────────────────────────────────
// bar 9 — C: the anthem
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:mp }
play note(E5) @dur:q @vel:mf @art:tenuto
play note(G5) @dur:q @vel:mf

// bar 10 — Am: turning phrase
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:mp }
play note(C5) @dur:q @vel:mf
play note(B4) @dur:e @vel:mf
play note(A4) @dur:e @vel:mf

// bar 11 — F: lifting
for $n in [F2 C3 A3 C3] { play note($n) @dur:e @vel:mp }
play note(A4) @dur:q @vel:mf
play note(C5) @dur:q @vel:mf @art:tenuto

// bar 12 — G: the question
for $n in [G2 D3 B3 D3] { play note($n) @dur:e @vel:mp }
play note(B4) @dur:q @vel:mf
play note(D5) @dur:q @vel:mf

// bar 13 — C: first ascent to the high octave
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:mp }
play note(G5) @dur:e @vel:mf
play note(E5) @dur:e @vel:mf
play note(C6) @dur:q @vel:mf

// bar 14 — Am: answering descent
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:mp }
play note(A5) @dur:q @vel:mf
play note(E5) @dur:q @vel:mf

// bar 15 — F: wind-down
for $n in [F2 C3 A3 C3] { play note($n) @dur:e @vel:mp }
play note(F5) @dur:q @vel:mf
play note(E5) @dur:e @vel:mf
play note(D5) @dur:e @vel:mf

// bar 16 — G: half-cadence, held by a tilde tie
for $n in [G2 D3 B3 D3] { play note($n) @dur:e @vel:mp }
B4~ q q

// ── B' · RESTATEMENT (bars 17-24) ────────────────────────────────────
// bar 17 — C
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:mp }
play note(E5) @dur:q @vel:f @art:legato
play note(G5) @dur:q @vel:f

// bar 18 — Am
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:mp }
play note(C5) @dur:q @vel:f
play note(B4) @dur:e @vel:f
play note(A4) @dur:e @vel:f

// bar 19 — F, accented top
for $n in [F2 C3 A3 C3] { play note($n) @dur:e @vel:mp }
play note(A4) @dur:q @vel:f
play note(C5) @dur:q @vel:f @art:accent

// bar 20 — G
for $n in [G2 D3 B3 D3] { play note($n) @dur:e @vel:mp }
play note(B4) @dur:q @vel:f
play note(D5) @dur:q @vel:f

// bar 21 — C, accented peak
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:mp }
play note(G5) @dur:e @vel:f
play note(E5) @dur:e @vel:f
play note(C6) @dur:q @vel:f @art:accent

// bar 22 — Am
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:mp }
play note(A5) @dur:q @vel:f
play note(E5) @dur:q @vel:f

// bar 23 — F
for $n in [F2 C3 A3 C3] { play note($n) @dur:e @vel:mp }
play note(F5) @dur:q @vel:f
play note(E5) @dur:e @vel:f
play note(D5) @dur:e @vel:f

// bar 24 — G -> C: the period ends on a full cadence
for $n in [G2 D3 B3 D3] { play note($n) @dur:e @vel:mp }
play chord(C, major) @dur:h @vel:ff

// ── C · INTERLUDE (bars 25-32) ────────────────────────────────────────
// bar 25 — Am
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:p }
play note(E5) @dur:q @vel:p
play note(A4) @dur:q @vel:p

// bar 26 — Dm
for $n in [D3 A3 F4 A3] { play note($n) @dur:e @vel:p }
play note(F5) @dur:q @vel:mp
play note(D5) @dur:q @vel:p

// bar 27 — Am
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:p }
play note(C5) @dur:q @vel:p
play note(E5) @dur:q @vel:p

// bar 28 — E7: the dominant darkens, a dom7 colour
for $n in [E2 B2 G3 B2] { play note($n) @dur:e @vel:p }
play note(B4) @dur:q @vel:mp
play chord(E, dom7) @dur:q @vel:mp

// bar 29 — Am: a long held E swells, then fades
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:p }
play note(E5) @dur:q @vel:p @tie
play note(E5) @dur:q @vel:pp

// bar 30 — Dm
for $n in [D3 A3 F4 A3] { play note($n) @dur:e @vel:p }
play note(F5) @dur:q @vel:mp
play note(D5) @dur:q @vel:p

// bar 31 — Am
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:p }
play note(C5) @dur:q @vel:mp
play note(B4) @dur:q @vel:p

// bar 32 — E7: climbing eighths launch the climax
for $n in [E2 B2 G3 B2] { play note($n) @dur:e @vel:p }
play note(B4) @dur:e @vel:mp
play note(C5) @dur:e @vel:mp
play note(D5) @dur:e @vel:mp
play note(E5) @dur:e @vel:mp

// ── D · CLIMAX (bars 33-40) ───────────────────────────────────────────
pedal on

// bar 33 — C
play chord(C, major) @dur:q @vel:f
perc(kick)
for $n in [C4 E4 G4 C5] { play note($n) @dur:e @vel:f }

// bar 34 — G
play chord(G, major) @dur:q @vel:f
perc(kick)
for $n in [B3 D4 G4 B4] { play note($n) @dur:e @vel:f }

// bar 35 — Am
play chord(A, minor) @dur:q @vel:f
perc(kick)
for $n in [A3 C4 E4 A4] { play note($n) @dur:e @vel:f }

// bar 36 — F
play chord(F, major) @dur:q @vel:f
perc(kick)
for $n in [F3 A3 C4 F4] { play note($n) @dur:e @vel:f }

// bar 37 — C, ff, triplet turn
play chord(C, major) @dur:q @vel:ff @art:accent
perc(kick)
t3(C5 E5 G5) @vel:ff

// bar 38 — G
play chord(G, major) @dur:q @vel:ff
perc(kick)
for $n in [G4 B4 D5 G5] { play note($n) @dur:e @vel:ff }

// bar 39 — Am
play chord(A, minor) @dur:q @vel:ff
perc(kick)
for $n in [A4 C5 E5 A5] { play note($n) @dur:e @vel:ff }

// bar 40 — C: the summit, with a crash
play chord(C, major) @dur:h @vel:fff
perc(kick)
perc(crash)

// ── E · CODA (bars 41-48) ─────────────────────────────────────────────
pedal off

// bar 41 — C, the theme returns once more, softer
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:p }
play note(E5) @dur:q @vel:mf
play note(G5) @dur:q @vel:mp

// bar 42 — gentle hymn: the progression itself
prog(C:q Am:q F:q G:q)

// bar 43 — Am
for $n in [A2 E3 C4 E3] { play note($n) @dur:e @vel:p }
play note(C5) @dur:q @vel:mp
play note(B4) @dur:e @vel:mp
play note(A4) @dur:e @vel:p

// bar 44 — F, with a seeded soft ornament velocity
$v = rand(27, 40)
assert $v >= 27, "coda velocity floor"
for $n in [F2 C3 A3 C3] { play note($n) @dur:e @vel:p }
play note(B4) @dur:q @vel:p
play note(A4) @dur:q @vel:$v

// bar 45 — echo of the intro, the last note an octave lower
rest e
!spark(B4, p)
play note(C5) @dur:q @vel:p
play note(D5) @dur:q @vel:pp
play note(E5) @dur:q @vel:pp @oct:-1

// bar 46 — C
for $n in [C3 G3 E4 G3] { play note($n) @dur:e @vel:pp }
play note(E5) @dur:q @vel:pp
play note(G5) @dur:q @vel:pp

// bar 47 — a rising scale dissolves into the final chord
for $n in scale(C major, 5, 1) {
    print $n
    play note($n) @dur:e @vel:pp @art:tenuto
}
rest e

// bar 48 — the last breath: soft roll, final C chord
pedal on
for $n in [C3 G3 C4 E4] { play note($n) @dur:e @vel:pp }
play chord(C, major) @dur:h @vel:pp @art:tenuto
pedal off

print midi