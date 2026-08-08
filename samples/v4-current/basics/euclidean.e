/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       euclidean.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates Euclidean rhythms in v4.
   Euclidean rhythms distribute N beats as evenly as possible
   across M steps — creating natural-sounding, non-uniform patterns.

/* @bpm 120 — Tempo setting.
   Note: @bpm is optional; v4 defaults to 120 BPM if omitted. */
@bpm 120

/* 5:8 — Euclidean rhythm: 5 beats in 8 steps.
   Syntax: <beats>:<steps> Note Duration

   This generates the pattern: [1 0 1 0 1 1 0 1]
   where 1 = play, 0 = rest.
   5 beats are spread as evenly as possible across 8 positions.

   At the eighth-note level, this creates a syncopated groove
   similar to a 5/8 time signature accent pattern. */
5:8 C4 e

/* 3:4 — Another Euclidean pattern: 3 beats in 4 steps.
   Pattern: [1 0 1 1].
   Simpler and more regular — a basic tresillo pattern
   common in Cuban and Latin music. */
3:4 D4 e

/* 7:12 — Complex Euclidean: 7 beats in 12 steps.
   Pattern: [1 0 1 1 0 1 0 1 1 0 1 0].
   Irregular and intricate — great for percussion grooves. */
7:12 E4 e

/* Euclidean rhythm properties:
   - All beats are as evenly spaced as possible.
   - No beat clustering — maximally distributed.
   - Patterns repeat every M steps.
   - Many world music rhythms are Euclidean (e.g., 3:4 = tresillo,
     5:8 = typical Afro-Cuban, 5:16 = Egyptian).

   Use Euclidean rhythms for:
   - Percussion/drum patterns
   - Arpeggio accent patterns
   - Bass note syncopation
   - Rhythmic harmonic changes */

// Run from project root: py ep.py compile samples/v4-current/basics/euclidean.e
