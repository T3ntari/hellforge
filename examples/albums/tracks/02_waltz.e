/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// 02_waltz.e  —  "Waltz of the Fireflies"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Track 2 of opus1.enx. A lilting waltz in G major.
// Classic oom-pah-pah accompaniment with a soaring melody.
// Run from project root: py ep.py compile examples/albums/tracks/02_waltz.e
// ====================================================================

@bpm 120                                // Lively waltz tempo
@sig 3/4                                // Waltz time

// -------------------------------------------------------------------
// SECTION A — Main Waltz Theme (bars 1–16)
// Oom-pah-pah: bass on 1, chords on 2 & 3
// -------------------------------------------------------------------
section "A — Theme"

for $i 0 to 15
  // Bass — root of chord on beat 1
  play G2 1.0
  @vel 65 + sin($i * 0.5) * 6

  // Chords — full voicing on beats 2 & 3
  play G3 B3 D4 G4 0.5                  // G major — beat 2
  @vel 50
  play G3 B3 D4 G4 0.5                  // Beat 3
  @vel 48

  // Melody — floats above on beats 1, 2, 3
  play D5 0.5
  @vel 70
  play B4 0.5
  @vel 65
  play G4 0.5
  @vel 68

  wait 0.5                               // Rest completes the bar

  // Bar 2 — D7 dominant
  play D2 1.0
  @vel 62
  play D3 F3 A3 D4 0.5
  play D3 F3 A3 D4 0.5
  play A4 0.5
  play F4 0.5
  play D4 0.5
  wait 0.5
end

// -------------------------------------------------------------------
// SECTION B — Trio (bars 17–32)
// Modulation to D major — brighter, more lyrical
// -------------------------------------------------------------------
section "B — Trio"

@vel 70 to 80 arc

for $i 0 to 15
  play D2 1.0
  play D3 F#3 A3 D4 0.5
  play D3 F#3 A3 D4 0.5
  play F#5 0.5
  play D5 0.5
  play A4 0.5
  wait 0.5

  play A2 1.0
  play A3 C#4 E4 A4 0.5
  play A3 C#4 E4 A4 0.5
  play E5 0.5
  play C#5 0.5
  play A4 0.5
  wait 0.5

  play E2 1.0
  play E3 G#3 B3 E4 0.5
  play E3 G#3 B3 E4 0.5
  play B4 0.5
  play G#4 0.5
  play E4 0.5
  wait 0.5

  play A2 1.0
  play A3 C#4 E4 A4 0.5
  play A3 C#4 E4 A4 0.5
  play C#5 0.5
  play A4 0.5
  play E4 0.5
  wait 0.5
end

// -------------------------------------------------------------------
// SECTION A' — Return (bars 33–40)
// Theme returns with fuller texture
// -------------------------------------------------------------------
section "A' — Return"

@vel 75 to 65 arc decrescendo           // Gradual wind-down

for $i 0 to 7
  play G2 1.0
  play G3 B3 D4 G4 0.5
  play G3 B3 D4 G4 0.5
  play D5 0.5
  play B4 0.5
  play G4 0.5
  wait 0.5

  play D2 1.0
  play D3 F#3 A3 D4 0.5
  play D3 F#3 A3 D4 0.5
  play F#4 0.5
  play D4 0.5
  play A3 0.5
  wait 0.5
end

// -------------------------------------------------------------------
// CODA (bars 41–44)
// Waltz fades out gracefully
// -------------------------------------------------------------------
section "Coda"

@vel 50 to 25 arc decrescendo
play G2 G3 B3 D4 G4 1.0
wait 1
play G2 G3 B3 D4 1.0
wait 1
play G2 G3 B3 1.0
wait 1
play G2 2.0                             // Single bass note to finish
wait 4

// End of Waltz — 44 bars
