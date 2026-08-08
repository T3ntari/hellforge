/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// lullaby_v4.e  —  "Starfall Slumber"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// A complete, beautiful lullaby in C major, 64+ bars at @bpm 80.
// Uses v4 polyrhythm, for loops, velocity modulation, sections.
// Run from project root: py ep.py compile examples/v4-compositions/lullaby_v4.e
// ====================================================================

@bpm 80                            // Gentle lullaby tempo
@sig 4/4                           // Common time, steady rock

// -------------------------------------------------------------------
// SECTION A — Introduction (bars 1–8)
// Soft arpeggiated C major chord, pianissimo, like distant stars
// -------------------------------------------------------------------
section "A — Intro"

// Polyrhythm layer: 5:4 right-hand arpeggio over bass pedal
polyrhythm 5:4
for $i 0 to 7                     // 8 bars of intro
  play C3 E3 G3 C4 E4 G4          // C major arpeggio, full
  @vel 30 + $i * 3                // Velocity modulation: crescendo from pp to mp
  @len 1.8                        // Legato, overlapping
  play D3 F3 A3 D4 F4 A4          // Dm7 — gentle lift
  @vel 32 + $i * 2
  play E3 G3 B3 E4 G4 B4          // Em7 — yearning, suspended
  @vel 28 + $i * 4
  play F3 A3 C4 F4 A4 C5          // Fmaj7 — warmth arriving
  @vel 35 + $i * 2
  wait 1/4                        // Brief breath between cycles
end

// -------------------------------------------------------------------
// SECTION B — Main Theme (bars 9–24)
// The lullaby melody enters: simple, singable, swaying
// -------------------------------------------------------------------
section "B — Theme"

for $i 0 to 15                    // 16 bars of melody
  // Bar 1 — melody phrase "star-fall gen-tle"
  @vel 55 + (sin(($i * 0.5)) * 15)  // Velocity modulated by sine wave
  play G4 1.0                     // "Star-"
  play A4 0.5                     // "fall"
  play B4 0.75                    // "gen-"
  play G4 1.0                     // "tle"

  // Bar 2 — descending answer
  @vel 50 + (cos(($i * 0.3)) * 10)
  play E4 1.5                     // "Sleep-"
  play F4 0.5                     // "ing"
  play E4 1.0                     // "child"

  // Bar 3 — rising third
  @vel 60 + (sin(($i * 0.7)) * 12)
  play C5 0.75                    // "Moon-"
  play D5 0.5                     // "beams"
  play C5 1.0                     // "dance"
  play B4 1.0                     // "soft"

  // Bar 4 — resolution
  @vel 45 + (cos(($i * 0.4)) * 8)
  play A4 2.0                     // "Hush..."
  wait 1/2                        // Rest, silence, breath
end

// -------------------------------------------------------------------
// SECTION C — Middle Interlude (bars 25–36)
// Modulation to relative minor (Am), more intimate, polyrhythmic
// -------------------------------------------------------------------
section "C — Interlude (Am)"

@vel 40 to 55 arc                 // Dynamic arc: gradual swell across section
polyrhythm 7:4                    // 7-over-4 — gentle unevenness, rocking

for $i 0 to 11                    // 12 bars
  play A2 C3 E3 A3 C4 E4          // Am7
  wait 1/2
  play D2 F3 A3 D4                // Dm7 — subdominant, tender
  wait 1/2
  play E2 G3 B3 E4                // E7 — dominant, slight tension
  wait 1/2
  play A2 C3 E3 A3 C4 E4          // Back to Am, resolved
  wait 1/2
  // Introduce counter-melody in higher register
  @vel 48
  play C5 0.75
  play B4 0.5
  play A4 1.0
  wait 1/4
end

// -------------------------------------------------------------------
// SECTION D — Return to C Major (bars 37–52)
// Theme returns with fuller texture, richer voicing
// -------------------------------------------------------------------
section "D — Theme Return"

for $i 0 to 15
  // Layered polyrhythm 3:2 over the return
  polyrhythm 3:2

  // Left hand — root-fifth pattern
  play C2 G2 2.0
  play F2 C3 2.0
  play G2 D3 2.0
  play C2 G2 2.0

  // Right hand — melody with ornamentation
  @vel 60 + (sqrt($i + 1) * 5)    // Velocity grows with sqrt curve
  play G4 0.5 G4 0.25 A4 0.5     // Grace note flourish
  play B4 1.0 G4 1.0
  play E4 0.75 F4 0.5 E4 1.0
  play C5 0.5 D5 0.5 C5 1.5

  // Fill — soft chordal pads
  @vel 35
  play C3 E3 G3 1.0
  wait 1/2
end

// -------------------------------------------------------------------
// SECTION E — Bridge (bars 53–58)
// Diminished transition, building anticipation for finale
// -------------------------------------------------------------------
section "E — Bridge"

@vel 50 to 75 arc                // Crescendo through bridge
polyrhythm 9:8                   // 9:8 — complex, swirling

for $i 0 to 5                    // 6 bars
  play B2 D3 F3 B3 D4 F4         // Bdim — tension
  wait 1/2
  play C3 E3 G3 C4 E4 G4         // Cmaj — brief relief
  wait 1/4
  play D3 F3 A3 D4 F4 A4         // Dm7
  wait 1/2
  play G2 B3 D4 G4               // G7 — dominant, expectant
  wait 1/4
end

// -------------------------------------------------------------------
// SECTION F — Finale & Coda (bars 59–72)
// Biggest dynamics, then fading to nothing
// -------------------------------------------------------------------
section "F — Finale & Coda"

@vel 75 to 85 arc                // Forte! Full expression
for $i 0 to 7                    // 8 bars of climactic statement
  play C2 G2 C3 E3 G3 C4 E4 G4 C5 E5 G5  // Full C major tutti
  wait 1
  play F2 C3 F3 A3 C4 F4 A4 C5 F5 A5      // Fmaj7
  wait 1
  play G2 D3 G3 B3 D4 G4 B4 D5 G5         // G7
  wait 1
  play C2 G2 C3 E3 G3 C4 E4 G4 C5 E5 G5  // C major — triumphant return
  wait 1
end

// Coda — fade to silence (bars 73–76)
@vel 60 to 20 arc decrescendo     // Gradually disappear
polyrhythm 5:4                    // Return to opening polyrhythm
play C3 G3 C4 E4 G4 C5           // Final chord
wait 2
play C3 G3 C4 E4                  // Reduced
wait 2
play C3 C4                        // Bare octave
wait 2
play C3                           // Single note
wait 4                            // Fade into silence

// End of piece
/* Lullaby complete: 76 bars, ~3:48 at @bpm 80 */
