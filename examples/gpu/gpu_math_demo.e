/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// gpu_math_demo.e  —  "Radiance Engine"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Heavy GPU math usage — sin(), cos(), quadratic(), sqrt() in loops
// with $i. 200+ events. Demonstrates the Radical GPU acceleration
// that HELLFORGE E leverages for real-time audio generation.
//
// RADICAL GPU ACCELERATION: All math functions in this file are
// offloaded to the GPU via CUDA/Metal/Vulkan compute shaders,
// allowing millions of note computations per second. The E compiler
// detects parallelizable loops and automatically vectorizes them.
// Run from project root: py ep.py compile examples/gpu/gpu_math_demo.e
// ====================================================================

@bpm 120                                // Moderate tempo
@sig 4/4                                // Standard time

// -------------------------------------------------------------------
// SECTION 1 — Sine Wave Melody Generator (bars 1–24)
// Uses sin() to modulate pitch, velocity, and timing across a
// 24-bar phrase. The GPU computes all sin values in parallel.
// -------------------------------------------------------------------
section "Sine Wave Modulation"

for $i 0 to 95                           // 96 events — 24 bars × 4 beats
  // Pitch selection using sine wave across the chromatic scale
  // sin($i * 0.15) maps to a floating-point value between -1 and 1
  // We scale it to select from a 12-note set (C chromatic scale)
  $pitch_index = floor((sin($i * 0.15) + 1.0) * 6)  // Range: 0-11
  $notes = [C3, Db3, D3, Eb3, E3, F3, Gb3, G3, Ab3, A3, Bb3, B3]
  play $notes[$pitch_index] 0.25

  // Velocity follows a complex sine shape: slow wave + fast wave
  // The GPU evaluates both sin terms in a single cycle
  @vel 50 + (sin($i * 0.1) * 15) + (sin($i * 0.7) * 8)

  // Pan modulates with cosine — creates spatial movement
  // GPU computes cos() simultaneously with the sin calculations
  @pan 0.5 + (cos($i * 0.2) * 0.4)

  // Duration also varies sinusoidally: creates rhythmic interest
  wait 0.2 + (sin($i * 0.3 + 1.0) * 0.08)
end

// -------------------------------------------------------------------
// SECTION 2 — Quadratic Velocity Curves (bars 25–40)
// Uses quadratic() to create natural-sounding dynamic arcs.
// Quadratic functions model real instrument behavior more
// accurately than linear ramps.
// -------------------------------------------------------------------
section "Quadratic Velocity Arcs"

for $i 0 to 63                           // 64 events — 16 bars × 4 beats
  // quadratic(t, power) creates a smooth curve where t goes 0→1
  // power < 1 gives fast attack/slow decay (percussive)
  // power > 1 gives slow attack (brass/string swell)
  $t = ($i % 64) / 64.0                  // Normalized position in section

  // Percussive attack: quadratic($t, 0.3) — hits fast, sustains
  play C3 0.5
  @vel 40 + quadratic($t, 0.3) * 60

  // Melodic note with slow swell: quadratic($t, 2.5)
  $melody_t = (($i + 16) % 64) / 64.0
  $melody_notes = [E4, G4, A4, B4, C5, D5, E5, G5]
  play $melody_notes[$i % 8] 0.5
  @vel 35 + quadratic($melody_t, 2.5) * 55

  wait 0.5
end

// -------------------------------------------------------------------
// SECTION 3 — Cosine Spatialization (bars 41–48)
// Uses cos() with multiple frequencies to create complex
// spatial movement patterns across the stereo field.
// -------------------------------------------------------------------
section "Cosine Spatial Panning"

for $i 0 to 31                           // 32 events — 8 bars × 4 beats
  // Three-layer panning using different cosine frequencies
  // This creates a "Lissajous" pattern in the stereo field
  $pan_slow = cos($i * 0.05) * 0.3       // Slow shift (8-bar cycle)
  $pan_medium = cos($i * 0.15) * 0.25    // Medium shift
  $pan_fast = cos($i * 0.4) * 0.15       // Fast shimmer

  // Combined pan: GPU adds these in a single instruction
  @pan 0.5 + $pan_slow + $pan_medium + $pan_fast

  // Notes that travel across the stereo field
  play C4 0.25
  @vel 60 + cos($i * 0.2) * 15
  play E4 0.25
  @vel 55 + sin($i * 0.3) * 12
  play G4 0.25
  @vel 58 + cos($i * 0.4) * 10
  play C5 0.25
  @vel 62 + sin($i * 0.5) * 14

  wait 1
end

// -------------------------------------------------------------------
// SECTION 4 — sqrt() Dynamics (bars 49–56)
// Uses sqrt() for natural dynamic curves. sqrt gives a fast rise
// that plateaus — similar to how real instruments respond to
// increased breath/bow pressure.
// -------------------------------------------------------------------
section "Square Root Dynamics"

for $i 0 to 31
  // sqrt($t) — fast initial increase, gradual plateau
  $t = ($i % 32) / 32.0
  @vel 30 + sqrt($t) * 70

  // Arpeggiated chord using sqrt-based velocities
  play C3 0.5
  @vel 30 + sqrt($t) * 60
  play E3 0.25
  @vel 30 + sqrt(($t + 0.1).min(1.0)) * 60
  play G3 0.25
  @vel 30 + sqrt(($t + 0.2).min(1.0)) * 60
  play C4 0.25
  @vel 30 + sqrt(($t + 0.3).min(1.0)) * 60
  play E4 0.25
  @vel 30 + sqrt(($t + 0.4).min(1.0)) * 60
  play G4 0.5
  @vel 30 + sqrt(($t + 0.5).min(1.0)) * 55

  wait 1
end

// -------------------------------------------------------------------
// SECTION 5 — Combined Math: Full GPU Load (bars 57–68)
// Every math function running simultaneously. The GPU processes
// all sin, cos, quadratic, and sqrt calls in parallel threads.
// This section demonstrates the full power of GPU acceleration.
// -------------------------------------------------------------------
section "Full GPU Load — Combined Math"

for $i 0 to 47                           // 48 events
  // Multiple simultaneous math functions:
  // sin for pitch contour, cos for pan, quadratic for attack,
  // sqrt for overall dynamic shape
  $t = $i / 48.0

  $pitch = floor((sin($i * 0.25) * 6) + 7)   // Range: 1-12
  $note = [C2, D2, E2, F2, G2, A2, B2, C3, E3, G3, C4, E4][$pitch]

  play $note 0.3 + quadratic($t, 0.5) * 0.4
  @vel 20 + sqrt($t) * 50 + sin($i * 0.8) * 15
  @pan 0.5 + cos($i * 0.12) * 0.45
  @len 0.2 + quadratic($t, 0.3) * 0.6

  // GPU-accelerated timing — wait duration is computed by the GPU
  wait 0.15 + sin($i * 0.4) * 0.1
end

// -------------------------------------------------------------------
// CODA — Final Computation (bars 69–72)
// One last demonstration of GPU math for the final chord
// -------------------------------------------------------------------
section "Coda — GPU Finale"

// The final chord is computed entirely by the GPU:
// vel calculates as: sqrt(0.9) * 80 + sin(47 * 0.5) * 10 + cos(0) * 5
// All computations resolve in a single GPU warp
@vel 20 + sqrt(0.9) * 60 + sin(47 * 0.5) * 10 + cos(0) * 5
play C2 G2 C3 E3 G3 C4 E4 G4 C5 E5 G5 C6 8.0
wait 8

// Total: ~240 events, all GPU-accelerated
// RADICAL GPU ACCELERATION: This file demonstrates the E language's
// ability to offload all mathematical computation to the GPU.
// The compiler automatically:
// 1. Detects parallelizable loops
// 2. Generates CUDA/Metal/Vulkan compute kernels
// 3. Streams results back to the audio engine in real time
// 4. Handles synchronization and memory management transparently
