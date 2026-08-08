// v5 — Pattern demo: the new v5 statements in one piece
// !fn macros · scale/range loops · print · assert · prog · perc · @seed + pick
@bpm 96
@key C Major
@seed 42

// ── 1. !fn — a parameterized macro: play any note at any duration/velocity
!fn arp(r, d, v) = play note($r) @dur:$d @vel:$v

!arp(C4, e, mf)
!arp(E4, e, mf)
!arp(G4, e, mf)

// ── 2. for-in-scale — iterate the degrees of C major (octave 4, one octave)
for $n in scale(C major, 4, 1) {
    print $n
    play note($n) @dur:q @vel:mp
}

// ── 3. for-in-range with a compile-time assert guard
for $i in 1..4 {
    assert $i < 5, "iteration must stay under the cap"
    print { $i * 2 }
}

// ── 4. prog — chord progression (root + quality + optional duration)
prog(C:q G:q Am:h F:q)

// ── 5. perc — GM percussion on channel 9
perc(kick)
perc(hihat)

// ── 6. @seed + pick — deterministic choice, identical on every compile
$fill = pick(C5 E5 G5)
play note($fill) @dur:h @vel:mf
