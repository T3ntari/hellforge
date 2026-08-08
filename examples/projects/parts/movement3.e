/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// movement3.e  —  Presto Furioso
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Third movement — blistering fast, virtuosic, relentless.
// Rondo form (ABACABA) with driving rhythmic energy.
// Run from project root: py ep.py compile examples/projects/parts/movement3.e
// ====================================================================

@bpm 160                                // Presto — very fast
@sig 2/4                                // Cut time, driving

// -------------------------------------------------------------------
// A REFRAIN — "The Chase" (bars 1–16)
// High-energy theme in C minor
// -------------------------------------------------------------------
section "A — Refrain"

for $i 0 to 15
  play C4 0.25
  @vel 90 + sin($i * 0.8) * 8
  play Eb4 0.25
  play G4 0.25
  play C5 0.25
  play B4 0.25
  play G4 0.25
  play Eb4 0.25
  play C4 0.25

  play C4 0.25
  play F4 0.25
  play A4 0.25
  play C5 0.25
  play B4 0.25
  play A4 0.25
  play G4 0.25
  play F4 0.25
end

// -------------------------------------------------------------------
// B EPISODE — "Lament" (bars 17–24)
// Contrasting lyrical episode in Ab major
// -------------------------------------------------------------------
section "B — Episode"

@vel 70                                 // Softer, lyrical

for $i 0 to 7
  play Ab4 0.5
  play C5 0.5
  play Bb4 0.5
  play Ab4 0.5
  play G4 0.5
  play F4 0.5
  play Eb4 0.5
  play C4 0.5
end

// -------------------------------------------------------------------
// A RETURN (bars 25–32)
// -------------------------------------------------------------------
section "A — Return"

@vel 90
for $i 0 to 7
  play C4 Eb4 G4 C5 B4 G4 Eb4 C4
  play C4 F4 A4 C5 B4 A4 G4 F4
end

// -------------------------------------------------------------------
// C EPISODE — "Tempest" (bars 33–48)
// Fugato passage with polyrhythmic layering
// -------------------------------------------------------------------
section "C — Tempest"

polyrhythm 5:4
@vel 85 to 105 arc                      // Crescendo through episode

for $i 0 to 15
  play G3 B3 D4 G4                      // G minor — stormy
  wait 0.25
  play A3 C4 E4 A4                      // Sequence rising
  wait 0.25
  play B3 D4 F4 B4                      // Bdim
  wait 0.25
  play C4 E4 G4 C5                      // C minor — peak
  wait 0.25
  play D4 F4 A4 D5                      // Sequence continues
  wait 0.25
  play Eb4 G4 Bb4 Eb5                   // Eb major — surprise
  wait 0.25
  play F4 A4 C5 F5                      // F minor
  wait 0.25
  play G4 Bb4 D5 G5                     // G dim
  wait 0.25
end

// -------------------------------------------------------------------
// A RETURN — "Recapitulation" (bars 49–56)
// -------------------------------------------------------------------
section "A — Recapitulation"

@vel 95
for $i 0 to 7
  play C4 Eb4 G4 C5 B4 G4 Eb4 C4
  play C4 F4 A4 C5 B4 A4 G4 F4
end

// -------------------------------------------------------------------
// B EPISODE RETURN (bars 57–64)
// -------------------------------------------------------------------
section "B — Episode Return"

@vel 75
for $i 0 to 7
  play Ab4 C5 Bb4 Ab4 G4 F4 Eb4 C4
end

// -------------------------------------------------------------------
// FINAL A — "Coda Prestissimo" (bars 65–80)
// Accelerating to the finish
// -------------------------------------------------------------------
section "Final A — Coda"

@tempo_curve 160 180 16                 // Push tempo to 180!
@vel 100 to 115 arc

for $i 0 to 15
  play C4 Eb4 G4 C5 B4 G4 Eb4 C4
  play F3 A3 C4 F4 E4 C4 A3 F3
  play G3 B3 D4 G4 F4 D4 B3 G3
  play C4 Eb4 G4 C5 B4 G4 Eb4 C4
end

// Final chord
play C3 Eb3 G3 C4 Eb4 G4 C5            // C minor — powerful finish
@vel 115
wait 4

// End of movement 3 — 80 bars
