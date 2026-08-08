/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// movement1.e  —  Allegro con Brio
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// First movement of the suite — bright, fast, energetic.
// Sonata-allegro form: Exposition, Development, Recapitulation.
// Run from project root: py ep.py compile examples/projects/parts/movement1.e
// ====================================================================

@bpm 120                                // Allegro tempo
@sig 4/4

// -------------------------------------------------------------------
// EXPOSITION — Theme 1 (bars 1–16)
// -------------------------------------------------------------------
section "Exposition — Theme 1"

for $i 0 to 15
  play C4 E4 G4 C5                      // C major fanfare
  @vel 80 + sin($i * 0.5) * 10
  wait 1/2

  play G3 B3 D4 G4                      // G major — dominant statement
  @vel 75 + cos($i * 0.3) * 8
  wait 1/2

  play A3 C4 E4 A4                      // A minor sequential
  @vel 70
  wait 1/2

  play F3 A3 C4 F4                      // F major — closing
  @vel 78
  wait 1/2
end

// -------------------------------------------------------------------
// EXPOSITION — Theme 2 (bars 17–24)
// -------------------------------------------------------------------
section "Exposition — Theme 2"

@vel 65                                 // Softer second theme

for $i 0 to 7
  play G4 1.0
  play E4 0.5
  play F4 0.5
  play G4 1.0
  play A4 1.0
  play B4 1.0
  play G4 1.0
  wait 1
end

// -------------------------------------------------------------------
// DEVELOPMENT (bars 25–40)
// -------------------------------------------------------------------
section "Development"

polyrhythm 5:4
@vel 70 to 95 arc

for $i 0 to 15
  play D3 F3 A3 D4                      // D minor — fragmentation
  wait 1/2
  play E3 G3 B3 E4                      // E minor — sequence
  wait 1/2
  play F3 A3 C4 F4                      // F major — false recapitulation
  wait 1/2
  play B2 D3 F3 B3                      // Bdim — tension
  wait 1/2
end

// -------------------------------------------------------------------
// RECAPITULATION (bars 41–56)
// -------------------------------------------------------------------
section "Recapitulation"

@vel 85                                 // Return of theme, triumphant

for $i 0 to 15
  play C4 E4 G4 C5                      // Theme 1 in home key
  @vel 82 + sin($i * 0.7) * 12
  wait 1/2
  play G3 B3 D4 G4
  wait 1/2
  play A3 C4 E4 A4
  wait 1/2
  play G3 B3 D4 G4                      // Ends on dominant
  wait 1/2
end

// -------------------------------------------------------------------
// CODA (bars 57–60)
// -------------------------------------------------------------------
section "Coda"

play C3 E3 G3 C4 E4 G4 C5 E5 G5        // Final C major chord
@vel 100
wait 4

// End of movement 1 — 60 bars
