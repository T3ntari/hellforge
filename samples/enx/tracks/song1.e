/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */
// .enx album root — ordered track listing
   File:       tracks/song1.e
   Version:    v4 (album track) — referenced by album.enx
   Status:     CURRENT STANDARD
   
   First track of the album defined in album.enx.
   This is a standalone .e file that can be compiled independently
   or played as part of the album track listing.

/* @title "Track One" — Track title metadata.
   Displayed by the player when this track begins. */
@title "Track One"

/* @bpm 120 — Track-specific tempo.
   Tempo can differ between tracks in an album. */
@bpm 120

/* A simple but complete song structure in v4 syntax:
   Intro -> Main Riff -> Variation -> Outro */

/* Intro — Two ascending notes to establish key. */
C4 q
G4 q

/* Main riff — repeated 4 times. */
repeat 4 {
    C4 e
    E4 e
    G4 e
    C5 e
}

/* Variation — similar pattern with different ending. */
repeat 2 {
    C4 e
    D4 e
    E4 e
    F4 e
}

/* Outro — Descending arpeggio to close. */
C5 q
G4 q
E4 q
C4 w

/* This track is compiled to tracks/song1.bin
   and played by the album player when album.enx references it. */

// Run from project root: py ep.py compile samples/enx/tracks/song1.e
