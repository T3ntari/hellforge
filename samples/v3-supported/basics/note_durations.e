/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       note_durations.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates all six duration codes in v3 syntax.
   Each note is pitched differently so you can hear the duration clearly.
   Durations are relative to the tempo (default 120 BPM).

/* Duration codes from longest to shortest:

   w  = whole note     = 4 beats     — longest standard duration
   h  = half note      = 2 beats     — half of whole
   q  = quarter note   = 1 beat      — default/reference duration
   e  = eighth note    = 1/2 beat    — half of quarter
   s  = sixteenth note = 1/4 beat    — fast, runs
   t  = thirty-second  = 1/8 beat    — very fast, trill-like
*/

/* C4 w  — Whole note C4, rings for 4 full beats.
          Also called "semibreve" in classical notation. */
C4 w

/* D4 h  — Half note D4, rings for 2 beats.
          Also called "minim". */
D4 h

/* E4 q  — Quarter note E4, rings for 1 beat.
          Also called "crotchet". This is the most common duration. */
E4 q

/* F4 e  — Eighth note F4, rings for 1/2 beat.
          Also called "quaver". Two per beat. */
F4 e

/* G4 s  — Sixteenth note G4, rings for 1/4 beat.
          Also called "semiquaver". Four per beat. */
G4 s

/* A4 t  — Thirty-second note A4, rings for 1/8 beat.
          Also called "demisemiquaver". Eight per beat. */
A4 t

/* Duration ratio summary:
   w = 4 beats
   h = 2 beats
   q = 1 beat
   e = 0.5 beats
   s = 0.25 beats
   t = 0.125 beats

   At 120 BPM, 1 beat = 500ms.
   So C4 w = 2000ms, D4 h = 1000ms, E4 q = 500ms, etc. */

// Run from project root: py ep.py compile samples/v3-supported/basics/note_durations.e
