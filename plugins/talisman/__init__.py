"""Talisman v1.1.0 — Audio Culling, Privacy & QOL Engine by Tentari.
Features: audio culling/occlusion, local-only mode, auto-backup,
device ID rotation, event inspection, compile stats."""

import os
import json
import time
import shutil

VERSION = "1.1.0"
author = "Tentari"
description = "Audio culling, privacy & QOL: local mode, backup, inspect, stats"

from .culling import (
    cull_and_occlude,
    set_culling_enabled,
    get_culling_enabled,
)

# ── Talisman State ──
_local_mode = False
_auto_backup = False
_compile_count = 0
_last_compile_events = []


def get_local_mode():
    return _local_mode


def set_local_mode(enabled):
    global _local_mode
    _local_mode = enabled


def get_auto_backup():
    return _auto_backup


def set_auto_backup(enabled):
    global _auto_backup
    _auto_backup = enabled


def register(api):
    api.add_boot_step("Talisman v1.1.0", "loading")

    # ── Post-compile hook ──
    def _cull_hook(events, bpm):
        global _compile_count, _last_compile_events
        _compile_count += 1
        _last_compile_events = events

        # Auto-backup
        if _auto_backup:
            _do_auto_backup(events, bpm)

        # Culling
        if not get_culling_enabled():
            return events
        result, culled, occluded = cull_and_occlude(events)
        if culled or occluded:
            from ep_compiler.debug import info as _info
            _info("TALISMAN", f"Culled {culled}, occluded {occluded}")
        return result

    api.on("post_compile", _cull_hook)

    # ── Command handler ──
    def _talisman_cmd(args):
        if not args or args[0] == "status":
            _cmd_status()
            return
        if args[0] in ("on", "off"):
            set_culling_enabled(args[0] == "on")
            s = "ON" if get_culling_enabled() else "OFF"
            print(f"  Talisman culling: {s}")
            return
        if args[0] == "local":
            set_local_mode(not _local_mode if len(args) < 2 else args[1] == "on")
            s = "ON" if _local_mode else "OFF"
            print(f"  Talisman local mode: {s} — backend calls disabled")
            return
        if args[0] in ("backup", "autobackup"):
            set_auto_backup(not _auto_backup if len(args) < 2 else args[1] == "on")
            s = "ON" if _auto_backup else "OFF"
            print(f"  Talisman auto-backup: {s}")
            return
        if args[0] == "rotate-id":
            _cmd_rotate_id()
            return
        if args[0] == "inspect":
            if len(args) < 2:
                print("  Usage: talisman inspect <file.e>")
                return
            _cmd_inspect(args[1])
            return
        if args[0] == "stats":
            _cmd_stats()
            return
        print("  Usage: talisman <on|off|local|backup|rotate-id|inspect|stats|status>")

    api.add_command("talisman", _talisman_cmd,
                    "Talisman: talisman <on|off|local|backup|rotate-id|inspect|stats>")
    api.add_boot_step("Talisman: audio culling + privacy QOL active", "done")


# ── Private helpers ──

def _do_auto_backup(events, bpm):
    """Save a timestamped backup of compiled events."""
    backup_dir = os.path.join(os.path.dirname(__file__), "..", "..", ".e_backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    path = os.path.join(backup_dir, f"compile_{ts}.json")
    try:
        with open(path, "w") as f:
            json.dump({"bpm": bpm, "events": events, "time": time.time()}, f)
    except Exception:
        pass


def _cmd_rotate_id():
    """Regenerate device ID for privacy."""
    try:
        from ep_compiler.plugin_security import get_device_id
        from ep_core import IDENTITY_DIR
        dev_path = IDENTITY_DIR / ".device_id"
        if dev_path.exists():
            dev_path.unlink()
        new_id = get_device_id()
        print(f"  Device ID rotated: {new_id[:16]}...")
        try:
            from ep_compiler.security_hash import reembed
            reembed()
            print("  identity digest refreshed")
        except Exception:
            pass
        print(f"  Your session will be treated as a new device by the backend")
    except Exception as e:
        print(f"  Rotate failed: {e}")


def _cmd_inspect(filepath):
    """Inspect a compiled .e/.mid file and show event statistics."""
    filepath = filepath.strip("\"'")
    if not os.path.exists(filepath):
        print(f"  Not found: {filepath}")
        return

    # Compile the file to get events
    from ep_compiler.compile import compile_file
    try:
        events, bpm = compile_file(filepath)
    except Exception as e:
        # Try loading as MIDI
        try:
            from ep_compiler.import_midi import import_midi_file
            events, bpm = import_midi_file(filepath)
        except Exception:
            print(f"  Cannot process: {e}")
            return

    if not events:
        print("  No events found")
        return

    total = len(events)
    dur = max(e["timestamp"] + e["duration"] for e in events) / 1000
    notes = [e["midi"] for e in events]
    vels = [e["velocity"] for e in events]
    channels = set(e.get("channel", 0) for e in events)
    unique_notes = len(set(notes))

    print(f"  {os.path.basename(filepath)} — {bpm} BPM")
    print(f"    Events: {total} | Duration: {dur:.1f}s | Unique notes: {unique_notes}")
    print(f"    Channels: {sorted(channels)}")
    print(f"    Velocity: min={min(vels)}, avg={sum(vels)//len(vels)}, max={max(vels)}")
    print(f"    Density: {total/dur:.1f} notes/s")

    # Per-channel breakdown
    by_ch = {}
    for e in events:
        ch = e.get("channel", 0)
        by_ch.setdefault(ch, []).append(e)
    for ch in sorted(by_ch):
        ch_ev = by_ch[ch]
        print(f"    CH{ch}: {len(ch_ev)} events, "
              f"notes {min(e['midi'] for e in ch_ev)}-{max(e['midi'] for e in ch_ev)}")


def _cmd_stats():
    """Show compile statistics for this session."""
    global _compile_count, _last_compile_events
    print(f"  Talisman compile stats:")
    print(f"    Compiles this session: {_compile_count}")
    if _last_compile_events:
        ev = _last_compile_events
        print(f"    Last compile: {len(ev)} events, "
              f"{max(e['timestamp'] + e['duration'] for e in ev)/1000:.1f}s")
        chs = set(e.get("channel", 0) for e in ev)
        print(f"    Channels used: {sorted(chs)}")
    print(f"    Culling: {'ON' if get_culling_enabled() else 'OFF'}")
    print(f"    Local mode: {'ON' if _local_mode else 'OFF'}")
    print(f"    Auto-backup: {'ON' if _auto_backup else 'OFF'}")


def _cmd_status():
    """Show full status of all Talisman features."""
    print(f"  Talisman v{VERSION}")
    print(f"    Culling: {'ON' if get_culling_enabled() else 'OFF'}")
    print(f"    Local mode: {'ON' if _local_mode else 'OFF'}")
    print(f"    Auto-backup: {'ON' if _auto_backup else 'OFF'}")
    print(f"    Compiles this session: {_compile_count}")
    if _last_compile_events:
        ev = _last_compile_events
        print(f"    Last compile: {len(ev)} events")
    print(f"  Commands: on|off|local|backup|rotate-id|inspect|stats|status")
