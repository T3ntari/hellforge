/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v1 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       melody.e
   Version:    v1 (machine mode) — DEPRECATED
   Status:     DEPRECATED — v1 machine mode. Use v4 instead.
   
   A simple ascending and descending scale melody in machine mode.
   Each line demonstrates a different aspect of v1 numeric token syntax.

/* --- DEPRECATION NOTICE ---
   This file uses the legacy v1 machine mode token set.
   All v1 tokens (T, N, D, V) are deprecated in favor of v4's
   expressive @-directive and human-readable syntax.
   Please see samples/v4-current/ for the modern equivalent.
   ------------------------- */

/* T0    = Tempo tick base. T0 means 120 BPM default timing grid.
   N60   = MIDI note 60 = C4 (middle C). N62 = D4, N64 = E4, N65 = F4, etc.
   D     = Duration in ticks. D250 = quarter note at default tempo.
   V     = Velocity (0-127). V90 = moderately loud (mf). */
T0 N60 D250 V90   /* C4 — first note, the tonic */
T0 N62 D250 V90   /* D4 — step up to supertonic */
T0 N64 D250 V90   /* E4 — mediant */
T0 N65 D250 V90   /* F4 — subdominant */
T0 N67 D250 V90   /* G4 — dominant */
T0 N69 D250 V90   /* A4 — submediant */
T0 N71 D250 V90   /* B4 — leading tone */
T0 N72 D250 V90   /* C5 — octave, the climax */

/* Now descend back down with slightly different durations. */
T0 N72 D500 V80   /* C5 — longer duration (half note equivalent) */
T0 N71 D250 V80   /* B4 */
T0 N69 D250 V80   /* A4 */
T0 N67 D250 V80   /* G4 */
T0 N65 D250 V80   /* F4 */
T0 N64 D250 V80   /* E4 */
T0 N62 D250 V80   /* D4 */
T0 N60 D500 V80   /* C4 — final tonic, held longer */

/* Melody structure: 16-note ascending/descending scale.
   Ascending: quarter notes at V90 (loud).
   Descending: quarter notes at V80 (slightly softer) with a held final note. */

// Run from project root: py ep.py compile samples/v1-deprecated/machine/melody.e
