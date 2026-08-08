/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// .ei project index — multi-file composition
   File:       parts/verse.e
   Version:    v4 (part file) — inherited by simple_project.ei
   Status:     CURRENT STANDARD
   
   Part file for the verse section of simple_project.ei.
   This follows the intro and provides the main melodic content.

/* Verse melody: a lyrical phrase in the same key (C major).
   Tempo is inherited from the parent .ei project (120 BPM). */

/* Melodic phrase 1. */
C4 q
D4 q
E4 h
F4 q
G4 q
A4 h

/* Melodic phrase 2 — slightly different, building tension. */
G4 q
F4 q
E4 q
D4 q
C4 w

/* Bridge-like transition back to the intro material. */
G4 e
A4 e
B4 e
C5 e
D5 q
C5 q
B4 q
C5 w

/* Verse structure: two 4-bar phrases with a transitional ending.
   This part is inherited and sequenced after the intro. */

// Run from project root: py ep.py compile samples/ei/parts/verse.e
