/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// v3 FULLY SUPPORTED — current alongside v4
   File:       channels.e
   Version:    v3 (consolidated engine) — FULLY SUPPORTED
   Status:     FULLY SUPPORTED
   
   Demonstrates multi-channel output in v3.
   Channels let you assign notes to different MIDI tracks/instruments.
   Useful for multi-timbral arrangements or layered sounds.

/* CH0, CH1, CH2 = Channel identifiers.
   HELLFORGE supports up to 16 MIDI channels (0-15).

   CH0 is the default channel if none is specified.
   Each channel can have a different MIDI instrument (program change).

   Use case example:
     CH0 = Piano (program 0)
     CH1 = Strings (program 48)
     CH2 = Bass (program 32)

   Syntax: CH<N> Note Duration [Velocity]
*/

/* CH0 — Piano channel (program 0 by default).
   Plays a C major scale ascending. */
CH0 C4 q      /* C4 on piano */
CH0 D4 q      /* D4 on piano */
CH0 E4 q      /* E4 on piano */
CH0 F4 q      /* F4 on piano */
CH0 G4 q      /* G4 on piano */

/* CH1 — Secondary channel (could be pads/strings).
   Plays sustained chords underneath the piano melody. */
CH1 C3 h      /* C3 half note — root chord tone on channel 1 */
CH1 E3 h      /* E3 half note — third of the chord on channel 1 */
CH1 G3 h      /* G3 half note — fifth of the chord on channel 1 */

/* CH2 — Bass channel, playing octave jumps.
   Bass notes are lower and rhythmically simple. */
CH2 C2 w      /* C2 whole note — bass drone on channel 2 */
CH2 C2 w      /* C2 held for another measure */

/* Multi-channel output creates layered arrangements:
   - Channel 0: melodic line (treble)
   - Channel 1: harmonic pad (mid)
   - Channel 2: bass foundation (low)
   This gives a full, rich texture from a single E file. */

// Run from project root: py ep.py compile samples/v3-supported/basics/channels.e
