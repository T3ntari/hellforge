/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// cinematic_v4.e  —  "The Approaching Storm"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Cinematic orchestral piece with tempo curves, dynamic arcs,
// polyrhythms, probability, and generative elements. 150+ events.
// Run from project root: py ep.py compile examples/v4-compositions/cinematic_v4.e
// ====================================================================

@bpm 60                             // Slow, majestic opening
@sig 4/4

// -------------------------------------------------------------------
// GLOBAL DYNAMIC ARC — defines the overall shape of the piece
// The entire composition follows this emotional contour
// -------------------------------------------------------------------
$global_arc = [20, 25, 35, 50, 45, 60, 80, 100, 110, 105, 90, 70, 50, 30]

// -------------------------------------------------------------------
// SECTION A — The Calm (bars 1–16)
// Sparse strings, atmospheric pads, generative melody
// -------------------------------------------------------------------
section "A — The Calm"

// Tempo curve: gradually accelerate from 60 to 72 over 16 bars
@tempo_curve 60 72 16

// Generative bass drone with probability-based ornamentation
for $i 0 to 15                      // 16 bars
  // Bass drone — deep, rumbling
  play C1 4.0                       // Held for full bar
  @vel 25 + $global_arc[$i / 2] * 0.3

  // Probabilistic string pad — 60% chance per bar, creates texture
  @probability 60
  play C3 G3 C4 E4 G4 C5           // C major string cluster
  @vel 30 + rand(10)
  @len 3.5

  // Generative upper melody — evolves using markov-like selection
  $probs = [40, 25, 20, 10, 5]     // Weighted probability distribution
  $melody_note = weighted_choice([E4, G4, A4, B4, C5], $probs)
  play $melody_note 1.5
  @vel 35 + rand(8)
  wait 1

  // Second half of bar — answering phrase
  $melody_note2 = weighted_choice([D4, E4, F4, G4, A4], $probs)
  play $melody_note2 1.0
  wait 1
end

// -------------------------------------------------------------------
// SECTION B — Rising Tension (bars 17–32)
// Strings expand, timpani enters, polyrhythm introduced
// -------------------------------------------------------------------
section "B — Rising Tension"

@tempo_curve 72 80 16
@vel 40 to 65 arc                   // Gradual crescendo across section

// Polyrhythm 5:4 — strings play 5 against the pulse's 4
polyrhythm 5:4

for $i 0 to 15
  // Timpani rolls on downbeats
  if ($i % 4 == 0)
    play C2 0.5
    @vel 50 + $i * 2
    @roll 0.4                       // Roll articulation
  end

  // String section — layered fifths
  play C3 G3 D4 A4 E5              // Open fifths, building
  @vel 40 + $i * 2
  @len 2.0

  // Brass stab — probability increases over time
  // As tension builds, brass becomes more likely to enter
  @probability 20 + $i * 3
  play E3 G3 C4 E4                  // C major brass stab
  @vel 60 + $i * 2

  // Low strings — chromatic creep
  play C2 2.0
  play C2 1.0                       // Held pedal
  play Db2 1.0                      // Half-step rise — tension
  play D2 1.0                       // Another half-step
  wait 1
end

// -------------------------------------------------------------------
// SECTION C — Storm (bars 33–48)
// Full orchestra, aggressive polyrhythms, dynamic climax
// -------------------------------------------------------------------
section "C — The Storm"

@tempo_curve 80 96 16               // Tempo drives forward
@vel 70 to 110 arc                  // Huge dynamic swell

for $i 0 to 15
  // Full orchestral hit
  play C1 C2 C3 E3 G3 C4 E4 G4 C5 E5 G5 C6  // Orchestral tutti
  @vel 75 + (sin($i * 1.2) * 20) + ($i * 2.5)
  @len 0.8

  // Polyrhythm 7:4 on horns
  polyrhythm 7:4
  play E3 G3 C4 E4                  // Horn stab
  @vel 85

  // Timpani and percussion
  if ($i % 2 == 0)
    play C2 0.3
    play G2 0.3                     // Timpani fifth
    @vel 90
  end

  // Probability-driven cymbal crashes
  @probability 35
  play C5 0.2                       // Crash cymbal
  @vel 100

  // Violins — fast ascending runs using generative algorithm
  $run_base = [C5, D5, E5, F5, G5, A5, B5, C6]
  for $j 0 to 3
    play $run_base[($i + $j) % 8] 0.1
    @vel 80 + $j * 5
  end

  wait 1
end

// -------------------------------------------------------------------
// SECTION D — Aftermath (bars 49–64)
// Decay, fragments, memory of the storm
// -------------------------------------------------------------------
section "D — Aftermath"

@tempo_curve 96 60 16               // Tempo slows back to start
@vel 80 to 30 arc decrescendo       // Massive decrescendo

// Polyrhythm 3:4 — inverted, feels like floating
polyrhythm 3:4

for $i 0 to 15
  // Fragmented string harmonics
  @probability 45
  play G4 2.0
  @vel 40 - $i * 1.5

  @probability 30
  play C5 1.0
  @vel 35 - $i * 1.2

  // Solo cello line — mournful, using natural minor
  $cello_mel = [C3, D3, Eb3, F3, G3, Ab3, Bb3, C4]
  play $cello_mel[$i % 8] 1.5
  @vel 30 - $i * 0.8

  // Distant timpani — like fading thunder
  if ($i % 6 == 0)
    play C2 0.4
    @vel 20
  end

  // Wind chimes — random high register sparkles
  @probability 20
  play G6 0.3
  @vel 15 + rand(10)

  wait 1
end

// -------------------------------------------------------------------
// CODA — Resolution (bars 65–68)
// Single cello note fades into silence
// -------------------------------------------------------------------
section "Coda"

@bpm 50                            // Ritardando to stop
@vel 20 to 5 arc decrescendo

play C3 8.0                        // Final note, held for 8 beats
wait 8                             // Silence

// Total: ~185 events across 68 bars, ~5:20 total duration
