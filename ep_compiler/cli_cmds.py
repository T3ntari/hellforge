"""Shared implementations for the v5 CLI commands (stats, tracks, inspect,
new, transpose, tempo, merge).

Both eshell.py (do_* handlers) and run.py (subcommands) call into this module
so the two front-ends stay in sync. Functions raise CLIError with a friendly,
user-facing message for bad input; callers print it without a traceback.
"""

import os

from .compile import compile_file
from .events import midi_to_name, sort_events
from .formats import export_midi
from .import_midi import events_to_e_source

SOURCE_EXTS = {".e", ".ei", ".enx", ".eci", ".eic"}
MIDI_EXTS = {".mid", ".midi"}


class CLIError(Exception):
    """Friendly user-facing command error."""


def _is_note(e):
    return not (e.get("pedal") or e.get("sustain") is not None)


def _chan(e):
    c = e.get("channel")
    return c if c is not None else 0


def _fmt_clock(ms):
    total = max(0, int(ms)) / 1000.0
    m, s = divmod(total, 60)
    return f"{int(m)}:{int(s):02d}"


def _read_midi(path):
    """Read a .mid directly with mido, keeping channel + track name per note."""
    import mido
    mid = mido.MidiFile(path)
    bpm = 120
    track_names = {}
    for ti, track in enumerate(mid.tracks):
        for msg in track:
            if msg.type == "track_name":
                track_names[ti] = msg.name
            elif msg.type == "set_tempo":
                bpm = mido.tempo2bpm(msg.tempo)
    events = []
    note_starts = {}
    for ti, track in enumerate(mid.tracks):
        t = 0
        for msg in track:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                note_starts[(msg.note, msg.channel)] = (t, msg.velocity, msg.channel, ti)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                start = note_starts.pop((msg.note, msg.channel), None)
                if start:
                    start_tick, vel, ch, ti0 = start
                    if t > start_tick:
                        scale = 60000.0 / (bpm * mid.ticks_per_beat)
                        events.append({
                            "timestamp": int(start_tick * scale),
                            "midi": msg.note,
                            "duration": max(1, int((t - start_tick) * scale)),
                            "velocity": vel,
                            "channel": ch,
                            "track": track_names.get(ti0),
                        })
    return events, bpm


def load_events(path, bpm=None):
    """Load events + bpm from .e/.ei/.enx/.eci/.eic/.mid inputs.

    bpm overrides the tempo: sources are recompiled at that BPM (word
    durations rescale), MIDI files have their timings scaled by the ratio.
    """
    if not os.path.exists(path):
        raise CLIError(f"Not found: {path}")
    ext = os.path.splitext(path)[1].lower()
    if ext in MIDI_EXTS:
        events, old_bpm = _read_midi(path)
        if bpm is not None and old_bpm:
            ratio = float(bpm) / old_bpm
            for e in events:
                e["timestamp"] = int(e["timestamp"] * ratio)
                e["duration"] = max(1, int(e["duration"] * ratio))
            return events, float(bpm)
        return events, old_bpm
    if ext in SOURCE_EXTS:
        events, bp = compile_file(path, bpm_override=bpm)
        if not events:
            raise CLIError(f"No events compiled from {path}")
        return events, bp
    raise CLIError(f"Unsupported file type {ext!r} — use .e/.ei/.enx/.eci/.eic/.mid")


def _write_output(events, bp, out):
    """Write events to out: .e source when the path ends .e, else MIDI."""
    out = os.path.expanduser(out)
    if os.path.splitext(out)[1].lower() == ".e":
        notes = [e for e in events if _is_note(e)]
        with open(out, "w", encoding="utf-8") as f:
            f.write(events_to_e_source(notes, bp, human=True))
    else:
        export_midi(events, bp, out)


def _max_polyphony(notes):
    pts = []
    for e in notes:
        pts.append((e["timestamp"], 1))
        pts.append((e["timestamp"] + e["duration"], -1))
    pts.sort()
    cur = mx = 0
    for _t, d in pts:
        cur += d
        if cur > mx:
            mx = cur
    return mx


# ── stats ─────────────────────────────────────────────────────────────

def stats_data(path):
    """Compute the stats dict for a file: notes, duration, range, velocity,
    polyphony, density, channels."""
    events, bp = load_events(path)
    notes = [e for e in events if _is_note(e)]
    total_ms = max((e["timestamp"] + e["duration"] for e in events), default=0)
    min_midi = min((e["midi"] for e in notes), default=None)
    max_midi = max((e["midi"] for e in notes), default=None)
    avg_velocity = int(sum(e["velocity"] for e in notes) / len(notes)) if notes else 0
    return {
        "path": path,
        "bpm": bp,
        "events": len(events),
        "notes": len(notes),
        "total_ms": total_ms,
        "min_midi": min_midi,
        "max_midi": max_midi,
        "avg_velocity": avg_velocity,
        "max_velocity": max((e["velocity"] for e in notes), default=0),
        "polyphony": _max_polyphony(notes),
        "density": len(notes) / (total_ms / 1000.0) if total_ms else 0.0,
        "channels": sorted({_chan(e) for e in events}),
    }


def stats_report(path):
    s = stats_data(path)
    if s["min_midi"] is None:
        rng = "—"
    else:
        rng = (f"{midi_to_name(s['min_midi'])} ({s['min_midi']}) – "
               f"{midi_to_name(s['max_midi'])} ({s['max_midi']})")
    chans = ", ".join(str(c) for c in s["channels"]) if s["channels"] else "—"
    return "\n".join([
        f"HELLFORGE stats — {os.path.basename(path)}",
        f"  Notes:         {s['notes']}",
        f"  Duration:      {_fmt_clock(s['total_ms'])} ({s['total_ms'] / 1000:.1f}s @ {s['bpm']:g} BPM)",
        f"  Note range:    {rng}",
        f"  Velocity:      avg {s['avg_velocity']}, max {s['max_velocity']}",
        f"  Max polyphony: {s['polyphony']} simultaneous notes",
        f"  Density:       {s['density']:.2f} notes/sec",
        f"  Channels:      {chans} ({len(s['channels'])} used)",
    ])


# ── tracks ────────────────────────────────────────────────────────────

def tracks_data(path):
    """Per-channel and (when TRK metadata exists) per-track tables."""
    events, bp = load_events(path)
    by_chan = {}
    by_track = {}
    for e in events:
        if not _is_note(e):
            continue
        row = by_chan.setdefault(_chan(e), [0, 128, 0, 0])
        row[0] += 1
        row[1] = min(row[1], e["midi"])
        row[2] = max(row[2], e["midi"])
        row[3] += e["velocity"]
        tname = e.get("track")
        if tname:
            trow = by_track.setdefault(tname, [0, 128, 0, 0])
            trow[0] += 1
            trow[1] = min(trow[1], e["midi"])
            trow[2] = max(trow[2], e["midi"])
            trow[3] += e["velocity"]

    def _rows(groups):
        out = []
        for key in sorted(groups):
            n, lo, hi, vsum = groups[key]
            out.append((key, n, lo, hi, int(vsum / n) if n else 0))
        return out

    return {"bpm": bp, "channels": _rows(by_chan), "tracks": _rows(by_track)}


def tracks_report(path):
    d = tracks_data(path)
    lines = [f"HELLFORGE tracks — {os.path.basename(path)}"]
    if not d["channels"]:
        lines.append("  No notes found.")
        return "\n".join(lines)
    lines.append(f"  {'CH':<5}{'Notes':>6}  {'Min':<6}{'Max':<6}{'AvgVel':>6}")
    for ch, n, lo, hi, av in d["channels"]:
        lines.append(f"  {ch:<5}{n:>6}  {midi_to_name(lo):<6}{midi_to_name(hi):<6}{av:>6}")
    if d["tracks"]:
        lines.append(f"  {'TRACK':<16}{'Notes':>6}  {'Min':<6}{'Max':<6}{'AvgVel':>6}")
        for name, n, lo, hi, av in d["tracks"]:
            lines.append(f"  {name:<16}{n:>6}  {midi_to_name(lo):<6}{midi_to_name(hi):<6}{av:>6}")
    return "\n".join(lines)


# ── inspect ───────────────────────────────────────────────────────────

def inspect_lines(path, n=12):
    """First n events as readable lines: T<ms> N<midi>(<name>) D<ms> V<vel> CH<n>."""
    events, bp = load_events(path)
    events = sort_events(events)
    shown = events[:max(1, int(n))]
    lines = [f"HELLFORGE inspect — {os.path.basename(path)} (first {len(shown)} of {len(events)} events)"]
    for e in shown:
        lines.append(f"T{e['timestamp']} N{e['midi']}({midi_to_name(e['midi'])}) "
                     f"D{e['duration']} V{e['velocity']} CH{_chan(e)}")
    return lines


# ── new ───────────────────────────────────────────────────────────────

def scaffold_project(name, out_dir=None):
    """Scaffold a v5 project. Returns the project root path.
    -o <dir> overrides the output location of the project root."""
    if not name or name in (".", "..") or any(ch in name for ch in "/\\"):
        raise CLIError(f"Invalid project name: {name!r}")
    root = os.path.abspath(out_dir) if out_dir else os.path.abspath(name)
    if os.path.exists(root) and os.listdir(root):
        raise CLIError(f"Directory already exists and is not empty: {root}")
    os.makedirs(os.path.join(root, "parts"), exist_ok=True)

    index = "\n".join([
        f"// v5 project index — {name}",
        f"// Scaffolded by HELLFORGE `new`",
        f'project "{name}"',
        f'composer "HELLFORGE"',
        f"tempo 120",
        f'@title "{name}"',
        "",
        f'include "parts/main.e" as main',
        "",
        'section "Main" {',
        "    play main",
        "}",
        "",
    ])

    main_part = "\n".join([
        f"// v5 — {name} main part: pedal, rests, articulations",
        "// HELLFORGE canonical syntax (v5 = v4 + performance features)",
        "@bpm 120",
        "@key C Major",
        "",
        "pedal on",
        "play note(C4) @dur:q @vel:mf @art:staccato",
        "play note(E4) @dur:q @vel:mp @art:legato",
        "rest e",
        "play chord(C, major) @dur:h @vel:f @art:tenuto",
        "pedal off",
        "play note(G4) @dur:h @vel:ff @art:accent",
        "",
    ])

    readme = "\n".join([
        f"# {name}",
        "",
        "HELLFORGE v5 project scaffolded by `new`.",
        "",
        "## Files",
        "",
        "- `index.ei` — project root: title, composer, tempo, section with part includes",
        "- `parts/main.e` — v5 part using pedal, rests, articulations",
        "",
        "## Compile",
        "",
        f"    python ep.py compile index.ei -o {name}.mid",
        "",
    ])

    for rel, content in (("index.ei", index), ("parts/main.e", main_part), ("README.md", readme)):
        with open(os.path.join(root, rel), "w", encoding="utf-8") as f:
            f.write(content)
    return root


# ── transpose ─────────────────────────────────────────────────────────

def transpose_events(path, semitones):
    """Shift all notes by semitones (clamped to 0-127). Returns (events, bpm)."""
    events, bp = load_events(path)
    for e in events:
        if _is_note(e):
            e["midi"] = max(0, min(127, e["midi"] + semitones))
    return events, bp


def transpose_file(path, semitones, out=None):
    """Transpose and write output. Default: <file>_transposed.mid."""
    try:
        semitones = int(semitones)
    except (TypeError, ValueError):
        raise CLIError(f"Invalid semitone count: {semitones!r}")
    if not out:
        out = f"{os.path.splitext(path)[0]}_transposed.mid"
    events, bp = transpose_events(path, semitones)
    _write_output(events, bp, out)
    n = sum(1 for e in events if _is_note(e))
    return (f"HELLFORGE transpose — {os.path.basename(path)} ({semitones:+d} semitones)\n"
            f"  ✓ {out} ({n} notes)")


# ── tempo ─────────────────────────────────────────────────────────────

def tempo_events(path, bpm):
    """Recompile/rescale events at bpm. Returns (events, bpm)."""
    if bpm <= 0:
        raise CLIError("BPM must be positive")
    events, bp = load_events(path, bpm=float(bpm))
    return events, bp


def tempo_file(path, bpm, out=None):
    """Recompile at bpm and write output. Default: <file>_tempo.mid."""
    try:
        bpm = float(bpm)
    except (TypeError, ValueError):
        raise CLIError(f"Invalid BPM: {bpm!r}")
    if bpm <= 0:
        raise CLIError("BPM must be positive")
    if not out:
        out = f"{os.path.splitext(path)[0]}_tempo.mid"
    events, bp = tempo_events(path, bpm)
    _write_output(events, bp, out)
    n = sum(1 for e in events if _is_note(e))
    return (f"HELLFORGE tempo — {os.path.basename(path)} ({bp:g} BPM)\n"
            f"  ✓ {out} ({n} notes)")


# ── merge ─────────────────────────────────────────────────────────────

def merge_events(a, b):
    """Merge b after a. Returns (merged_events, bpm, len_a, len_b, offset)."""
    ev_a, bp = load_events(a)
    ev_b, _ = load_events(b)
    offset = max((e["timestamp"] + e["duration"] for e in ev_a), default=0)
    for e in ev_b:
        e["timestamp"] += offset
    return sort_events(ev_a + ev_b), bp, len(ev_a), len(ev_b), offset


def merge_files(a, b, out=None):
    """Merge two files into one output. Default: <a>_merged.mid."""
    if not out:
        out = f"{os.path.splitext(a)[0]}_merged.mid"
    merged, bp, na, nb, offset = merge_events(a, b)
    _write_output(merged, bp, out)
    return (f"HELLFORGE merge — {os.path.basename(a)} + {os.path.basename(b)}\n"
            f"  A: {na} notes (ends at {offset}ms)\n"
            f"  B: {nb} notes (offset +{offset}ms)\n"
            f"  ✓ {out} ({na + nb} notes total)")
