/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       var_update_loop.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Demonstrates updating a variable inside a while loop to create
   a gradually changing musical parameter. The variable $base starts
   at 60 (C4) and increases by 1 each iteration, creating an ascending
   chromatic line with changing durations and velocities.

/* @bpm 120 — Set tempo. */
@bpm 120

/* $base = 60 — Initialize the starting pitch to C4 (MIDI 60).
   This variable will be incremented inside the loop. */
$base = 60

/* while $base < 72 — Continue until $base reaches 72 (C5).
   The loop runs 12 times (notes: 60 through 71 = C4 through B4). */

while $base < 72 {
    /* N{$base} — Current value of $base.
       First iteration: N{60}  = C4
       Last iteration:  N{71}  = B4

       D{($base - 60) * 20 + 100} — Duration increases with pitch.
       First note: D100 (~200ms at 120 BPM)
       Last note:  D320 (~640ms) — getting gradually slower.

       V{$base + 10} — Velocity also increases.
       First note: V70  (mf-f)
       Last note:  V81  (just above mf) — slight crescendo. */
    T{($base - 60) * 200} N{$base} D{($base - 60) * 20 + 100} V{$base + 10}

    /* $base = $base + 1 — Increment the base pitch by 1 semitone.
       This is the critical update that moves the loop forward.
       Without this, the loop would run forever on the same note. */
    $base = $base + 1
}

/* After the loop, $base = 72 (the condition $base < 72 is now false).
   The loop produced a chromatic scale from C4 to B4 with:
   - Ascending pitch (linear)
   - Lengthening duration (ritardando)
   - Increasing velocity (crescendo)
   
   This demonstrates how a single variable can control multiple
   musical parameters simultaneously. */

// Run from project root: py ep.py compile samples/v4-current/loops/var_update_loop.e
