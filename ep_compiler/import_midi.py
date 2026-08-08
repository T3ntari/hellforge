"""MIDI file importer — converts .mid to E events, source code, and full projects.
Also handles .ec binary import."""

import os
import struct
import collections

# Duration code mapping (ms at 120 BPM → note values)
DUR_CODES = [
    (2000, "w"), (1000, "h"), (500, "q"), (250, "e"),
    (125, "s"), (62, "t"), (31, "sf"),
]
VEL_NAMES = {
    16: "ppp", 33: "pp", 49: "p", 64: "mp",
    80: "mf", 96: "f", 112: "ff", 126: "fff",
}


def _dur_to_code(ms, bpm):
    scaled = ms * (120.0 / bpm)
    for val, code in DUR_CODES:
        if scaled >= val * 0.7:
            return code
    return "sf"


def _vel_to_name(vel):
    best = "mf"
    for v, name in sorted(VEL_NAMES.items()):
        if abs(vel - v) < abs(vel - [k for k in VEL_NAMES if True][0] if False else 127):
            pass
        if abs(vel - v) <= 15:
            return name
    return "mf"


def import_midi(midi_path):
    """Parse a MIDI file into E events.
    Returns: (events: list[dict], bpm: float)
    """
    try:
        import mido
    except ImportError:
        print("Error: mido required for MIDI import")
        return [], 120

    mid = mido.MidiFile(midi_path)
    bpm = 120

    note_starts = {}
    events = []

    for track in mid.tracks:
        t = 0
        for msg in track:
            t += msg.time
            if msg.type == "set_tempo":
                bpm = mido.tempo2bpm(msg.tempo)
            elif msg.type == "note_on" and msg.velocity > 0:
                note_starts[(msg.note, msg.channel)] = (t, msg.velocity, msg.channel)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                start = note_starts.pop((msg.note, msg.channel), None)
                if start:
                    start_tick, vel, ch = start
                    if t > start_tick:
                        ts_ms = start_tick * 60000 / (bpm * mid.ticks_per_beat)
                        dur_ms = (t - start_tick) * 60000 / (bpm * mid.ticks_per_beat)
                        events.append({
                            "timestamp": int(ts_ms),
                            "midi": msg.note,
                            "duration": max(1, int(dur_ms)),
                            "velocity": vel,
                            "channel": ch,
                        })

    events.sort(key=lambda e: e["timestamp"])
    return events, bpm


# ── Human syntax source generation ──────────

def _events_by_channel(events):
    """Group events by channel. Returns dict channel -> [events]."""
    ch_groups = collections.defaultdict(list)
    for e in events:
        ch = e.get("channel", 0)
        ch_groups[ch].append(e)
    return dict(ch_groups)


def _human_event_line(e, bpm):
    """Convert a single event to human syntax: play note(C4) @dur:q @vel:mf @time:ts
    Preserves original note duration as exact ms."""
    from .events import midi_to_name
    name = midi_to_name(e["midi"])
    dur_ms = max(10, min(e["duration"], 5000))
    dur_str = f"{int(dur_ms)}ms"
    vel = min(127, max(1, e.get("velocity", 80)))
    vel_name = _vel_to_name(vel)
    ts = e.get("timestamp", 0)
    ch = e.get("channel")
    parts = f"play note({name}) @dur:{dur_str} @vel:{vel_name}"
    if ts is not None and ts > 0:
        parts += f" @time:{ts}"
    if ch is not None:
        parts += f" @ch:{ch}"
    return parts


def _code_to_ms(code, bpm):
    """Convert a duration code back to ms at given BPM."""
    for val, c in DUR_CODES:
        if c == code:
            return val * (bpm / 120.0) if bpm > 0 else val
    return 500


def events_to_e_source(events, bpm, human=True):
    """Convert E events to .e source code.
    If human=True, uses play note(C4) @dur:q @vel:mf syntax.
    If human=False, uses T0 N60 D500 V80 machine syntax.
    """
    if human:
        lines = [f"@bpm {int(bpm)}"]
        for e in sorted(events, key=lambda x: x["timestamp"]):
            lines.append(_human_event_line(e, bpm))
        return "\n".join(lines)
    else:
        lines = [f"@bpm {int(bpm)}"]
        ch_map = {}
        for e in sorted(events, key=lambda x: x["timestamp"]):
            ts = e["timestamp"]
            midi = e["midi"]
            dur = e["duration"]
            vel = min(127, max(1, e.get("velocity", 80)))
            ch = e.get("channel")
            if ch is not None and ch not in ch_map:
                ch_map[ch] = len(ch_map)
            prefix = f"CH[{ch}] " if ch is not None else ""
            lines.append(f"{prefix}T{ts} N{midi} D{dur} V{vel}")
        return "\n".join(lines)


def midi_to_e_project(midi_path, output_dir, name=None):
    """Convert MIDI to a full E project with index.ei, parts/*.e, and project.enx.
    Returns output_dir path.
    """
    events, bpm = import_midi(midi_path)
    if not events:
        return None

    os.makedirs(output_dir, exist_ok=True)
    parts_dir = os.path.join(output_dir, "parts")
    os.makedirs(parts_dir, exist_ok=True)

    project_name = name or os.path.splitext(os.path.basename(midi_path))[0]
    ch_groups = _events_by_channel(events)

    # Write part files
    part_names = {}
    for ch in sorted(ch_groups):
        ch_events = ch_groups[ch]
        ch_events.sort(key=lambda e: e["timestamp"])
        label = f"part_ch{ch}"
        part_names[ch] = label
        part_path = os.path.join(parts_dir, f"{label}.e")
        src = events_to_e_source(ch_events, bpm, human=True)
        with open(part_path, "w", encoding="utf-8") as f:
            f.write(f"// Channel {ch}\n")
            f.write(src)

    # Write index.ei
    ei_lines = [f'project "{project_name}"', f'tempo {int(bpm)}', ""]
    for ch in sorted(ch_groups):
        label = part_names[ch]
        ei_lines.append(f'include "parts/{label}.e" as {label}')
    ei_lines.append("")
    ei_lines.append('section "Main" {')
    for ch in sorted(ch_groups):
        label = part_names[ch]
        ei_lines.append(f"    play {label}")
    ei_lines.append("}")

    with open(os.path.join(output_dir, "index.ei"), "w", encoding="utf-8") as f:
        f.write("\n".join(ei_lines))

    # Write project.enx if multiple channels
    if len(ch_groups) > 1:
        enx_lines = [f"#ENX v1", f'project "{project_name}"', "", 'order "index.ei"']
        with open(os.path.join(output_dir, "project.enx"), "w", encoding="utf-8") as f:
            f.write("\n".join(enx_lines))

    print(f"  ✓ Project: {output_dir}/")
    print(f"    index.ei  ({len(ch_groups)} parts)")
    if len(ch_groups) > 1:
        print(f"    project.enx")
    print(f"    parts/ ({len(ch_groups)} files, {len(events)} notes)")
    return output_dir


# ── .ec binary import ──────────────────────

def import_ec(ec_path):
    """Read a .ec binary file back into events. Returns (events, bpm)."""
    events = []
    bpm = 120
    with open(ec_path, "rb") as f:
        magic = f.read(4)
        if magic[:2] != b"EC":
            print("  Not a valid .ec file")
            return [], 120
        bpm = struct.unpack("<f", f.read(4))[0]
        count = struct.unpack("<I", f.read(4))[0]
        total_dur = struct.unpack("<I", f.read(4))[0]
        f.read(8)  # reserved
        for _ in range(count):
            data = f.read(12)
            if len(data) < 12:
                break
            ts, midi_raw, dur, vel_raw, pan, bend = struct.unpack("<IBHBhh", data)
            events.append({
                "timestamp": ts,
                "midi": midi_raw & 0xFF,
                "duration": dur,
                "velocity": vel_raw & 0xFF,
                "pan": pan / 32767.0 if pan else 0.0,
                "bend": bend / 512.0 if bend else 0,
            })
    events.sort(key=lambda e: e["timestamp"])
    return events, bpm
