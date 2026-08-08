/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v1 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       bare_minimum.e
   Version:    v1 (machine mode) — DEPRECATED
   Status:     DEPRECATED — v1 machine mode. Use v4 instead.
   
   This is the absolute minimum valid E program in original machine mode.
   Machine mode uses numeric tokens exclusively: T (tick/tempo), N (note),
   D (duration), V (velocity).

/* --- DEPRECATION NOTICE ---
   WARNING: v1 machine mode is deprecated as of HELLFORGE v4.
   All v1 features have been superseded by v4's unified engine.
   Please migrate to v4 syntax (see samples/v4-current/).
   ------------------------- */

/* T0   = Set tempo to 0 (default tempo, 120 BPM equivalent in v1 timing).
   N60  = Play MIDI note number 60 (middle C, C4).
   D500 = Hold the note for 500 ticks (duration).
   V100 = Set velocity (volume) to 100 out of 127. */
T0 N60 D500 V100

// Run from project root: py ep.py compile samples/v1-deprecated/machine/bare_minimum.e
