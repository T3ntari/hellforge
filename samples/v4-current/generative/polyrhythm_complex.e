/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       polyrhythm_complex.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates multiple simultaneous polyrhythms in v4.
   Three different polyrhythmic ratios play concurrently on different
   pitches, creating a rich, layered rhythmic tapestry.

/* @bpm 100 — Base tempo. All polyrhythms are relative to this.
   The engine schedules all three layers independently on the same timeline. */
@bpm 100

/* Layer 1: 3:2 — Three beats in the time of two.
   On channel 0 (piano), playing C4.
   This creates a triplet-against-duple cross rhythm.
   Pattern: X . X . X . (felt against a steady 2-beat pulse)

   3:2 is one of the most common polyrhythms, known as "hemiola."
   It appears in West African drumming, Brazilian samba, and jazz. */
CH0 3:2 C4 e

/* Layer 2: 4:3 — Four beats in the time of three.
   On channel 1 (strings/pad), playing G3.
   This is slower and more complex — 4 evenly-spaced notes
   in the space of 3 eighth notes.

   Combined with the 3:2 layer, the composite rhythm is:
   3:2 (on C4) + 4:3 (on G3) = intricate cross-rhythmic texture. */
CH1 4:3 G3 e

/* Layer 3: 5:4 — Five beats in the time of four.
   On channel 2 (bass), playing C3.
   Five even notes in the space of four creates a quintuplet feel.

   All three polyrhythms together:
   3:2 (fastest) + 4:3 (medium) + 5:4 (slowest)
   = a complex rhythmic fabric with three distinct pulse layers. */
CH2 5:4 C3 e

/* Each polyrhythm is on a different channel and pitch,
   making them clearly audible as separate layers.
   The channels can have different MIDI programs/instruments
   for even greater clarity.

   Polyrhythm resolution timing:
   The 3:2 cycle repeats every 2 beats (lowest LCM = 6).
   The 4:3 cycle repeats every 3 beats (LCM = 12).
   The 5:4 cycle repeats every 4 beats (LCM = 20).
   All three align every LCM(6,12,20) = 60 beats. */

// Run from project root: py ep.py compile samples/v4-current/generative/polyrhythm_complex.e
