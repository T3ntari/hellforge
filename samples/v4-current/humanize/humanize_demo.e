/* HELLFORGE v1.0.0.0 ALPHA - CORE-EXPANSION: REGAS */
// Humanize — de-robot MIDI with a tiny numpy MoE (~49k params)
   File:       humanize_demo.e
   Version:    v4 (unified engine) - CURRENT STANDARD
   Status:     CURRENT STANDARD
   
   The @humanize:nn directive adds human micro-timing and expressive
   velocity to compiled songs. nn is strength 0-100:
     @humanize:15   subtle (default)
     @humanize:50   noticeable
     @humanize:100  fully human
     @humanize:0    off (also: @humanize off)
   
   Each note's context (pitch, velocity, position in bar, local note
   density, previous timing/dynamics) is scored by an 8-expert
   Mixture-of-Experts model that predicts timing jitter + velocity
   deltas — trained once on a human-performance regression task and
   cached to .fent_cache. Pure numpy, instant CPU inference. */

@bpm 96
@humanize:40

// An 8-note melody repeated twice — the second pass gets the
// humanized timing/dynamics from the model.
C4 q
D4 q
E4 q
F4 q
G4 q
A4 q
G4 q
E4 q

repeat 2 {
    C4 e D4 e E4 e F4 e
    G4 e A4 e G4 e E4 e
}

/* Tip: run 'humanize status' in eshell to see the model info,
   'humanize retrain' to re-fit, or convert with strength to taste. */
