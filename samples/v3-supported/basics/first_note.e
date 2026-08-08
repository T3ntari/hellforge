/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       first_note.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   The simplest possible v3 program: a single note with a duration.
   v3 consolidated v1's machine mode and v2's human mode into a unified
   syntax where "Note Duration" is the fundamental unit.

/* --- SUPPORT STATUS ---
   v3 is the current stable consolidated engine.
   All v3 features are fully supported and will remain compatible
   with v4 (v4 is a superset of v3).
   ------------------------- */

/* C4 q
   ^^ ^
   |  |
   |  +-- Duration code: q = quarter note (1 beat)
   |
   +----- Note name: C4 = middle C (MIDI 60)

   This single token tells the engine:
   "Play C4 for the length of one quarter note at default velocity."

   Duration codes:
     w = whole note    (4 beats)
     h = half note     (2 beats)
     q = quarter note  (1 beat)
     e = eighth note   (1/2 beat)
     s = sixteenth note(1/4 beat)
     t = thirty-second (1/8 beat)
*/
C4 q

/* Default velocity is 80 (mf) unless overridden.
   Default tempo is 120 BPM unless @bpm is set. */

// Run from project root: py ep.py compile samples/v3-supported/basics/first_note.e
