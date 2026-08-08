/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// movement2.e  —  Adagio Sostenuto
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Second movement — slow, lyrical, deeply expressive.
// Ternary form (ABA) with a contemplative middle section.
// Run from project root: py ep.py compile examples/projects/parts/movement2.e
// ====================================================================

@bpm 50                                 // Adagio — very slow
@sig 3/4                                // Triple time, waltz-like

// -------------------------------------------------------------------
// A SECTION — Cantabile (bars 1–16)
// Singing melody in F major, warm and spacious
// -------------------------------------------------------------------
section "A — Cantabile"

for $i 0 to 15
  // Melody in right hand
  play F4 1.5
  @vel 55 + sin($i * 0.4) * 8
  play G4 1.0
  play A4 1.5
  play C5 1.0
  play A4 1.0
  play G4 1.0
  play F4 2.0
  wait 0.5

  // Bass — simple waltz accompaniment
  play F2 1.0
  play C3 1.0
  play A2 1.0
end

// -------------------------------------------------------------------
// B SECTION — Agitato (bars 17–28)
// Turbulent middle section in D minor
// -------------------------------------------------------------------
section "B — Agitato"

@vel 65 to 80 arc                       // Building agitation

for $i 0 to 11
  play D3 F3 A3 D4                      // D minor — uneasy
  wait 1
  play E3 G3 B3 E4                      // E dim — chromatic rise
  wait 1
  play F3 A3 C4 F4                      // F major — brief respite
  wait 1
  play G2 B3 D4 G4                      // G7 — dominant
  wait 1
  play C3 E3 G3 C4                      // C major — false resolution
  wait 1
  play A2 C3 E3 A3                      // Am — falling back
  wait 1
end

// -------------------------------------------------------------------
// A' SECTION — Return (bars 29–44)
// Theme returns, more elaborate, with decorated melody
// -------------------------------------------------------------------
section "A' — Return"

@vel 60 to 70 arc                       // Slightly fuller than first A

for $i 0 to 15
  // Ornamented melody with passing tones
  play F4 1.0
  play E4 0.25                          // Grace note
  play F4 0.25
  play G4 1.0
  play A4 1.5
  play Bb4 0.5
  play A4 0.5
  play G4 1.0
  play F4 2.0
  wait 0.5

  // Richer accompaniment
  play F2 A2 C3 F3 1.5
  play C3 E3 G3 1.5
  play D3 F3 A3 D4 1.5
  wait 1.5
end

// -------------------------------------------------------------------
// CODA (bars 45–48)
// Fade on the tonic, like a held breath
// -------------------------------------------------------------------
section "Coda"

@vel 45 to 25 arc decrescendo           // Diminuendo al niente

play F3 A3 C4 F4 A4 C5                 // Final F major chord
wait 3
play F3 A3 C4 F4                       // Reduced voicing
wait 3
play F3 C4 F4                          // Bare fifth
wait 6                                 // Let ring

// End of movement 2 — 48 bars
