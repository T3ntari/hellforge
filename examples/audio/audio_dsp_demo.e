/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// audio_dsp_demo.e  —  "Spatial Reverie"
// VERSION STATUS: v4  CURRENT STANDARD  |  E LANGUAGE ALPHA
// Demonstrates audio features: @vol, @pan, @reverb, @delay
// directives. A rich composition showcasing EAudio integration
// with full DSP control per note and per section.
//
// EAudio provides real-time DSP processing directly within the
// E language compiler. Parameters are applied per-note and can
// be modulated by any expression.
//
// Run from project root: py ep.py compile examples/audio/audio_dsp_demo.e
// ====================================================================

@bpm 85                                 // Moderate, spacious
@sig 4/4                                // Common time

// -------------------------------------------------------------------
// GLOBAL DSP SETTINGS — applied to entire composition
// -------------------------------------------------------------------
@reverb_room 0.3                        // Room size (0.0–1.0)
@reverb_damp 0.5                        // High-frequency damping
@reverb_wet 0.25                        // Mix level for reverb

// -------------------------------------------------------------------
// SECTION 1 — Dry Center (bars 1–8)
// Bone-dry piano, center panned, no effects.
// Establishes the theme in its purest form.
// -------------------------------------------------------------------
section "Dry Center — Pure Tone"

@vol 0.75                               // Moderate volume
@pan 0.5                                // Dead center
@reverb 0.0                             // No reverb — completely dry
@delay 0.0                              // No delay

for $i 0 to 15
  play C4 0.5
  @vel 60
  play E4 0.5
  play G4 1.0
  play C5 1.0
  play B4 0.5
  play G4 0.5
  play E4 1.0
  play C4 1.0
end

// -------------------------------------------------------------------
// SECTION 2 — Reverb Swell (bars 9–16)
// Gradual introduction of reverb — cathedral space emerges.
// The same theme now sounds like it's in a vast hall.
// -------------------------------------------------------------------
section "Reverb Swell — Cathedral"

// Ramping reverb wetness from 0.2 to 0.8 over 8 bars
// This creates the illusion of the space slowly opening up
for $i 0 to 15
  $rev_wet = 0.2 + ($i * 0.04)          // Linear ramp: 0.2 → 0.8

  @vol 0.70
  @pan 0.5
  @reverb $rev_wet                      // Reverb increases bar by bar
  @reverb_size 0.6 + ($i * 0.025)       // Room grows from medium to large
  @reverb_damp 0.7 - ($i * 0.02)        // Dampening decreases (brighter)

  play C4 E4 G4 C5 2.0                  // Sustained chord
  @vel 55 + ($i * 1.5)
  wait 1

  play G3 B3 D4 G4 2.0                  // G7 — dominant
  @vel 50 + ($i * 1.2)
  wait 1
end

// -------------------------------------------------------------------
// SECTION 3 — Pan Automation (bars 17–24)
// Notes sweep across the stereo field using @pan modulation.
// Creates movement and width in the arrangement.
// -------------------------------------------------------------------
section "Pan Automation — Spatial Sweep"

@reverb 0.4                             // Moderate reverb
@delay 0.0

for $i 0 to 31
  // Pan oscillates left to right using a sawtooth-like pattern
  $sweep_pos = ($i % 16) / 15.0         // 0.0 to 1.0 over 16 events
  @pan $sweep_pos                       // Pans from hard left to hard right

  @vol 0.65 + sin($i * 0.3) * 0.1       // Volume slightly modulated

  play A3 0.25
  @vel 55
  play C4 0.25
  @vel 58
  play E4 0.25
  @vel 52
  play A4 0.25
  @vel 60
  play C5 0.25
  @vel 56
  play E5 0.25
  @vel 54
  play A5 0.5
  @vel 62
  wait 0.5
end

// -------------------------------------------------------------------
// SECTION 4 — Delay Cascade (bars 25–32)
// Ping-pong delay creates rhythmic echoes across the stereo field.
// Delay times sync to the tempo for musical repeats.
// -------------------------------------------------------------------
section "Delay Cascade — Ping Pong"

@bpm 100                                // Slightly faster for delay effect
@reverb 0.2                             // Less reverb to let delay shine

for $i 0 to 31
  // Ping-pong delay: left channel has 1/4 note delay, right has 1/8
  // The combination creates a cascading rhythmic effect
  @delay 0.5                            // 1/2 note delay time (syncs to @bpm)
  @delay_feedback 0.35                  // Moderate feedback (3-4 repeats)
  @delay_pan 0.5                        // Spread repeats across stereo

  // Alternate which side the dry signal hits
  if ($i % 2 == 0)
    @pan 0.2                            // Slightly left
  else
    @pan 0.8                            // Slightly right
  end

  @vol 0.70

  play D3 0.25
  @vel 70
  play F3 0.25
  @vel 65
  play A3 0.25
  @vel 68
  play D4 0.25
  @vel 72
  play F4 0.25
  @vel 66
  play A4 0.25
  @vel 70
  play D5 0.5
  @vel 75

  wait 0.5
  wait 0.5
end

// -------------------------------------------------------------------
// SECTION 5 — Full DSP Mix (bars 33–40)
// All effects active simultaneously — reverb, delay, pan, volume.
// Rich, immersive soundscape showing full EAudio integration.
// -------------------------------------------------------------------
section "Full DSP — Immersive"

for $i 0 to 31
  // Every parameter modulated simultaneously
  $t = $i / 32.0

  @vol 0.6 + quadratic($t, 0.4) * 0.3   // Volume swells
  @pan 0.5 + sin($i * 0.25) * 0.45      // Wide stereo motion
  @reverb 0.3 + cos($i * 0.15) * 0.25   // Reverberant shimmer
  @reverb_size 0.5 + sin($i * 0.1) * 0.3
  @reverb_damp 0.6 - cos($i * 0.2) * 0.2
  @delay 0.25 + sin($i * 0.3) * 0.15    // Delay time modulates
  @delay_feedback 0.3 + quadratic($t, 2.0) * 0.3

  // Rich chord with all DSP processing
  play F2 0.5
  @vel 50 + sin($i * 0.4) * 15
  play A2 0.5
  play C3 0.5
  play F3 0.5
  play A3 0.5
  play C4 0.5
  play F4 1.0
  @vel 55 + cos($i * 0.3) * 12

  wait 0.5

  // Answer chord with different DSP settings
  @pan 0.5 - sin($i * 0.25) * 0.4       // Inverse pan
  @reverb 0.4 - cos($i * 0.15) * 0.2    // Complementary reverb
  play G2 0.5
  play B2 0.5
  play D3 0.5
  play G3 0.5
  play B3 0.5
  play D4 0.5
  play G4 1.0
  wait 0.5
end

// -------------------------------------------------------------------
// CODA — FX Fadeout (bars 41–48)
// Gradually remove effects one by one, ending where we began: dry.
// -------------------------------------------------------------------
section "Coda — FX Fadeout"

for $i 0 to 31
  // Remove effects in reverse order
  @delay 0.5 - ($i * 0.016)             // Delay fades to 0
  @delay_feedback 0.3 - ($i * 0.01)

  @reverb 0.5 - ($i * 0.016)            // Reverb fades to 0
  @reverb_size 0.7 - ($i * 0.022)
  @reverb_damp 0.4 + ($i * 0.012)       // Becoming duller

  @pan 0.5 + (cos($i * 0.3) * 0.4 * (1.0 - $i * 0.03))  // Pan narrows
  @vol 0.7 - ($i * 0.015)               // Fade out

  play C3 E3 G3 C4 1.0
  @vel 50 - ($i * 1.2)
  wait 1
end

// Final note — completely dry, center, quiet
@vol 0.25
@pan 0.5
@reverb 0.0
@delay 0.0
play C4 4.0
@vel 25
wait 4.0

// End of audio_dsp_demo.e — full DSP demonstration
