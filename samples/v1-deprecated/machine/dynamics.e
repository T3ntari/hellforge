/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v1 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       dynamics.e
   Version:    v1 (machine mode) — DEPRECATED
   Status:     DEPRECATED — v1 machine mode. Use v4 instead.
   
   Demonstrates the full dynamic (velocity) range of v1 machine mode.
   The same note (C4, N60) is played at 6 different velocity values,
   showing how the V token controls loudness from barely audible to maximum.

/* --- DEPRECATION NOTICE ---
   v1 machine mode is deprecated. In v4, use V{ppp}, V{pp}, V{p}, V{mp},
   V{mf}, V{f}, V{ff}, V{fff} or @-directive dynamics instead.
   ------------------------- */

/* T0 = tempo default, N60 = C4, D250 = quarter note duration.

   Velocity values (V) follow the MIDI specification (0-127):
     0   = silent
     1   = barely audible
     64  = mf (mezzo-forte) — moderate loudness
     127 = fff (fortississimo) — maximum

   Standard mapping:
     ppp = 16   pp = 33   p = 49   mp = 64
     mf  = 80   f  = 96   ff = 112  fff = 127
*/

/* C4 at velocity 10 — barely audible, like ppp minus (whisper) */
T0 N60 D250 V10

/* C4 at velocity 30 — very soft, between ppp and pp */
T0 N60 D250 V30

/* C4 at velocity 50 — moderately soft, around p (piano) */
T0 N60 D250 V50

/* C4 at velocity 80 — moderately loud, around mf (mezzo-forte) */
T0 N60 D250 V80

/* C4 at velocity 100 — loud, between f and ff */
T0 N60 D250 V100

/* C4 at velocity 127 — maximum, fff (fortississimo) */
T0 N60 D250 V127

/* Dynamic crescendo effect: each successive note gets louder,
   demonstrating the full 0-127 velocity spectrum in 6 steps. */

// Run from project root: py ep.py compile samples/v1-deprecated/machine/dynamics.e
