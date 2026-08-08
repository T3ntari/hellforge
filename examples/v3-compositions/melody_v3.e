/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// melody_v3.e  —  "Morning Walk"
// VERSION STATUS: v3  FULLY SUPPORTED  |  E LANGUAGE ALPHA
// A complete melody using v3 shorthand notation exclusively.
// @bpm 100. Uses note+duration format throughout.
// Run from project root: py ep.py compile examples/v3-compositions/melody_v3.e
// ====================================================================

@bpm 100                                // Comfortable walking tempo
@sig 4/4                                // Simple time signature

// -------------------------------------------------------------------
// v3 Shorthand Syntax:
// In v3 mode, notes are written as:  NOTE DURATION
// where duration is in beats (1.0 = quarter note, 0.5 = eighth, etc.)
// Velocity is set via @vel directive preceding notes.
// This is the classic E DSL notation — concise and musical.
// -------------------------------------------------------------------

// -------------------------------------------------------------------
// SECTION A — Statement (bars 1–8)
// Opening melodic phrase, bright and optimistic in C major
// -------------------------------------------------------------------
section "A — Statement"

@vel 70                                 // mezzo-forte, confident

// Bar 1: Rising fifth — "morn-ing light"
C4 1.0
D4 0.5
E4 0.5
F4 1.0
G4 1.0

// Bar 2: Descending sequence — "greets the world"
E4 0.5
F4 0.5
E4 1.0
D4 1.0
C4 1.0

// Bar 3: Arch shape — "sun-beams warm"
E4 0.75
G4 0.25
A4 1.0
G4 1.0
E4 1.0

// Bar 4: Cadence — "peace-ful day"
D4 0.5
C4 0.5
D4 1.0
C4 2.0

// Repeat phrase with variation (bars 5–8)
E4 0.5
F4 0.5
G4 1.0
A4 1.0
B4 1.0
G4 0.5
A4 0.5
G4 1.0
F4 1.0
E4 1.0
F4 0.75
A4 0.25
C5 1.0
B4 1.0
G4 1.0
E4 0.5
F4 0.5
E4 1.0
C4 2.0

// -------------------------------------------------------------------
// SECTION B — Development (bars 9–16)
// Moves to the dominant, more animated
// -------------------------------------------------------------------
section "B — Development"

@vel 75                                 // Slightly louder

// Bar 9–10: Exploration in G major
G4 0.5
A4 0.5
B4 1.0
D5 1.0
C5 0.5
B4 0.5
A4 1.0
G4 1.0
F4 1.0

// Bar 11–12: Syncopated rhythm
E4 0.25
G4 0.25
E4 0.5
G4 1.0
A4 0.5
G4 0.5
F4 1.0
E4 1.0
D4 1.0

// Bar 13–14: Climb to climax
F4 0.5
G4 0.5
A4 1.0
C5 1.0
E5 1.0
D5 0.5
C5 0.5
B4 1.0
G4 1.0

// Bar 15–16: Return cadence
C5 0.5
B4 0.5
A4 1.0
G4 1.0
F4 0.5
E4 0.5
D4 1.0
C4 2.0

// -------------------------------------------------------------------
// SECTION C — Variation (bars 17–20)
// Syncopated rhythmic variation, using shorter durations
// -------------------------------------------------------------------
section "C — Variation"

@vel 65                                 // Softer, more intimate

C4 0.25
E4 0.25
G4 0.5
C5 0.5
B4 0.25
A4 0.25
G4 0.5
E4 0.5
F4 0.25
A4 0.25
C5 0.5
E5 0.5
D5 0.25
C5 0.25
B4 0.5
G4 0.5
A4 0.25
B4 0.25
C5 0.5
A4 0.5
G4 0.25
F4 0.25
E4 0.5
D4 0.5
C4 0.25
E4 0.25
G4 0.5
C5 0.5
E5 0.5
D5 0.5
C5 1.0

// -------------------------------------------------------------------
// SECTION D — Recapitulation (bars 21–28)
// Theme returns with fuller expression
// -------------------------------------------------------------------
section "D — Recapitulation"

@vel 78                                 // Richer dynamic

// Bars 21–28: Return of opening, varied and extended
C4 1.0
D4 0.5
E4 0.5
F4 1.0
G4 1.5
E4 0.5
F4 0.5
E4 1.0
D4 1.0
C4 1.5
E4 0.75
G4 0.25
A4 1.0
C5 1.0
B4 0.5
A4 0.5
G4 1.0
F4 1.0
E4 1.0
D4 0.5
C4 0.5
D4 1.0
C4 2.0
G4 0.5
A4 0.5
B4 1.0
C5 1.0
D5 1.0
C5 0.5
B4 0.5
C5 1.0
E5 1.0
D5 1.0
C5 0.5
B4 0.5
A4 1.0
G4 1.0
F4 0.5
E4 0.5
D4 1.0
C4 2.0

// -------------------------------------------------------------------
// CODA (bars 29–32)
// Gentle resolution with ritardando feel
// -------------------------------------------------------------------
section "Coda"

@vel 55 to 30 arc decrescendo           // Fading away

C4 1.5
E4 1.0
G4 2.0
C5 1.0
B4 1.0
A4 2.0
G4 1.5
E4 1.0
C4 3.0

// End of melody — 32 bars total
