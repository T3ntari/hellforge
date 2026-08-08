/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       rhythm_layers.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates v4's polyrhythmic layering — two simultaneous rhythms
   with different time signatures playing concurrently.
   Polyrhythms are a hallmark of v4 and enable complex, organic grooves.

/* @bpm 120 — Base tempo. Both polyrhythms will align to this grid. */
@bpm 120

/* 3:2 — Polyrhythmic ratio: 3 beats in the time of 2.
   Syntax: <count>:<beats> Note Duration
   This means: play 3 evenly-spaced C4 eighth notes
   in the time it normally takes to play 2 eighth notes.

   The result is a 3-over-2 cross-rhythm (hemiola).
   Common in African and Latin music — creates a "rolling" feel. */
3:2 C4 e

/* C4 q — Simultaneous quarter note on the same pitch.
   While the polyrhythm plays 3:2 eighth notes above,
   this line plays steady quarter notes.

   In v4, all lines execute concurrently unless sequentally ordered.
   The engine schedules both rhythms on the same timeline.

   Polyrhythm combinations:
     3:2  = 3 against 2 (triplet feel against duple)
     4:3  = 4 against 3
     5:4  = 5 against 4
     6:5  = 6 against 5

   Each creates a unique rhythmic tension that resolves
   when both cycles align again (every LCM of the ratios). */
C4 q

/* Note: In a real composition, you'd assign different channels/pitches
   to each polyrhythm layer so they're audibly distinct.
   See polyrhythm_complex.e in generative/ for more examples. */

// Run from project root: py ep.py compile samples/v4-current/basics/rhythm_layers.e
