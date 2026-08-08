/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v2 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       semantic_basics.e
   Version:    v2 (semantic mode) — DEPRECATED
   Status:     DEPRECATED — v2 semantic mode. Use v4 instead.
   
   v2 introduced semantic constructs: sections, key signatures, and
   built-in musical functions (arpeggio, chromatic run, etc.).
   This file demonstrates the core v2 semantic vocabulary.

/* --- DEPRECATION NOTICE ---
   v2 semantic mode is deprecated. v4's engine subsumes all v2 features
   with greater flexibility, polyrhythmic support, and generative tools.
   ------------------------- */

/* [Section: Intro] — Marks the beginning of the Intro section.
   Sections help organize song structure and can be looped or jumped to. */
[Section: Intro]

/* Key: C_Major — Sets the harmonic context to C major.
   All subsequent note/chord operations default to this key.
   Available keys: C_Major, G_Major, D_Major, A_Major, E_Major,
   A_Minor, E_Minor, etc. */
Key: C_Major

/* arpeggio(C4, G4, D5) — Plays the notes C4, G4, D5 as an arpeggio
   (one after another) rather than simultaneously.
   Each note is spaced evenly within the default tempo grid. */
arpeggio(C4, G4, D5)

/* chromatic_run(C4, C5) — Plays every semitone from C4 to C5
   in ascending order (12 notes: C4, C#4, D4, D#4, ..., B4, C5).
   Useful for transitions, build-ups, or tension. */
chromatic_run(C4, C5)

/* [Section: Verse] — Transition to Verse section. */
[Section: Verse]

/* arpeggio(F3, A3, C4, E4) — A broader arpeggio spanning 2 octaves.
   C major 7 arpeggio (Fmaj7 in second inversion context). */
arpeggio(F3, A3, C4, E4)

/* Key: A_Minor — Modulate to the relative minor key.
   Key changes can happen mid-song for emotional contrast. */
Key: A_Minor

/* arpeggio(A3, C4, E4) — A minor arpeggio (A-C-E).
   Different quality than the earlier major arpeggios. */
arpeggio(A3, C4, E4)

/* Chromatic movements create tension; arpeggios create harmony.
   v2 semantic functions abstract away individual note tokens
   into higher-level musical intent. */

// Run from project root: py ep.py compile samples/v2-deprecated/semantic_basics.e
