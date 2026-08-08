/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       probability.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates HELLFORGE's probabilistic (aleatoric) composition.
   The @prob directive sets a probability (0.0 to 1.0) that each
   note will actually play. This creates chance-based music where
   every run produces a different result.

/* @bpm 120 — A moderate tempo. */
@bpm 120

/* @prob 0.5 — Sets a 50% probability for each subsequent note.
   Each note has an independent 50% chance of sounding.
   This means roughly half the notes will play on any given run.
   
   @prob syntax:
     @prob 1.0  = 100% — all notes play (deterministic, default)
     @prob 0.75 = 75%  — most notes play
     @prob 0.5  = 50%  — half the notes play
     @prob 0.25 = 25%  — sparse
     @prob 0.0  = 0%   — nothing plays (silence)

   The random seed is based on system time by default,
   so each run sounds different. */
@prob 0.5

/* 16 notes, each has 50% chance to play.
   On average 8 notes will sound per run, but the exact set
   and rhythm are randomized — creating aleatoric (chance) music. */
C4 e
D4 e
E4 e
F4 e
G4 e
A4 e
B4 e
C5 e
C5 e
B4 e
A4 e
G4 e
F4 e
E4 e
D4 e
C4 e

/* Reset probability to 100% for the final deterministic note. */
@prob 1.0

/* Final chord — always plays, giving the piece a consistent ending
   regardless of the randomized middle section. */
play chord(C, major) @dur:w @vel:ff

/* @prob creates:
   - Aleatoric music (Cage, Feldman)
   - Generative background textures
   - "Broken" rhythms that feel more human
   - Dynamic variation between performances
   - Sparse or pointillistic textures

   Each playback is unique — like a musical "snowflake." */

// Run from project root: py ep.py compile samples/v4-current/generative/probability.e
