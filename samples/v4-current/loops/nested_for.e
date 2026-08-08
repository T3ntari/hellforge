/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       nested_for.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates nested for loops — a loop inside another loop.
   Nested loops create multi-dimensional patterns such as grids,
   matrix-like sequences, or chord progressions with variations.

/* @bpm 100 — Slower tempo so the nested grid is clearly audible. */
@bpm 100

/* Outer loop: $i from 0 to 3 (4 iterations — one per "beat" or "row").
   Inner loop: $j from 0 to 3 (4 iterations — one per "subdivision").
   
   Total notes: 4 * 4 = 16 notes. */

for $i = 0 to 3 {
    /* $i — controls the "row" / harmonic layer.
       N{60 + $i * 4} — each outer iteration transposes up by a major third:
         i=0: 60 (C4), i=1: 64 (E4), i=2: 68 (G#4), i=3: 72 (C5) */

    for $j = 0 to 3 {
        /* $j — controls the "column" / rhythmic subdivision.
           N{60 + $j * 2} — inner loop adds diatonic steps:
             j=0: 0, j=1: +2, j=2: +4, j=3: +6
           
           Combined note: N{60 + $i * 4 + $j * 2}
           This creates a 2D pitch grid where each cell has
           a unique note computed from both loop indices. */

        /* T{$i * 400 + $j * 100} — Time offset:
           Each cell is positioned at row * 400 + col * 100 ticks.
           $i=0, $j=0: T0 (first note)
           $i=0, $j=3: T300
           $i=1, $j=0: T400
           This lays out the grid left-to-right, top-to-bottom. */

        T{$i * 400 + $j * 100} N{60 + $i * 4 + $j * 2} D80 V80
    }
}

/* The resulting 4x4 note grid sounds like a 16-step sequencer
   where each row is a different pitch register.

   Nested loops are powerful for:
   - Step sequencer patterns (rows = pitch, columns = time)
   - Drum machine matrices (rows = drum type, columns = time)
   - Chord variations (outer = chord, inner = inversion)
   - Algorithmic counterpoint (outer = voice 1, inner = voice 2) */

// Run from project root: py ep.py compile samples/v4-current/loops/nested_for.e
