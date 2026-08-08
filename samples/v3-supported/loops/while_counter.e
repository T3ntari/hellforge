/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       while_counter.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates the while loop with a manual counter variable.
   while loops provide more flexible control than for/repeat
   because the condition can be any boolean expression.

/* $i = 0 — Initialize the counter variable to 0.
   Variables used in while must be initialized before the loop. */
$i = 0

/* while $i < 8 { ... } — Continue looping as long as $i is less than 8.
   The condition ($i < 8) is checked at the start of each iteration.
   If false initially, the body never executes. */
while $i < 8 {
    /* C4 q — Play middle C as a quarter note.
       All 8 iterations play the same note, creating a steady pulse. */
    C4 q

    /* $i = $i + 1 — Increment the counter.
       IMPORTANT: Without this increment, the loop would run forever!
       Always update your counter inside the loop body. */
    $i = $i + 1
}

/* After the while loop, $i equals 8 (the condition $i < 8 is now false).
   The loop ran exactly 8 times: $i = 0,1,2,3,4,5,6,7. */

/* Using $i inside the body for musical variation: */
$i = 0
while $i < 8 {
    /* Note choice changes with $i — ascending scale fragment.
       V{80 - $i * 5} — velocity decreases each iteration (decrescendo). */
    T0 N{60 + $i * 2} D200 V{80 - $i * 5}
    $i = $i + 1
}

/* While loops are more powerful than for loops because:
   - Condition can be any expression ($i < 10 and $done == 0).
   - Counter can change by any amount ($i = $i + 2 for step 2).
   - Can have multiple exit conditions. */

// Run from project root: py ep.py compile samples/v3-supported/loops/while_counter.e
