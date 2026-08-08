/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       for_scale.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates the for loop construct in v3.
   Loops are essential for repetitive patterns like scales,
   arpeggios, drum patterns, and ostinatos.

/* for $i = 0 to 7 { ... } — Loop variable $i goes from 0 to 7 inclusive.
   That's 8 iterations total (0, 1, 2, 3, 4, 5, 6, 7).
   The loop body executes once per iteration.

   Inside the body, {$i} is replaced with the current loop index.
   Note formula: 60 + {$i * 2} produces:
     i=0: 60 (C4), i=1: 62 (D4), i=2: 64 (E4), ...
   This is a C major scale in whole steps? No — that's wrong.
   Let's use the actual C major intervals.

   Better formula: N{60 + $i * 2} maps to:
     i=0: 60 (C), i=1: 62 (D), i=2: 64 (E), i=3: 66 (F#! wrong!)
   
   For proper C major: use an interval array.
   But in HELLFORGE v3, we can't index arrays yet.
   Just using step=2 gives a whole-tone scale, which is fine for demo.
*/

for $i = 0 to 7 {
    /* N{60 + $i * 2}  — Play notes at intervals of 2 semitones (whole tone scale).
       D{$i * 50 + 100} — Duration increases with each note (ritardando effect).
       V{$i * 10 + 40}  — Velocity increases (crescendo). */
    T0 N{60 + $i * 2} D{$i * 50 + 100} V{$i * 10 + 40}
}

/* Loop variable $i is automatically scoped to the loop.
   The body can contain any valid E tokens, including nested loops,
   expressions, and channel directives.

   Loop variants:
     for $i = 0 to 10       — 11 iterations (0 through 10 inclusive)
     for $i = 10 to 0       — descending (10, 9, 8, ..., 0)
     for $i = 0 to 100 step 10 — every 10th value
*/

// Run from project root: py ep.py compile samples/v3-supported/loops/for_scale.e
