#!/usr/bin/env python3
"""
midi2e.py — Convert Standard MIDI Files (.mid) to E Language (.e)

Reads any .mid file via music21 (handles corrupted/complex MIDI),
pairs note_on/note_off events, computes absolute timestamps and
durations in milliseconds, and emits a stateless #MACHINE token
stream that any E compiler can ingest.

Usage:
    python midi2e.py input.mid [-o output.e] [--bpm 120]
    python midi2e.py *.mid --outdir ./e_files
"""

import argparse
import os
import sys

try:
    import music21 as m21
except ImportError:
    print("Error: music21 is required. Install with: pip install music21", file=sys.stderr)
    sys.exit(1)


INSTRUMENT_NAMES = {
    0: "Acoustic Grand Piano", 1: "Bright Acoustic Piano",
    2: "Electric Grand Piano", 3: "Honky-tonk Piano",
    4: "Electric Piano 1", 5: "Electric Piano 2",
    6: "Harpsichord", 7: "Clavi",
    8: "Celesta", 9: "Glockenspiel",
    10: "Music Box", 11: "Vibraphone",
    12: "Marimba", 13: "Xylophone",
    14: "Tubular Bells", 15: "Dulcimer",
    16: "Drawbar Organ", 17: "Percussive Organ",
    18: "Rock Organ", 19: "Church Organ",
    20: "Reed Organ", 21: "Accordion",
    22: "Harmonica", 23: "Tango Accordion",
    24: "Acoustic Guitar (nylon)", 25: "Acoustic Guitar (steel)",
    26: "Electric Guitar (jazz)", 27: "Electric Guitar (clean)",
    28: "Electric Guitar (muted)", 29: "Overdriven Guitar",
    30: "Distortion Guitar", 31: "Guitar Harmonics",
    32: "Acoustic Bass", 33: "Electric Bass (finger)",
    34: "Electric Bass (pick)", 35: "Fretless Bass",
    36: "Slap Bass 1", 37: "Slap Bass 2",
    38: "Synth Bass 1", 39: "Synth Bass 2",
    40: "Violin", 41: "Viola",
    42: "Cello", 43: "Contrabass",
    44: "Tremolo Strings", 45: "Pizzicato Strings",
    46: "Orchestral Harp", 47: "Timpani",
    48: "String Ensemble 1", 49: "String Ensemble 2",
    50: "Synth Strings 1", 51: "Synth Strings 2",
    52: "Choir Aahs", 53: "Voice Oohs",
    54: "Synth Voice", 55: "Orchestra Hit",
    56: "Trumpet", 57: "Trombone",
    58: "Tuba", 59: "Muted Trumpet",
    60: "French Horn", 61: "Brass Section",
    62: "Synth Brass 1", 63: "Synth Brass 2",
    64: "Soprano Sax", 65: "Alto Sax",
    66: "Tenor Sax", 67: "Baritone Sax",
    68: "Oboe", 69: "English Horn",
    70: "Bassoon", 71: "Clarinet",
    72: "Piccolo", 73: "Flute",
    74: "Recorder", 75: "Pan Flute",
    76: "Blown Bottle", 77: "Shakuhachi",
    78: "Whistle", 79: "Ocarina",
    80: "Lead 1 (square)", 81: "Lead 2 (sawtooth)",
    82: "Lead 3 (calliope)", 83: "Lead 4 (chiff)",
    84: "Lead 5 (charang)", 85: "Lead 6 (voice)",
    86: "Lead 7 (fifths)", 87: "Lead 8 (bass + lead)",
    88: "Pad 1 (new age)", 89: "Pad 2 (warm)",
    90: "Pad 3 (polysynth)", 91: "Pad 4 (choir)",
    92: "Pad 5 (bowed)", 93: "Pad 6 (metallic)",
    94: "Pad 7 (halo)", 95: "Pad 8 (sweep)",
    96: "FX 1 (rain)", 97: "FX 2 (soundtrack)",
    98: "FX 3 (crystal)", 99: "FX 4 (atmosphere)",
    100: "FX 5 (brightness)", 101: "FX 6 (goblins)",
    102: "FX 7 (echoes)", 103: "FX 8 (sci-fi)",
    104: "Sitar", 105: "Banjo",
    106: "Shamisen", 107: "Koto",
    108: "Kalimba", 109: "Bagpipe",
    110: "Fiddle", 111: "Shanai",
    112: "Tinkle Bell", 113: "Agogo",
    114: "Steel Drums", 115: "Woodblock",
    116: "Taiko Drum", 117: "Melodic Tom",
    118: "Synth Drum", 119: "Reverse Cymbal",
    120: "Guitar Fret Noise", 121: "Breath Noise",
    122: "Seashore", 123: "Bird Tweet",
    124: "Telephone Ring", 125: "Helicopter",
    126: "Applause", 127: "Gunshot",
}

DRUM_KIT_NAMES = {
    35: "Acoustic Bass Drum", 36: "Bass Drum 1",
    37: "Side Stick", 38: "Acoustic Snare",
    39: "Hand Clap", 40: "Electric Snare",
    41: "Low Floor Tom", 42: "Closed Hi-Hat",
    43: "High Floor Tom", 44: "Pedal Hi-Hat",
    45: "Low Tom", 46: "Open Hi-Hat",
    47: "Low-Mid Tom", 48: "Hi-Mid Tom",
    49: "Crash Cymbal 1", 50: "High Tom",
    51: "Ride Cymbal 1", 52: "Chinese Cymbal",
    53: "Ride Bell", 54: "Tambourine",
    55: "Splash Cymbal", 56: "Cowbell",
    57: "Crash Cymbal 2", 58: "Vibraslap",
    59: "Ride Cymbal 2", 60: "Hi Bongo",
    61: "Low Bongo", 62: "Mute Hi Conga",
    63: "Open Hi Conga", 64: "Low Conga",
    65: "High Timbale", 66: "Low Timbale",
    67: "High Agogo", 68: "Low Agogo",
    69: "Cabasa", 70: "Maracas",
    71: "Short Whistle", 72: "Long Whistle",
    73: "Short Guiro", 74: "Long Guiro",
    75: "Claves", 76: "Hi Wood Block",
    77: "Low Wood Block", 78: "Mute Cuica",
    79: "Open Cuica", 80: "Mute Triangle",
    81: "Open Triangle",
}


def _ql_to_ms(ql, bpm):
    """Convert quarter length to milliseconds at given BPM."""
    beat_ms = 60000.0 / bpm
    return int(round(ql * beat_ms))


def _extract_notes_from_part(part, bpm):
    """Extract (midi_note, start_ms, dur_ms, velocity) from a music21 part."""
    notes_out = []
    try:
        flat = part.flatten()
    except Exception:
        return notes_out

    for n in flat.notes:
        try:
            ql = n.quarterLength
            dur_ms = _ql_to_ms(ql, bpm)

            if n.isChord:
                for sub in n:
                    try:
                        pitch = sub.pitch.midi
                        vel = sub.volume.velocity if hasattr(sub, 'volume') and sub.volume else 80
                        start_offset = 0
                        notes_out.append((pitch, start_offset, dur_ms, int(vel)))
                    except Exception:
                        continue
            elif n.isNote:
                try:
                    pitch = n.pitch.midi
                    vel = n.volume.velocity if hasattr(n, 'volume') and n.volume else 80
                    notes_out.append((pitch, 0, dur_ms, int(vel)))
                except Exception:
                    continue
        except Exception:
            continue

    return notes_out


def _get_instrument_name(part):
    """Try to extract instrument name from a music21 part."""
    try:
        instr = part.getInstrument()
        if instr and instr.instrumentName:
            return instr.instrumentName
    except Exception:
        pass
    try:
        if part.partName:
            return part.partName
    except Exception:
        pass
    return None


def convert_midi(midi_path, output_path, force_bpm=None):
    """Convert a .mid file to .e format using music21."""
    try:
        score = m21.converter.parse(midi_path)
    except Exception as e:
        print(f"Error reading MIDI file: {e}", file=sys.stderr)
        return False

    # Determine BPM
    if force_bpm:
        bpm = force_bpm
    else:
        try:
            mm = score.metronomeMarkBoundaries()
            bpm = mm[0][2].number if mm else 120
        except Exception:
            bpm = 120

    lines = []
    lines.append("#MACHINE")
    lines.append(f"// Generated by midi2e.py from {os.path.basename(midi_path)}")
    lines.append(f"// Tempo: {bpm:.0f} BPM")
    try:
        dur_ql = score.duration.quarterLength
        dur_s = (dur_ql * 60.0) / bpm
        lines.append(f"// Duration: {dur_s:.2f}s ({dur_ql:.1f} quarter notes)")
    except Exception:
        lines.append("// Duration: unknown")
    lines.append(f"// Parts: {len(score.parts)}")
    lines.append(f"@bpm {bpm:.0f}")
    lines.append("")

    # Collect all note events with absolute timestamps
    all_events = []
    total_notes = 0

    for part_idx, part in enumerate(score.parts):
        try:
            flat = part.flatten()
        except Exception:
            continue

        inst_name = _get_instrument_name(part) or f"Part {part_idx}"
        notes_in_part = 0
        part_events = []

        for n in flat.notes:
            try:
                ql = n.quarterLength
                start_ql = n.offset if hasattr(n, 'offset') else 0
                dur_ms = _ql_to_ms(ql, bpm)
                start_ms = _ql_to_ms(start_ql, bpm)

                if n.isChord:
                    for sub in n:
                        try:
                            pitch = sub.pitch.midi
                            vel = int(sub.volume.velocity) if hasattr(sub, 'volume') and sub.volume else 80
                            part_events.append((start_ms, pitch, max(1, dur_ms), vel))
                            notes_in_part += 1
                        except Exception:
                            continue
                elif n.isNote:
                    try:
                        pitch = n.pitch.midi
                        vel = int(n.volume.velocity) if hasattr(n, 'volume') and n.volume else 80
                        part_events.append((start_ms, pitch, max(1, dur_ms), vel))
                        notes_in_part += 1
                    except Exception:
                        continue
            except Exception:
                continue

        lines.append(f"// Part {part_idx}: {inst_name}")
        if part_events:
            lines.append(f"//   Notes: {notes_in_part}")
            is_drum = any(p > 127 for _, p, _, _ in part_events)
            min_pitch = min(p for _, p, _, _ in part_events)
            max_pitch = max(p for _, p, _, _ in part_events)

            for start_ms, pitch, dur_ms, vel in part_events:
                vel_str = f"{vel / 127:.2f}"
                if is_drum or pitch > 127:
                    drum_name = DRUM_KIT_NAMES.get(pitch, f"Note {pitch}")
                    lines.append(f"T{start_ms} N{pitch} D{dur_ms} V{vel_str} // {drum_name}")
                else:
                    lines.append(f"T{start_ms} N{pitch} D{dur_ms} V{vel_str}")
                all_events.append((start_ms, pitch, dur_ms, vel))
                total_notes += 1
        else:
            lines.append(f"//   (no note events)")

        lines.append("")

    # Add summary
    if all_events:
        total_dur_ms = max(e[0] + e[2] for e in all_events)
        lines.append(f"// Total notes: {total_notes}")
        lines.append(f"// Total duration: {total_dur_ms / 1000:.2f}s")
    lines.append(f"// End of {os.path.basename(midi_path)}")

    content = "\n".join(lines) + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Converted {midi_path} -> {output_path}")
    print(f"  Tempo: {bpm:.0f} BPM")
    print(f"  Parts: {len(score.parts)}")
    print(f"  Notes: {total_notes}")
    if all_events:
        dur_s = max(e[0] + e[2] for e in all_events) / 1000
        print(f"  Duration: {dur_s:.2f}s")
    print(f"  File size: {len(content):,} bytes")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert MIDI files (.mid) to E language (.e) using music21",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python midi2e.py song.mid
  python midi2e.py song.mid -o output.e
  python midi2e.py song.mid --bpm 140
  python midi2e.py *.mid --outdir ./e_files
        """,
    )
    parser.add_argument("input", nargs="+", help="Input .mid file(s)")
    parser.add_argument("-o", "--output", help="Output .e file (single input only)")
    parser.add_argument("--outdir", default=".", help="Output directory for batch conversions")
    parser.add_argument("--bpm", type=float, help="Override tempo (default: from MIDI)")

    args = parser.parse_args()

    if len(args.input) > 1 and args.output:
        print("Error: -o/--output cannot be used with multiple input files", file=sys.stderr)
        sys.exit(1)

    success = 0
    for midi_path in args.input:
        if not os.path.exists(midi_path):
            print(f"Error: file not found: {midi_path}", file=sys.stderr)
            continue

        if len(args.input) == 1 and args.output:
            out_path = args.output
        else:
            base = os.path.splitext(os.path.basename(midi_path))[0]
            safe_base = base.replace(" ", "_").replace("(", "").replace(")", "").replace("+", "plus")
            out_path = os.path.join(args.outdir, safe_base + ".e")

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        if convert_midi(midi_path, out_path, force_bpm=args.bpm):
            success += 1

    if success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
