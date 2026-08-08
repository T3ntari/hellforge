/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       var_expr.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates variable assignment and inline expressions in v3.
   Variables use $ prefix. Expressions use {$expr} interpolation syntax.
   This is the foundation of procedural music generation in HELLFORGE.

/* $bpm = 120 — Declare a variable named $bpm and assign it the value 120.
   Variables are integers by default and can be used anywhere
   a numeric value is expected via {$variable} or {$expression}. */
$bpm = 120

/* T{$bpm * 2} — Inline expression using { } brackets.
   This evaluates to T{240}, which sets the tempo to 240 BPM
   (double the base tempo — a "double-time feel").
   The $bpm variable is multiplied by 2 at compile time. */
T{$bpm * 2}

/* N60 — Play MIDI note 60 (C4) at the new doubled tempo.
   Using a raw numeric token alongside expressions is fine. */
N60 D100

/* N{$bpm + 20} — Expression evaluates to N{140}.
   This would be MIDI note 140 — very high, but demonstrates
   how variables can produce note numbers.
   In practice, keep note numbers within 0-127. */
T{$bpm / 2} N{$bpm + 20} D200

/* Expressions support arithmetic operators:
   +   addition
   -   subtraction
   *   multiplication
   /   integer division
   %   modulo (remainder)
   ( ) grouping

   Variable scope: $ variables are global within a single .e file.
   Reassignment is allowed: $bpm = $bpm + 10 would increase by 10. */

// Run from project root: py ep.py compile samples/v3-supported/math/var_expr.e
