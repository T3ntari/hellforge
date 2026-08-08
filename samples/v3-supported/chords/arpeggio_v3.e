/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       arpeggio_v3.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates arpeggiated chords using the @mode:arpeggio directive.
   Instead of playing all chord notes at once, arpeggio mode plays
   them sequentially, creating a "broken chord" effect.

/* @mode:arpeggio — Switches the engine to arpeggio mode.
   In this mode, "play chord" emits notes in sequence (up-down pattern)
   rather than simultaneously.
   
   The arpeggio pattern is:
   Root -> Third -> Fifth -> Octave -> Fifth -> Third -> Root
   (up then down, creating a classic arpeggio shape). */

@mode:arpeggio

/* C major arpeggio. With @mode:arpeggio, the notes C-E-G-C
   are played one at a time in rapid succession.
   @dur:e plays each arpeggio note as an eighth note. */
play chord(C, major) @dur:e @vel:mf

/* A minor arpeggio. Notes: A-C-E-A played sequentially.
   The arpeggio pattern repeats for each chord. */
play chord(A, minor) @dur:e @vel:mf

/* F major arpeggio. Notes: F-A-C-F. */
play chord(F, major) @dur:e @vel:mf

/* G major arpeggio (as a transition back). Notes: G-B-D-G. */
play chord(G, major) @dur:e @vel:mf

/* Turn off arpeggio mode for a final block chord. */
@mode:normal

/* C major block chord — all notes at once, held for a whole note.
   Notice the contrast between the flowing arpeggios above
   and this solid final chord. */
play chord(C, major) @dur:w @vel:ff

/* @mode directive toggles:
   @mode:normal    — default, chords play simultaneously
   @mode:arpeggio  — chords play as arpeggios (sequential)
   @mode:roll      — chords play as a fast roll (harp-like)

   Arpeggio speed is determined by the @dur value of the chord.
   @dur:e = eighth note per arpeggio note = faster
   @dur:q = quarter note per arpeggio note = slower/more deliberate */

// Run from project root: py ep.py compile samples/v3-supported/chords/arpeggio_v3.e
