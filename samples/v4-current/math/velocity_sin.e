/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       velocity_sin.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Uses the sine function to modulate velocity (volume) creating
   wave-like dynamic envelopes. This simulates natural phrasing
   that rises and falls like breathing or vibrato.

/* @bpm 140 — Moderate tempo for clear dynamic shaping. */
@bpm 140

/* for $i = 0 to 31 — 32 iterations = 2 full cycles of a sine wave
   at this step size (since sin repeats every 2*PI ~ 6.28,
   and 0.5 * 32 / 6.28 ~ 2.5 cycles — let's adjust). */

for $i = 0 to 31 {
    /* V{60 + round(30 * sin($i * 0.5))} — Dynamic velocity formula:
       
       sin($i * 0.5) — Sine wave with period ~12.56 iterations.
       As $i goes 0..31, sin() goes from 0 -> +1 -> 0 -> -1 -> 0
       about 2.5 times.
       
       30 * sin(...) — Amplitude scaling. Results in range [-30, +30].
       
       round(...) — Round to nearest integer (velocity must be int).
       
       60 + ... — Center around velocity 60 (mp range).
       Final range: approximately 30 (p) to 90 (f).
       
       Result: a natural swelling and fading of volume,
       like a cello player using bow pressure for expression. */
    T{$i * 100} N{60 + $i % 12} D80 V{60 + round(30 * sin($i * 0.5))}
}

/* The velocity envelope forms a sinusoidal wave:
   /\    /\    /\
  /  \  /  \  /  \
 /    \/    \/    \
  Each peak is a dynamic high point, each trough is a soft point.

   Try different frequency multipliers:
     sin($i * 0.25) — slower waves (longer phrases)
     sin($i * 1.0)  — faster waves (tremolo effect)
     sin($i * 2.0)  — very fast (vibrato speed) */

// Run from project root: py ep.py compile samples/v4-current/math/velocity_sin.e
