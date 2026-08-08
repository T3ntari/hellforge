/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       tempo_curve.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates the @curve directive for dynamic tempo changes.
   @curve creates a smooth transition of a parameter (bpm in this case)
   from a start value to an end value over a specified number of beats.
   This is v4's mechanism for accelerando and ritardando.

/* @bpm 60 — Initial tempo: 60 BPM (very slow, one beat per second).
   The tempo will increase from here to 120 BPM. */
@bpm 60

/* @curve bpm from 60 to 120 over 4 — Accelerando directive.
   This creates a tempo ramp:
   - Starting at 60 BPM (one beat per second)
   - Linearly increasing to 120 BPM (two beats per second)
   - Over a duration of 4 beats (4 quarter notes at the average tempo)
   
   The @curve affects all subsequent notes within its span.
   After the curve completes, tempo stays at 120 BPM. */
@curve bpm from 60 to 120 over 4

/* While the curve is active, the tempo gradually increases.
   These 8 notes will start slow and end fast (accelerando). */
C4 q     /* About 60 BPM — slow, deliberate */
D4 q     /* Tempo increasing */
E4 q     /* Getting noticeably faster */
F4 q     /* Moderate speed */
G4 q     /* Approaching 120 BPM */
A4 q     /* Almost at target tempo */
B4 q     /* Fast */
C5 w     /* At 120 BPM — final held note, now at full speed */

/* @curve can control many parameters:
   @curve bpm from 120 to 60 over 4   — ritardando (slowing down)
   @curve vol from 50 to 127 over 8   — overall volume swell
   @curve pan from 0 to 100 over 16   — auto-pan effect

   Curve interpolation is always linear.
   Multiple curves can overlap or cascade for complex envelopes. */

// Run from project root: py ep.py compile samples/v4-current/generative/tempo_curve.e
