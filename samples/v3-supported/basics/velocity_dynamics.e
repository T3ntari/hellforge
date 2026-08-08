/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       velocity_dynamics.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates all velocity (dynamic) words in v3 syntax.
   Each note has the same duration (quarter note) but a different
   velocity, creating a crescendo from ppp to fff.

/* Velocity keywords map to specific MIDI velocity values:

   ppp = 16   — pianississimo, extremely soft
   pp  = 33   — pianissimo, very soft
   p   = 49   — piano, soft
   mp  = 64   — mezzo-piano, moderately soft
   mf  = 80   — mezzo-forte, moderately loud (default)
   f   = 96   — forte, loud
   ff  = 112  — fortissimo, very loud
   fff = 127  — fortississimo, maximum

   Syntax: Note Duration Velocity
   The velocity word follows the duration code.
*/

/* Soft dynamics — intimate, gentle */
C4 q ppp   /* ppp — barely audible whisper. C4 at velocity 16. */
D4 q pp    /* pp  — very soft. D4 at velocity 33. */
E4 q p     /* p   — soft. E4 at velocity 49. */

/* Medium dynamics — balanced, neutral */
F4 q mp    /* mp  — moderately soft. F4 at velocity 64. */
G4 q mf    /* mf  — moderately loud (default). G4 at velocity 80. */

/* Loud dynamics — powerful, intense */
A4 q f     /* f   — loud. A4 at velocity 96. */
B4 q ff    /* ff  — very loud. B4 at velocity 112. */
C5 q fff   /* fff — maximum. C5 at velocity 127. */

/* This creates a gradual crescendo over 8 notes spanning
   3 dynamic levels (soft -> medium -> loud).
   Each subsequent note is played slightly louder. */

// Run from project root: py ep.py compile samples/v3-supported/basics/velocity_dynamics.e
