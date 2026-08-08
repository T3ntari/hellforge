/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// 01_prelude.e  —  "Prelude in C"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Track 1 of opus1.enx. A gentle prelude in C major.
// Slow arpeggiated chords with delicate ornamentation.
// Run from project root: py ep.py compile examples/albums/tracks/01_prelude.e
// ====================================================================

@bpm 80                                 // Gentle, walking pace
@sig 4/4                                // Common time

// -------------------------------------------------------------------
// SECTION 1 — Arpeggiated Chords (bars 1–16)
// Broken C major chords spanning the keyboard, pp to mp
// -------------------------------------------------------------------
section "Arpeggios"

for $i 0 to 15
  play C3 0.25
  @vel 35 + ($i * 1.5)
  play E3 0.25
  play G3 0.25
  play C4 0.25
  play E4 0.25
  play G4 0.25
  play C5 0.25
  play B4 0.25
  play G4 0.25
  play E4 0.25
  play C4 0.25
  play G3 0.25
  play E3 0.25
  wait 0.25
  wait 0.25
end

// -------------------------------------------------------------------
// SECTION 2 — Melody Emerges (bars 17–24)
// A simple soprano melody floats above the arpeggios
// -------------------------------------------------------------------
section "Melody"

for $i 0 to 7
  play C4 E4 G4 C5 E5 G5               // Full arpeggio chord
  @vel 50
  wait 1

  play E4 G4 B4 E5                      // Em — slight turn
  @vel 45
  wait 1

  play F4 A4 C5 F5                      // Fmaj7
  @vel 52
  wait 1

  play G4 B4 D5 G5                      // G7 — building
  @vel 48
  wait 1
end

// -------------------------------------------------------------------
// SECTION 3 — Closing (bars 25–32)
// Return to C, gentle decrescendo
// -------------------------------------------------------------------
section "Closing"

@vel 50 to 30 arc decrescendo

for $i 0 to 7
  play C3 G3 C4 E4 G4 C5               // C major — home
  wait 1
end

play C3 C4 E4 G4 C5                     // Final chord, held
@vel 25
wait 8                                  // Let ring to silence

// End of Prelude — 32 bars
