/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       chord_progression.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates chord progression using the "play chord" directive.
   The classic I-IV-V-I progression in C major, with an added
   vi (A minor) for emotional color — making it I-vi-IV-V-I.

/* "play chord(name, quality)" — Emits all notes of the chord simultaneously.
   Quality options: major, minor, dom7, maj7, min7, dim, aug, sus2, sus4.

   @dur — duration applied to all chord notes.
   @vel — velocity applied to all chord notes.
*/

/* I — C major (C E G). The tonic chord.
   Root position: C as the lowest note. */
play chord(C, major) @dur:h @vel:mf

/* vi — A minor (A C E). The relative minor, adds melancholy.
   This is a common substitute for the tonic. */
play chord(A, minor) @dur:h @vel:mf

/* IV — F major (F A C). The subdominant, bright and expansive. */
play chord(F, major) @dur:h @vel:mf

/* V — G dominant 7 (G B D F). Creates strong tension wanting resolution.
   The dom7 quality adds extra pull back to the tonic. */
play chord(G, dom7) @dur:h @vel:mf

/* I — C major again. The V7 resolves here — the tension releases.
   Final chord, held as a whole note for a conclusive ending. */
play chord(C, major) @dur:w @vel:ff

/* This progression (I-vi-IV-V7-I) is one of the most common
   in Western popular music — used in thousands of songs.

   Roman numeral analysis:
     I   = C major  (tonic)
     vi  = A minor  (submediant)
     IV  = F major  (subdominant)
     V7  = G7       (dominant 7th)
     I   = C major  (tonic — resolution) */

// Run from project root: py ep.py compile samples/v3-supported/chords/chord_progression.e
