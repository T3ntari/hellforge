/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       repeat_pattern.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates the repeat loop — a simplified loop for repeating
   a fixed block of notes a specific number of times.

/* repeat N { body } — Repeats the body exactly N times.
   Unlike for, there's no loop variable — just pure repetition.
   Useful for ostinatos, drum loops, and repeated phrases. */

/* repeat 4 { ... } — Play this 4-note pattern 4 times (= 16 notes total).
   The pattern C4 e D4 e E4 e F4 e is a chromatic climb
   that sounds like a classic rock or boogie-woogie riff. */
repeat 4 {
    C4 e     /* Eighth note C4 — first note of the pattern */
    D4 e     /* Eighth note D4 — step up */
    E4 e     /* Eighth note E4 — step up */
    F4 e     /* Eighth note F4 — step up */
}

/* After the repeat finishes, play a resolution.
   The pattern goes C-D-E-F four times, then resolves to G (dominant)
   and back to C (tonic). */
G4 q     /* G quarter note — pause point */
C4 w     /* C whole note — final resolution */

/* Repeat vs For:
   - Use "repeat" when you just need N identical repetitions.
   - Use "for" when you need a counter variable ($i, $j, etc.).

   repeat 8 { C4 e } — 8 identical C4 eighth notes (steady pulse).
   for $i = 0 to 7 { N{60 + $i} e } — ascending scale, each note different. */

// Run from project root: py ep.py compile samples/v3-supported/loops/repeat_pattern.e
