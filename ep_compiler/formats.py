"""Output format handlers: MIDI, WAV, MP3, MP4, EC, EIC."""

import os
import struct
import json
import subprocess
import sys
import tempfile

from .events import (
    validate_events,
    sort_events,
)
import numpy as np

TICKS_PER_BEAT = 480

# Velocity normalization: auto-boost quiet files
def normalize_velocities(events):
    """Apply velocity curve to ensure audible dynamic range.
    Detects files with avg velocity < 40 and applies a sqrt-based boost.
    This fixes MIDI imports that have overly quiet velocity values."""
    if not events:
        return events
    vels = np.array([e.get("velocity", 80) for e in events])
    avg_vel = np.mean(vels)
    max_vel = np.max(vels)

    # Only normalize if the file is unusually quiet (avg < 40)
    if avg_vel >= 40:
        return events

    # Apply sqrt curve: quiet notes get boosted more than loud ones
    # This preserves dynamic shape while raising the overall level
    norm = vels / 127.0
    boosted = np.sqrt(norm) * 127.0
    boosted = np.clip(boosted, 10, 127).astype(int)
    for i, e in enumerate(events):
        e["velocity"] = int(boosted[i])
    print(f"  > Velocity normalized: avg {avg_vel:.0f} -> {np.mean(boosted):.0f}")
    return events


def export_midi(events, bpm, output_path):
    """Export events to standard MIDI file."""
    try:
        import mido
    except ImportError:
        print("Error: mido required for MIDI export")
        return False

    # Auto-normalize velocities for audible output
    events = normalize_velocities(events)

    mid = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
    track = mido.MidiTrack()
    mid.tracks.append(track)

    us_per_beat = int(60_000_000 / bpm)
    track.append(mido.MetaMessage("set_tempo", tempo=us_per_beat, time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4,
                                   clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
    track.append(mido.MetaMessage("track_name", name="E Compilation", time=0))

    # Master volume CC7 on all channels
    master_vol = None
    for e in events:
        if e.get("master_vol") is not None:
            master_vol = e["master_vol"]
            break
    # Send reverb (CC91=40) and chorus (CC93=10) for natural piano ambience,
    # plus pan center and optional master volume
    for ch in range(16):
        if master_vol is not None:
            vol_cc = max(0, min(127, int(float(master_vol) * 127)))
            track.append(mido.Message("control_change", control=7, value=vol_cc, channel=ch, time=0))
        track.append(mido.Message("control_change", control=91, value=40, channel=ch, time=0))   # Reverb ~30% wet
        track.append(mido.Message("control_change", control=93, value=10, channel=ch, time=0))   # Light chorus
        track.append(mido.Message("control_change", control=10, value=64, channel=ch, time=0))  # Pan center

    # Polyphony check: warn if any timestamp exceeds 64 simultaneous notes
    from collections import Counter
    ts_counts = Counter(e["timestamp"] for e in events)
    max_poly = max(ts_counts.values()) if ts_counts else 0
    if max_poly > 64:
        print(f"  > Polyphony warning: {max_poly} simultaneous notes at one point "
              f"(MIDI synths typically support 32-64 voices)")

    # Track used channels for program changes
    channels_used = set()
    midi_events = []
    for e in events:
        ch = e.get("channel")
        if ch is not None:
            channels_used.add(ch)
        st = int(e["timestamp"] * TICKS_PER_BEAT * bpm / 60000)
        et = int((e["timestamp"] + e["duration"]) * TICKS_PER_BEAT * bpm / 60000)
        ch_actual = ch if ch is not None else 0
        is_pedal = (e.get("pedal") is True
                    or (e.get("sustain") is not None and e.get("midi", 0) == 0))
        if e.get("sustain") is not None:
            sustain_val = max(0, min(127, int(e["sustain"])))
            midi_events.append((st, "control_change", 64, sustain_val, ch_actual))
        if not is_pedal:
            vel = max(1, min(127, round(e["velocity"])))
            midi_events.append((st, "note_on", e["midi"], vel, ch_actual))
            midi_events.append((et, "note_off", e["midi"], 0, ch_actual))

    # Program change for each used channel (instrument 0 = Acoustic Grand Piano)
    for ch in sorted(channels_used):
        track.append(mido.Message("program_change", program=0, channel=ch, time=0))

    midi_events.sort(key=lambda x: (x[0], 0 if x[1] == "note_on" else (1 if x[1] == "control_change" else 2)))

    cur = 0
    for tick, etype, *args in midi_events:
        delta = max(0, tick - cur)
        if etype == "control_change":
            control, value, ch = args
            track.append(mido.Message("control_change", control=control, value=value, channel=ch, time=delta))
        elif etype == "note_on":
            note, vel, ch = args
            track.append(mido.Message("note_on", note=note, velocity=vel, channel=ch, time=delta))
        else:
            note, vel, ch = args
            track.append(mido.Message("note_off", note=note, velocity=vel, channel=ch, time=delta))
        cur = tick

    remaining = max(0, midi_events[-1][0] + TICKS_PER_BEAT * 2 - cur) if midi_events else 480
    track.append(mido.MetaMessage("end_of_track", time=remaining))
    mid.save(output_path)
    return True


def export_ec(events, bpm, output_path):
    """Export events to compiled .ec binary format."""
    total_dur = max((e["timestamp"] + e["duration"] for e in events), default=0)
    with open(output_path, "wb") as f:
        f.write(b"EC\x01\x00")
        f.write(struct.pack("<f", bpm))
        f.write(struct.pack("<I", len(events)))
        f.write(struct.pack("<I", total_dur))
        f.write(b"\x00" * 8)
        for e in events:
            pan_scaled = max(-32768, min(32767, int(e.get("pan", 0) * 32767)))
            bend_scaled = max(-32768, min(32767, int(e.get("bend", 0) * 512)))
            f.write(struct.pack("<IBHBhh", e["timestamp"], e["midi"],
                                 min(65535, e["duration"]), e["velocity"],
                                 pan_scaled, bend_scaled))
    return True


def export_wav(events, bpm, output_path, params=None):
    """Render events to WAV/MP3 using FluidSynth or software synth.
    params: optional dict with sample_rate, bit_depth, gain, sub,
    bass_boost, stereo_width, neural (from @sr/@bit/@quality/@gain/
    @sub/@bass_boost/@stereo_width/@neural directives)."""
    import tempfile
    import subprocess
    from .formats import export_midi
    mid_path = tempfile.mktemp(suffix=".mid")
    export_midi(events, bpm, mid_path)
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from piano_synth import render
        result = render(mid_path, output_path, params=params or {})
        if result:
            return True
    except Exception:
        pass
    # Fallback
    result = subprocess.run(["ffmpeg", "-y", "-i", mid_path, "-b:a", "192k", output_path],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    os.unlink(mid_path)
    return result.returncode == 0


def export_eic(source_path, output_path):
    """Export .e/.ei/.enx project to .eic (E Index Clear) bundle format."""
    base_dir = os.path.dirname(os.path.abspath(source_path))
    ext = os.path.splitext(source_path)[1].lower()

    def _write(lines, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        sz = os.path.getsize(path) // 1024
        print(f"  ✓ {path} ({sz}KB)")

    lines = []
    lines.append("// EIC — E Index Clear")
    lines.append(f"// Generated from: {os.path.basename(source_path)}")
    lines.append("")

    if ext == ".enx":
        # Export .enx album: inline all ordered .ei/.e projects
        from .mode_enx import (
            _parse_enx_text,
            read_enx_meta,
        )
        meta = read_enx_meta(source_path)
        raw_text = meta["text"]
        orders = _parse_enx_text(raw_text, base_dir)

        lines.append("// ===== ALBUM ROOT (.enx) =====")
        lines.append(f'project "{meta["project"]}"')
        if meta["composer"]:
            lines.append(f'composer "{meta["composer"]}"')
        lines.append("")
        lines.append("// Original .enx directives:")
        for line in raw_text.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("//"):
                lines.append(stripped)
        lines.append("")
        lines.append("// ===== ORDERED PROJECTS =====")

        part_index = 0
        for ord_path, delay, tempo in orders:
            part_index += 1
            ord_ext = os.path.splitext(ord_path)[1].lower()
            label = f"order_{part_index}"
            lines.append(f"")
            lines.append(f"// --- Order {part_index}: {os.path.relpath(ord_path, base_dir)} ---")
            delay_str = f" at {delay}ms" if delay else ""
            tempo_str = f" tempo {int(tempo)}" if tempo else ""
            lines.append(f'// order "{os.path.relpath(ord_path, base_dir)}"{delay_str}{tempo_str}')

            if ord_ext == ".ei":
                from .e_runtime import load_ei
                proj = load_ei(ord_path)
                if proj:
                    lines.append(f"// Project: {proj.name}")
                    for pname in sorted(proj.parts):
                        lines.append(f"//   Part: {pname}")
                    for pname in sorted(proj.parts):
                        lines.append(f"")
                        lines.append(f"// ===== {os.path.relpath(ord_path, base_dir)} :: {pname} =====")
                        src = proj.parts[pname].strip()
                        lines.append(src)
                else:
                    lines.append(f"//  (could not load .ei project)")
            elif ord_ext == ".e":
                with open(ord_path, "r", encoding="utf-8", errors="replace") as f:
                    src = f.read().strip()
                lines.append(f"// ===== {os.path.relpath(ord_path, base_dir)} =====")
                lines.append(src)
            else:
                lines.append(f"//  (unsupported file type: {ord_ext})")

        _write(lines, output_path)
        return True

    elif ext == ".ei":
        # Read index and include all parts inline
        from .e_runtime import load_ei
        proj = load_ei(source_path)
        if proj:
            lines.append("// ===== PROJECT INDEX =====")
            lines.append(f'project "{proj.name}"')
            if proj.composer:
                lines.append(f'composer "{proj.composer}"')
            lines.append(f"tempo {int(proj.bpm)}")
            for pname in sorted(proj.parts):
                rel = f"parts/{pname}"
                lines.append(f'include "{rel}" as {pname}')
            lines.append("")
            lines.append('section "Main" {')
            for pname in sorted(proj.parts):
                lines.append(f"    play {pname}")
            lines.append("}")
            lines.append("")
            for pname in sorted(proj.parts):
                lines.append(f"// ===== parts/{pname} =====")
                src = proj.parts[pname].strip()
                lines.append(src)
                lines.append("")
        _write(lines, output_path)
        return True

    else:
        # Single .e file: embed directly
        with open(source_path, "r", encoding="utf-8", errors="replace") as f:
            src = f.read()
        lines.append("// ===== SOURCE =====")
        lines.append(src.strip())
        _write(lines, output_path)
        return True
