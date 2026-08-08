/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// techno_v4.e  —  "Acid Pulse"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// High-energy techno at 140bpm. Uses for loops, math functions for
// velocity, repeat patterns, Euclidean rhythms. 100+ events.
// Run from project root: py ep.py compile examples/v4-compositions/techno_v4.e
// ====================================================================

@bpm 140                            // Driving techno tempo
@sig 4/4                            // Four-on-the-floor foundation

// -------------------------------------------------------------------
// SECTION 1 — Kick Pattern (bars 1–8)
// Classic 4/4 kick with Euclidean hi-hat accents
// -------------------------------------------------------------------
section "Kick Foundation"

// Euclidean rhythm: 5/8 hi-hat pattern over 4/4 kick
// This creates that off-kilter, hypnotic techno feel
for $i 0 to 31                      // 32 beats = 8 bars
  // Four-on-the-floor kick
  play C2 0.1                       // Short, punchy kick
  @vel 100
  wait 1/4

  play C2 0.1
  @vel 95
  wait 1/4

  play C2 0.1
  @vel 100
  wait 1/4

  play C2 0.1
  @vel 98
  wait 1/4
end

// -------------------------------------------------------------------
// SECTION 2 — Hi-Hat & Percussion (bars 9–16)
// Euclidean rhythm generator for hi-hats and claps
// -------------------------------------------------------------------
section "Percussion Layer"

for $i 0 to 31
  // Kick still going — pattern repeats
  play C2 0.1
  @vel 100
  wait 1/8

  // Euclidean decision: play hi-hat on steps 0, 1, 3, 5, 7 of 8
  // This is a standard 5/8 Euclidean pattern (E(5,8))
  if ($i % 8 == 0 || $i % 8 == 1 || $i % 8 == 3 || $i % 8 == 5 || $i % 8 == 7)
    play E5 0.05                    // Closed hi-hat — very short
    @vel 65 + ($i % 3) * 10         // Slight velocity variation
  end

  // Clap on beats 2 and 4 (every 4th step)
  if ($i % 4 == 1)
    play D3 0.15                     // Clap sound
    @vel 85 + sin($i * 0.5) * 5     // Subtle humanization on clap
  end

  wait 1/8
end

// -------------------------------------------------------------------
// SECTION 3 — Bassline (bars 17–24)
// Acid-style bassline using for loop with math modulation
// -------------------------------------------------------------------
section "Acid Bassline"

for $i 0 to 31
  // Bass note selection modulated by sin for that acid squelch
  // Pattern cycles through E, F, G, A, Bb, creating tension
  $note_index = floor(abs(sin($i * 0.3)) * 6)
  if ($note_index == 0)
    play E1 0.4
  elif ($note_index == 1)
    play F1 0.3
  elif ($note_index == 2)
    play G1 0.5
  elif ($note_index == 3)
    play A1 0.3
  elif ($note_index == 4)
    play Bb1 0.4
  else
    play E1 0.6
  end

  // Velocity follows a saw wave pattern for pumping effect
  @vel 70 + (($i % 16) * 2) - (sin($i * 0.25) * 10)

  // Slide between notes for that acid feel
  @slide 0.15
  wait 1/4
end

// -------------------------------------------------------------------
// SECTION 4 — Synth Stabs (bars 25–32)
// Call-and-response synth stabs with velocity modulation
// -------------------------------------------------------------------
section "Synth Stabs"

for $i 0 to 15                      // 8 bars of stabs
  // Main stab — every 2 beats
  play E3 G3 B3 D4                   // Em7 stab
  @vel 80 + quadratic($i, 0.5) * 15  // Quadratic velocity curve
  @len 0.3                           // Staccato
  wait 1/2

  // Response stab — off-beat
  play A3 C4 E4 G4                   // Am7 answer
  @vel 70 + cos($i * 0.8) * 12
  wait 1/2

  // Tension building — alternate chord every 4 bars
  if ($i % 4 == 0)
    play B2 D3 F3 B3 D4 F4          // Bdim — tension spike
    @vel 90
  end

  if ($i % 4 == 2)
    play F3 A3 C4 F4                 // Fmaj7 — release
    @vel 75
  end
end

// -------------------------------------------------------------------
// SECTION 5 — Breakdown & Buildup (bars 33–40)
// Filtered, reduced, then building energy back up
// -------------------------------------------------------------------
section "Breakdown"

@vel 50 to 40 arc decrescendo       // Pull back energy
for $i 0 to 15
  // Just hi-hat and kick, filtered
  play C2 0.15
  @vel 60
  wait 1/8

  if ($i % 4 == 0)
    play E5 0.05                     // Open hat on downbeats
    @vel 45
  end

  // Snare roll buildup
  if ($i >= 8)
    play D3 0.1
    @vel 40 + ($i - 8) * 5           // Crescendo roll
  end
  wait 1/8
end

// -------------------------------------------------------------------
// SECTION 6 — Drop (bars 41–48)
// Full energy return — layered polyrhythm 3:2
// -------------------------------------------------------------------
section "Drop — Full Energy"

polyrhythm 3:2                      // 3-over-2 polyrhythm for maximum drive
@vel 95 to 110 arc                  // Crushing volume

for $i 0 to 31                      // 8 bars of drop
  // Kick doubled with bass drum
  play C1 0.15
  play C2 0.1
  wait 1/8

  // Syncopated synth line — E Phrygian
  $note = [E2, F2, G2, A2, Bb2, C3, D3, E3][$i % 8]
  play $note 0.2
  @vel 85 + abs(sin($i * 1.5)) * 20

  // Hi-hat pattern alternates every bar
  if (($i / 4) % 2 == 0)
    play E5 0.05
  else
    play E5 0.15                    // Open hat — more energy
  end
  wait 1/8
end

// -------------------------------------------------------------------
// OUTRO — Fade and stop (bars 49–52)
// -------------------------------------------------------------------
section "Outro"

@vel 80 to 30 arc decrescendo
for $i 0 to 15
  play C2 0.1
  wait 1/8
  play E5 0.05
  wait 1/8
end

play C1 0.5                         // Final hit
wait 2                              // Silence

// Total: ~120 events across 52 bars, ~2:58 at @bpm 140
