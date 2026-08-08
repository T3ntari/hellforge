#!/usr/bin/env python3
"""
e2midi.py — Convert E Language (.e) to Standard MIDI Files (.mid)

Usage:
    python e2midi.py input.e [-o output.mid] [--bpm 120]

Parses a #MACHINE token stream, converts absolute timestamps and
durations to MIDI delta ticks, and writes a standard .mid file.
"""

import argparse
import os
import re
import sys

try:
    import mido
except ImportError:
    print("Error: mido is required. Install with: pip install mido", file=sys.stderr)
    sys.exit(1)


TICKS_PER_BEAT = 480


def ms_to_ticks(ms, tempo_bpm):
    """Convert milliseconds to MIDI ticks at given tempo."""
    us_per_beat = 60_000_000 / tempo_bpm
    ticks_per_us = TICKS_PER_BEAT / us_per_beat
    return int(round(ms * 1000 * ticks_per_us))


def parse_e_file(e_path):
    """Parse any .e file using ep.py's unified parser (handles v1, v2, variables, .ee, .eic)."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    try:
        from ep import (
            get_input_events,
            parse_e_text,
        )
    except ImportError:
        # Fallback to old parser if ep.py not available
        return _legacy_parse(e_path)

    # Check if it's a .ee or .eic file
    if e_path.endswith(('.ee', '.eic')):
        events, bpm = get_input_events(e_path)
        # Convert to format expected by this tool
        result = []
        for e in events:
            result.append({
                "timestamp": e["timestamp"],
                "midi": e["midi"],
                "duration": e["duration"],
                "velocity": e["velocity"],
            })
        return result, bpm

    # Read raw text, resolve variables, detect v2
    with open(e_path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    # Check for v2 syntax
    v2_patterns = ['[Section:', 'Key:', 'Tempo:', 'play(', 'arpeggio(', 'chromatic_run(']
    if any(p in text for p in v2_patterns):
        events, bpm = get_input_events(e_path)
        result = []
        for e in events:
            result.append({
                "timestamp": e["timestamp"],
                "midi": e["midi"],
                "duration": e["duration"],
                "velocity": e["velocity"],
            })
        return result, bpm

    # Use legacy parser for v1
    return _legacy_parse(e_path)


def _legacy_parse(e_path):
    """Original v1 #MACHINE parser (fallback)."""
    with open(e_path, "r", encoding="utf-8") as f:
        content = f.read()

    bpm = 120
    events = []

    machine_re = re.compile(
        r"T(?P<ts>\d+)\s+"
        r"N(?P<midi>\d+)\s*"
        r"(?:D(?P<dur>\d+))?\s*"
        r"(?:V(?P<vel>[\d.]+))?\s*"
        r"(?P<fx>(?:P\[bend:[^\]]+\]\s*|S\[pan:[^\]]+\]\s*)*)"
    )

    bpm_re = re.compile(r"@bpm\s+(\d+(?:\.\d+)?)", re.IGNORECASE)
    comment_re = re.compile(r"//.*$", re.MULTILINE)

    content_no_comments = comment_re.sub("", content)

    bpm_match = bpm_re.search(content_no_comments)
    if bpm_match:
        bpm = float(bpm_match.group(1))

    for line in content_no_comments.split("\n"):
        line = line.strip()
        if not line or line.startswith("@") or line.startswith("#"):
            continue

        match = machine_re.search(line)
        if match:
            ts = int(match.group("ts"))
            midi = int(match.group("midi"))
            dur = int(match.group("dur")) if match.group("dur") else 500
            vel = float(match.group("vel")) if match.group("vel") else 0.8
            events.append({
                "timestamp": ts,
                "midi": midi,
                "duration": dur,
                "velocity": min(127, max(0, int(round(vel * 127)))),
            })

    events.sort(key=lambda e: e["timestamp"])
    return events, bpm


def write_midi(events, bpm, output_path):
    """Write parsed events to a .mid file with proper interleaving."""
    if not events:
        print("Warning: no note events found, writing empty MIDI", file=sys.stderr)

    midi_file = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    midi_file.tracks.append(track)

    us_per_beat = int(60_000_000 / bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=us_per_beat, time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4, clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
    track.append(mido.MetaMessage("track_name", name="E Language Import", time=0))

    midi_events = []
    for ev in events:
        start_tick = ms_to_ticks(ev["timestamp"], bpm)
        end_tick = ms_to_ticks(ev["timestamp"] + ev["duration"], bpm)
        vel = ev["velocity"]
        midi_events.append((start_tick, "note_on", ev["midi"], max(1, vel)))
        midi_events.append((end_tick, "note_off", ev["midi"], 0))

    midi_events.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))

    current_tick = 0
    for tick, etype, note, vel in midi_events:
        delta = max(0, tick - current_tick)
        if etype == "note_on":
            track.append(mido.Message("note_on", note=note, velocity=vel, time=delta))
        else:
            track.append(mido.Message("note_off", note=note, velocity=0, time=delta))
        current_tick = tick

    final_tick = ms_to_ticks(
        max((e["timestamp"] + e["duration"] for e in events), default=0) + 2000, bpm
    )
    track.append(mido.MetaMessage("end_of_track", time=max(0, final_tick - current_tick)))

    midi_file.save(output_path)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Convert E language files (.e) to MIDI (.mid)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python e2midi.py song.e
  python e2midi.py song.e -o song.mid
  python e2midi.py song.e --bpm 140
  python e2midi.py *.e --outdir ./midi_files
        """,
    )
    parser.add_argument("input", nargs="+", help="Input .e file(s)")
    parser.add_argument("-o", "--output", help="Output .mid file (single input only)")
    parser.add_argument("--outdir", default=".", help="Output directory for batch conversions")
    parser.add_argument("--bpm", type=float, help="Override tempo (default: from .e file)")

    args = parser.parse_args()

    if len(args.input) > 1 and args.output:
        print("Error: -o/--output cannot be used with multiple input files", file=sys.stderr)
        sys.exit(1)

    success = 0
    for e_path in args.input:
        if not os.path.exists(e_path):
            print(f"Error: file not found: {e_path}", file=sys.stderr)
            continue

        try:
            events, file_bpm = parse_e_file(e_path)
        except Exception as e:
            print(f"Error parsing {e_path}: {e}", file=sys.stderr)
            continue

        bpm = args.bpm or file_bpm

        if len(args.input) == 1 and args.output:
            out_path = args.output
        else:
            base = os.path.splitext(os.path.basename(e_path))[0]
            out_path = os.path.join(args.outdir, base + ".mid")

        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

        try:
            write_midi(events, bpm, out_path)
            print(f"Converted {e_path} -> {out_path}")
            print(f"  Tempo: {bpm:.0f} BPM")
            print(f"  Notes: {len(events)}")
            duration_s = (max(e["timestamp"] + e["duration"] for e in events) / 1000) if events else 0
            print(f"  Duration: {duration_s:.2f}s")
            success += 1
        except Exception as e:
            print(f"Error writing {out_path}: {e}", file=sys.stderr)

    if success == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
