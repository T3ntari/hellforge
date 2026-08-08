/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// .ei project index — multi-file composition
   File:       parts/intro.e
   Version:    v4 (part file) — inherited by simple_project.ei
   Status:     CURRENT STANDARD
   
   Part file for the intro section of simple_project.ei.
   This file is not meant to be compiled standalone — it's inherited
   by the parent .ei project file.
   
   Part files contain self-contained musical sections that can be
   reused across multiple projects.

/* Intro melody: a short, ascending phrase that sets the mood.
   No @bpm here — the parent .ei (simple_project.ei) sets the global tempo. */

/* A gentle rising arpeggio in C major. */
C4 q
E4 q
G4 q
C5 h

/* Brief descending return. */
B4 e
G4 e
E4 q
C4 h

/* Intro structure: 4 bars of arpeggiated C major.
   This part is inherited and sequenced before the verse. */

// Run from project root: py ep.py compile samples/ei/parts/intro.e
