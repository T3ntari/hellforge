/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       for_step.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates the "step" modifier on for loops.
   Step allows skipping values — useful for intervals, chord skips,
   and non-sequential note selection.

/* @bpm 120 — Standard tempo. */
@bpm 120

/* for $i = 0 to 12 step 3 — Iterates $i = 0, 3, 6, 9, 12.
   The step keyword tells the loop to add 3 each time instead of 1.
   That's only 5 iterations instead of 13 with step 1.

   This creates a sequence of notes spaced 3 semitones apart:
     i=0:  N{60}  = C4
     i=3:  N{63}  = D#4 (minor third above)
     i=6:  N{66}  = F#4 (tritone — augmented fourth)
     i=9:  N{69}  = A4  (major sixth)
     i=12: N{72}  = C5  (octave) */

for $i = 0 to 12 step 3 {
    T{$i * 150} N{60 + $i} D100 V80
}

/* Now a descending pattern with step — skipping 4 semitones
   (a major third interval each time). */
for $i = 24 to 0 step 4 {
    T{(24 - $i) * 150} N{48 + $i} D100 V{80 - $i}
}

/* Step values and their musical effects:
   step 1  = chromatic scale (every semitone)
   step 2  = whole tone scale (every whole step)
   step 3  = minor third intervals (diminished/arpeggio feel)
   step 4  = major third intervals (whole tone-ish)
   step 5  = perfect fourth (scale-like)
   step 7  = perfect fifth (wide leaps)
   step 12 = octave jumps

   Negative step (step -1) works for descending loops:
   for $i = 12 to 0 step 1  — goes 12, 11, 10, ..., 0 */

// Run from project root: py ep.py compile samples/v4-current/loops/for_step.e
