/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       functions.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates all built-in mathematical functions available in
   {$expr} expressions. These enable algorithmic and procedural
   composition — generating note parameters from formulas.

/* Built-in math functions (all return integers):

   sin(x)   — Sine of x degrees. Returns value in range -1000 to 1000.
   cos(x)   — Cosine of x degrees. Same scaling.
   sqrt(x)  — Square root of x (rounded).
   pow(b,e) — b raised to power e (b^e).
   min(a,b) — Returns the smaller of a and b.
   max(a,b) — Returns the larger of a and b.
   abs(x)   — Absolute value of x (removes negative sign).
   floor(x) — Rounds x down to the nearest integer.
*/

/* sin(45) — Sine of 45 degrees = ~0.707 * 1000 = 707.
   Useful for oscillating note patterns (LFO-like effects). */
T0 N{60 + sin(45) / 50} D200 V80

/* cos(60) — Cosine of 60 degrees = 0.5 * 1000 = 500.
   Combined with sin, creates stereo panning/alternating patterns. */
T0 N{60 + cos(60) / 50} D200 V80

/* sqrt(144) — Square root of 144 = 12.
   Useful for mapping non-linear values to note numbers. */
T0 N{sqrt(144) + 48} D200 V80    /* 12 + 48 = 60 = C4 */

/* pow(2, 3) — 2^3 = 8.
   Exponential scaling — useful for dynamic curves. */
T0 N{pow(2, 3) * 5} D200 V80    /* 8 * 5 = 40 */

/* min(70, 100) — Returns 70 (the smaller value).
   Use as a clamp: N{max(60, $someValue)} ensures note >= 60. */
T0 N{min(70, 100)} D200 V80     /* 70 */

/* max(70, 100) — Returns 100 (the larger value). */
T0 N{max(70, 100)} D200 V80     /* 100 */

/* abs(-5) — Returns 5.
   Removes negative sign, useful after subtractions. */
T0 N{60 + abs(-5)} D200 V80     /* 65 */

/* floor(45.7) — Returns 45.
   Truncates decimal (note: all results are integers anyway). */
T0 N{60 + floor(45)} D200 V80   /* 105 */

/* Functions can be nested: sin(pow(2, 3) * 10).
   Expression evaluator handles arbitrary depth. */

// Run from project root: py ep.py compile samples/v3-supported/math/functions.e
