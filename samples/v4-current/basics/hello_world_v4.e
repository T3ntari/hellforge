/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       hello_world_v4.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   The simplest v4 program — the "Hello, World" of E.
   v4 unifies all previous syntaxes into a single expressive engine
   with @-directives, polyrhythms, and expression-based everything.

/* @bpm 120 — Sets the tempo to 120 beats per minute.
   @-directives are the primary configuration mechanism in v4.
   Unlike v1's T token or implicit defaults, @bpm is explicit and clear. */
@bpm 120

/* C4 q — A single note: C4 (middle C), quarter note duration.
   v4 retains the v3 Note-Duration core syntax while adding
   powerful new features around it.

   In v4, this note automatically uses the polyrhythmic engine
   with a default 1:1 ratio (no polyrhythm). */
C4 q

/* v4's key advancements over v3:
   1. @-directives for all configuration (bpm, mode, channel, etc.)
   2. Polyrhythmic syntax: ratio:count Note Duration (e.g., 3:2 C4 e)
   3. Euclidean rhythms: steps:beats (e.g., 5:8)
   4. Generative features: @prob, @curve
   5. Rich built-in functions and expression system
   6. Full backward compatibility with v3 syntax */

// Run from project root: py ep.py compile samples/v4-current/basics/hello_world_v4.e
