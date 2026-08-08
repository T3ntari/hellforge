/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       scale_calc.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Uses expression math to construct a musical scale.
   Rather than hardcoding note numbers, we start from $base = 60 (C4)
   and add intervals to build a C major scale.

/* $base = 60 — The root note. MIDI 60 = C4 (middle C).
   All scale degrees are computed relative to this base. */
$base = 60

/* C major scale intervals (in semitones) from root:
   Degree | Interval | Note
   I      | 0        | C   (root)
   II     | 2        | D
   III    | 4        | E
   IV     | 5        | F
   V      | 7        | G
   VI     | 9        | A
   VII    | 11       | B
   VIII   | 12       | C (octave)
*/

/* Each line plays one scale degree at the computed MIDI note number.
   The duration D250 is a quarter note at 120 BPM. */
T0 N{$base + 0}  D250 V90   /* C4 — tonic (root)          */
T0 N{$base + 2}  D250 V90   /* D4 — supertonic            */
T0 N{$base + 4}  D250 V90   /* E4 — mediant               */
T0 N{$base + 5}  D250 V90   /* F4 — subdominant           */
T0 N{$base + 7}  D250 V90   /* G4 — dominant              */
T0 N{$base + 9}  D250 V90   /* A4 — submediant            */
T0 N{$base + 11} D250 V90   /* B4 — leading tone          */
T0 N{$base + 12} D250 V90   /* C5 — octave (8va)         */

/* To play a different scale, just change $base:
   $base = 65 would transpose to F major.
   $base = 57 would transpose to A major.

   The interval formula stays the same regardless of root,
   making this a reusable scale pattern. */

// Run from project root: py ep.py compile samples/v3-supported/math/scale_calc.e
