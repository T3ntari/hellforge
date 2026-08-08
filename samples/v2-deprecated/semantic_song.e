/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v2 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       semantic_song.e
   Version:    v2 (semantic mode) — DEPRECATED
   Status:     DEPRECATED — v2 semantic mode. Use v4 instead.
   
   A complete short song written entirely in v2 semantic syntax.
   Uses sections, keys, arpeggios, and chromatic runs to build
   a coherent musical piece with intro-verse-chorus structure.

/* --- DEPRECATION NOTICE ---
   v2 is deprecated. For equivalent v4 generative songwriting,
   see samples/v4-current/generative/ and v4-current/loops/.
   ------------------------- */

/* [Section: Intro] — Opening section, sets the mood.
   Tempo is implicit at default 120 BPM. */
[Section: Intro]

Key: C_Major

/* A gentle rising arpeggio to introduce the key. */
arpeggio(C3, E3, G3, C4)

/* A second arpeggio filling out the harmony. */
arpeggio(E3, G3, B3, D4)

/* [Section: Verse] — Main melodic content begins. */
[Section: Verse]

Key: C_Major

/* Verse phrase 1: stepwise arpeggio movement. */
arpeggio(C4, E4, G4)
arpeggio(D4, F4, A4)
arpeggio(E4, G4, B4)
arpeggio(F4, A4, C5)

/* Chromatic climb to build tension into the chorus. */
chromatic_run(C4, G4)

/* [Section: Chorus] — Higher energy, brighter key feel. */
[Section: Chorus]

Key: G_Major

/* Brighter arpeggios in G major — the dominant key adds energy. */
arpeggio(G3, B3, D4, G4)
arpeggio(C4, E4, G4, C5)
arpeggio(D4, F#4, A4, D5)
arpeggio(G3, B3, D4, G4)

/* [Section: Outro] — Resolution and fade. */
[Section: Outro]

Key: C_Major

/* Return to tonic key with a gentle descending arpeggio. */
arpeggio(C5, G4, E4, C4)

/* Final sustained arpeggio — the last chord rings out. */
arpeggio(C3, E3, G3, C4)

/* Song structure: Intro (4 bars) -> Verse (8 bars) -> Chorus (8 bars) -> Outro (4 bars).
   Standard pop/rock form adapted for v2 semantic syntax. */

// Run from project root: py ep.py compile samples/v2-deprecated/semantic_song.e
