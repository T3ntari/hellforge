/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v1 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       play_chords.e
   Version:    v1 (human mode) — DEPRECATED
   Status:     DEPRECATED — v1 human mode. Use v4 instead.
   
   Demonstrates chord construction in v1 human mode using the
   "play chord(name, quality)" syntax. Three different chord types:
   major, minor, and dominant 7th.

/* --- DEPRECATION NOTICE ---
   v1 chord syntax is superseded by v4's richer harmonic engine.
   v4 supports extended chords (maj7, min7, dim, aug, sus2, sus4),
   inversions, voicings, and arpeggiation modes.
   ------------------------- */

/* Chord quality suffixes:
   major  = I, III, V   — e.g., C major = C E G
   minor  = i, IIIb, V  — e.g., A minor = A C E
   dom7   = I, III, V, VIIb — e.g., G7 = G B D F

   @dur = duration for the entire chord (all notes play simultaneously).
   @vel = velocity applied to all notes in the chord.
*/

/* C major chord (I — tonic) — bright, stable.
   Notes: C E G (MIDI 60, 64, 67). */
play chord(C, major) @dur:w @vel:mf

/* F major chord (IV — subdominant) — warm, expansive.
   Notes: F A C (MIDI 65, 69, 72). */
play chord(F, major) @dur:w @vel:mf

/* G dominant 7th chord (V7 — dominant) — tense, wants to resolve.
   Notes: G B D F (MIDI 67, 71, 74, 77). */
play chord(G, dom7) @dur:w @vel:mf

/* C major chord again (I — tonic resolution) — the V7 resolves here.
   Classic I-IV-V-I progression in C major. */
play chord(C, major) @dur:w @vel:mf

/* A minor chord — relative minor of C major, sad/contemplative.
   Notes: A C E (MIDI 69, 72, 76). */
play chord(A, minor) @dur:w @vel:mp

/* Chord vocabulary:
   Major intervals: root + major 3rd (4 semitones) + perfect 5th (7 semitones).
   Minor intervals: root + minor 3rd (3 semitones) + perfect 5th (7 semitones).
   Dom7 adds: minor 7th (10 semitones) above root. */

// Run from project root: py ep.py compile samples/v1-deprecated/human/play_chords.e
