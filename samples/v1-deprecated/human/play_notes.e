/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v1 DEPRECATED — use v4 instead. See samples/v4-current/
   File:       play_notes.e
   Version:    v1 (human mode) — DEPRECATED
   Status:     DEPRECATED — v1 human mode. Use v4 instead.
   
   Human mode introduces readable note names, duration mnemonics,
   and velocity qualifiers instead of raw MIDI numbers.
   This file plays multiple individual notes using human-friendly syntax.

/* --- DEPRECATION NOTICE ---
   v1 human mode is deprecated. v4 provides a far richer human-readable
   syntax with @-directives, polyrhythms, and generative features.
   See samples/v4-current/ for the modern equivalent.
   ------------------------- */

/* "play note" tells the engine to emit a single note event.

   @dur   = duration qualifier. Values:
     :w   = whole note     = 4 beats
     :h   = half note      = 2 beats
     :q   = quarter note   = 1 beat
     :e   = eighth note    = 1/2 beat
     :s   = sixteenth note = 1/4 beat
     :t   = thirty-second  = 1/8 beat

   @vel   = velocity (volume) qualifier. Values:
     :ppp = pianississimo   = very very soft
     :pp  = pianissimo      = very soft
     :p   = piano           = soft
     :mp  = mezzo-piano     = moderately soft
     :mf  = mezzo-forte     = moderately loud
     :f   = forte           = loud
     :ff  = fortissimo      = very loud
     :fff = fortississimo   = very very loud
*/

play note(C4) @dur:q @vel:mf   /* C4, quarter note, moderately loud */
play note(D4) @dur:q @vel:mf   /* D4, quarter note, moderately loud */
play note(E4) @dur:q @vel:mf   /* E4, quarter note, moderately loud */
play note(F4) @dur:q @vel:mf   /* F4, quarter note, moderately loud */
play note(G4) @dur:h @vel:f    /* G4, half note, loud (climax) */
play note(A4) @dur:q @vel:mf   /* A4, quarter note */
play note(B4) @dur:e @vel:mp   /* B4, eighth note, slightly softer (passing tone) */
play note(C5) @dur:w @vel:ff   /* C5, whole note, very loud (final held note) */

/* Note naming convention:
   C4 = middle C (MIDI 60)
   D4 = D above middle C (62)
   B4 = B above middle C (71)
   C5 = one octave above middle C (72)
   Accidentals use # and b: C#4, Db4, etc. */

// Run from project root: py ep.py compile samples/v1-deprecated/human/play_notes.e
