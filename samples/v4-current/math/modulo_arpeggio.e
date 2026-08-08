/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v4 CURRENT STANDARD — recommended for all new compositions
   File:       modulo_arpeggio.e
   Version:    v4 (unified engine) — CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   Uses modulo arithmetic ($i % 12) to generate a repeating sawtooth
   arpeggio pattern. The modulo operator creates octave-cycling behavior
   that maps naturally to musical pitch classes.

/* @bpm 180 — Faster tempo to make the arpeggio flow. */
@bpm 180

/* for $i = 0 to 23 — 24 iterations (two octaves worth of 12 semitones each).
   The loop counter $i controls every parameter of the note:
   time (T), pitch (N), and duration (D). */

for $i = 0 to 23 {
    /* T{$i * 50} — Time offset: each note is delayed by $i * 50 ticks.
       This creates a staggered, cascading entry rather than all at once.
       First note at 0 ticks, last at 1150 ticks (at 180 BPM ~ 2 seconds). */

    /* N{60 + $i % 12} — Note number:
       60 (C4) + ($i modulo 12).
       Modulo 12 creates a repeating pattern every 12 iterations:
         i=0:  N{60}  = C4
         i=1:  N{61}  = C#4
         i=2:  N{62}  = D4
         ...
         i=11: N{71}  = B4
         i=12: N{60}  = C4 (back to root, octave higher? No — same octave)
         i=13: N{61}  = C#4 (same pattern repeats)
       
       Result: a cycling arpeggio that climbs chromatically then wraps. */

    /* D40 — Short duration (40 ticks = ~133ms at 180 BPM).
       Staccato notes for a crisp, rhythmic arpeggio effect. */
    T{$i * 50} N{60 + $i % 12} D40
}

/* The modulo pattern creates a "sawtooth" pitch shape:
   /|/|/|/|/|/| — each tooth is 12 notes long.
   This is the foundation of many electronic music arpeggiators. */

/* Variation: try N{60 + $i % 7} for a diatonic (scale-based) arpeggio
   that only plays the 7 notes of a major scale pattern. */

// Run from project root: py ep.py compile samples/v4-current/math/modulo_arpeggio.e
