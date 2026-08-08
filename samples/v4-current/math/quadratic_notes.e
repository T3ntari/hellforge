/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       quadratic_notes.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Uses a quadratic function to generate curved note patterns.
   Quadratic equations produce parabolic curves — useful for
   accelerating/decelerating pitch sequences and "bounce" effects.

/* @bpm 120 — Standard tempo. */
@bpm 120

/* quadratic(a, b, c) — Built-in quadratic function:
   f(x) = a*x^2 + b*x + c
   
   Where x is the first argument after the function name.
   In HELLFORGE v4, quadratic() takes parameters:
     quadratic(coeff_a, coeff_b, coeff_c)
   and computes: coeff_a * x^2 + coeff_b * x + coeff_c
   where x is the loop variable $i.
*/

/* for $i = 0 to 15 — 16 notes forming a parabolic pitch arc. */

for $i = 0 to 15 {
    /* N{round(quadratic(1, -$i, $i * 2) + 60)} — Quadratic pitch curve:
       
       At $i = 0:  quadratic(1, 0, 0) = 0,  + 60 = 60 (C4)
       At $i = 4:  quadratic(1, -4, 8) = 1*16 - 4*4 + 8 = 16-16+8 = 8, +60 = 68 (G#4)
       At $i = 8:  quadratic(1, -8, 16) = 64 - 64 + 16 = 16, +60 = 76 (E5)
       At $i = 12: quadratic(1, -12, 24) = 144 - 144 + 24 = 24, +60 = 84 (C6)
       At $i = 15: quadratic(1, -15, 30) = 225 - 225 + 30 = 30, +60 = 90 (F#6)
       
       The quadratic curve (-$i + $i*2 becomes +$i overall) creates
       an upward-accelerating pitch arc — notes climb faster as $i increases.
       
       round() ensures the result is a valid integer MIDI note number. */
    T{$i * 80} N{round(quadratic(1, -$i, $i * 2) + 60)} D60 V80
}

/* Parabolic pitch shapes create interesting musical contours:
   - Positive quadratic: upward-accelerating (exciting, building)
   - Negative quadratic: upward-decelerating (tension, approaching limit)
   - Full parabola: go up then come back down (arc shape)

   Try: quadratic(-1, $i, 0) for a downward arc (peak then fall). */

// Run from project root: py ep.py compile samples/v4-current/math/quadratic_notes.e
