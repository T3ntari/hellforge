/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// ====================================================================
// chord_song_v3.e  —  "Harmony's Voyage"
// VERSION STATUS: v3  FULLY SUPPORTED  |  E LANGUAGE ALPHA
// A song built around chord progressions using play chord() in v3 mode.
// Uses v3 shorthand: chord inversions, voicings, and voice leading.
// Run from project root: py ep.py compile examples/v3-compositions/chord_song_v3.e
// ====================================================================

@bpm 90                                 // Moderate ballad tempo
@sig 4/4                                // Common time

// -------------------------------------------------------------------
// v3 Chord Syntax:
// play chord(ROOT, TYPE, INVERSION, DURATION)
// Types: "maj", "min", "dim", "aug", "7", "maj7", "min7", "dom7"
// Inversions: 0 = root, 1 = first, 2 = second, 3 = third
// Example: play chord(C, "maj7", 1, 2.0)
// -------------------------------------------------------------------

// -------------------------------------------------------------------
// VERSE 1 (bars 1–8)
// I — vi — IV — V — I — ii — V — I
// Classic pop progression, gently arpeggiated
// -------------------------------------------------------------------
section "Verse 1"

@vel 60                                 // Piano dynamic, gentle

// Bar 1: I — C major in root position
play chord(C, "maj", 0, 4.0)

// Bar 2: vi — A minor, first inversion (smoother voice leading)
play chord(A, "min", 1, 4.0)

// Bar 3: IV — F major, second inversion
play chord(F, "maj", 2, 4.0)

// Bar 4: V — G dominant 7, root position (creates tension)
play chord(G, "dom7", 0, 4.0)

// Bar 5: I — C major, first inversion
play chord(C, "maj", 1, 4.0)

// Bar 6: ii — D minor, root position
play chord(D, "min", 0, 4.0)

// Bar 7: V — G7, third inversion (leading tone in bass)
play chord(G, "dom7", 3, 4.0)

// Bar 8: I — C major, root position (resolution)
play chord(C, "maj", 0, 4.0)

// -------------------------------------------------------------------
// VERSE 2 (bars 9–16)
// Same progression, different voicings, more sustained
// -------------------------------------------------------------------
section "Verse 2"

@vel 65                                 // Slightly fuller

// Voice leading: keep common tones, move inner voices minimally
play chord(C, "maj7", 0, 4.0)           // Cmaj7 — warmer color
play chord(A, "min7", 0, 4.0)           // Am7 — relative minor
play chord(F, "maj7", 1, 4.0)           // Fmaj7 — first inversion, A in bass
play chord(G, "dom7", 0, 4.0)           // G7 — dominant preparation
play chord(C, "maj7", 2, 4.0)           // Cmaj7 — second inversion, G in bass
play chord(D, "min7", 1, 4.0)           // Dm7 — first inversion, F in bass
play chord(G, "dom7", 2, 3.0)           // G7 — second inversion, D in bass
play chord(G, "dom7", 0, 1.0)           // G7 — root, short, leading to...
play chord(C, "maj7", 0, 4.0)           // I — resolved

// -------------------------------------------------------------------
// CHORUS (bars 17–24)
// IV — V — iii — vi — ii — V — I
// Bright, uplifting chorus progression
// -------------------------------------------------------------------
section "Chorus"

@vel 75                                 // Forte

play chord(F, "maj", 0, 3.0)            // IV — subdominant
play chord(F, "maj", 1, 1.0)            // IV — lift to first inversion
play chord(G, "dom7", 0, 4.0)           // V — dominant
play chord(E, "min", 1, 3.0)            // iii — mediant, first inversion
play chord(E, "min", 0, 1.0)            // Root position landing
play chord(A, "min", 0, 2.0)            // vi — submediant
play chord(A, "min", 2, 2.0)            // Second inversion, move to...
play chord(D, "min", 0, 2.0)            // ii — supertonic
play chord(D, "min", 1, 2.0)            // First inversion
play chord(G, "dom7", 0, 3.0)           // V — build tension
play chord(G, "dom7", 3, 1.0)           // V — third inversion, resolving
play chord(C, "maj", 0, 4.0)            // I — triumphant return

// -------------------------------------------------------------------
// BRIDGE (bars 25–32)
// i — bIII — bVII — IV in C minor (parallel minor modulation)
// Modal shift adds emotional depth
// -------------------------------------------------------------------
section "Bridge"

@vel 55 to 70 arc                       // Crescendo through bridge

play chord(C, "min", 0, 3.0)            // i — C minor, dark turn
play chord(C, "min", 2, 1.0)            // i — second inversion
play chord(Eb, "maj", 0, 4.0)           // bIII — Eb major, relative major
play chord(Bb, "maj", 2, 3.0)           // bVII — Bb major, second inversion
play chord(Bb, "maj", 0, 1.0)           // bVII — root
play chord(F, "min", 0, 2.0)            // iv — F minor, subdominant
play chord(F, "min", 1, 2.0)            // First inversion
play chord(G, "dom7", 0, 2.0)           // V — dominant in C minor
play chord(G, "dom7", 3, 2.0)           // Third inversion
play chord(Ab, "maj", 0, 2.0)           // bVI — Ab major, surprise
play chord(G, "dom7", 0, 2.0)           // V — pull back
play chord(C, "maj", 0, 4.0)            // Picardy third! Ends on C major

// -------------------------------------------------------------------
// FINAL CHORUS (bars 33–40)
// Full expression, richer voicings, wider range
// -------------------------------------------------------------------
section "Final Chorus"

@vel 80                                 // Fortissimo

play chord(F, "maj7", 2, 4.0)           // IVmaj7 — lush
play chord(G, "dom7", 1, 4.0)           // V7 — first inversion
play chord(E, "min7", 0, 3.0)           // iii7
play chord(E, "min7", 2, 1.0)
play chord(A, "min7", 0, 4.0)           // vi7
play chord(D, "min7", 1, 2.0)           // ii7
play chord(D, "min7", 0, 2.0)
play chord(G, "dom7", 0, 2.0)           // V7
play chord(G, "dom7", 2, 2.0)           // V7 — second inversion
play chord(C, "maj7", 0, 6.0)           // Imaj7 — final, sustained

// -------------------------------------------------------------------
// CODA (bars 41–44)
// Gentle plagal cadence — IV → I (Amen cadence)
// -------------------------------------------------------------------
section "Coda"

@vel 50 to 30 arc decrescendo           // Fade to silence

play chord(F, "maj7", 1, 4.0)           // IV — Amen
play chord(C, "maj7", 0, 8.0)           // I — final rest

// Total: 44 bars, 44 chord events, ~1:58 at @bpm 90
