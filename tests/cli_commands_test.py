#!/usr/bin/env python3
"""HELLFORGE v5 CLI command tests — stats, tracks, inspect, new, transpose, tempo, merge.

Covers both the eshell do_* handlers and the run.py subcommands, sharing
logic via ep_compiler.cli_cmds.
"""
import sys
import os
import re
import glob
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        import traceback
        traceback.print_exc()
        print(f"  [FAIL] {name}: {e}")


TMP = tempfile.mkdtemp(prefix="hf_cli_")

SRC = "@bpm 120\nT0 N60 D500 V80\nT250 N64 D500 V90\nT1000 N72 D1000 V100\n"


def write_src(name="song.e"):
    path = os.path.join(TMP, name)
    with open(path, "w") as f:
        f.write(SRC)
    return path


def write_midi(name, notes, track_names=None):
    """Build a .mid file. notes: list of (note, channel, start_tick, dur_ticks, vel)."""
    import mido
    m = mido.MidiFile(ticks_per_beat=480)
    tr = mido.MidiTrack()
    m.tracks.append(tr)
    tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
    if track_names:
        tr.append(mido.MetaMessage("track_name", name=track_names[0], time=0))
    msgs = []
    for note, ch, st, d, vel in notes:
        msgs.append((st, "note_on", note, vel, ch))
        msgs.append((st + d, "note_off", note, 0, ch))
    msgs.sort(key=lambda x: (x[0], x[1]))
    cur = 0
    for t, typ, note, vel, ch in msgs:
        tr.append(mido.Message(typ, note=note, velocity=vel, channel=ch, time=max(0, t - cur)))
        cur = t
    tr.append(mido.MetaMessage("end_of_track", time=0))
    path = os.path.join(TMP, name)
    m.save(path)
    return path


def count_midi_notes(path):
    import mido
    m = mido.MidiFile(path)
    return sum(1 for msg in m if msg.type == "note_on" and msg.velocity > 0)


def midi_bpm(path):
    import mido
    m = mido.MidiFile(path)
    for msg in m:
        if msg.type == "set_tempo":
            return mido.tempo2bpm(msg.tempo)
    return 120


# ── stats ──

def test_stats_known_values():
    from ep_compiler.cli_cmds import stats_data
    s = stats_data(write_src())
    assert s["notes"] == 3, s
    assert s["min_midi"] == 60 and s["max_midi"] == 72, s
    assert s["avg_velocity"] == 90 and s["max_velocity"] == 100, s
    assert s["polyphony"] == 2, s
    assert s["total_ms"] == 2000, s
    assert abs(s["density"] - 1.5) < 0.001, s
    assert s["channels"] == [0], s
test("Stats: note count, range, velocity, polyphony, density, channels", test_stats_known_values)


def test_stats_v5_sample():
    from ep_compiler.cli_cmds import stats_data, load_events
    sample = os.path.join(ROOT, "samples", "v5-current", "performance_demo.e")
    s = stats_data(sample)
    # pedal on/off events must not count as notes
    assert s["notes"] == 9, s
    assert s["min_midi"] == 60, s   # C4
    assert s["max_midi"] == 76, s   # E5
    # t3(G4 C5 E5) @vel:f tuplet must contribute its 3 notes (67/72/76)
    ev, _ = load_events(sample)
    midis = {e["midi"] for e in ev if e["midi"] != 0}
    assert {67, 72, 76} <= midis, midis
test("Stats: v5 sample counts pedal events as non-notes, tuplet included", test_stats_v5_sample)


def test_stats_midi_input():
    from ep_compiler.cli_cmds import stats_data
    mid = write_midi("song.mid", [(60, 0, 0, 480, 80), (64, 0, 240, 480, 90), (72, 0, 960, 960, 100)])
    s = stats_data(mid)
    assert s["notes"] == 3, s
    assert s["min_midi"] == 60 and s["max_midi"] == 72, s
    assert s["avg_velocity"] == 90, s
test("Stats: .mid input via mido", test_stats_midi_input)


def test_stats_missing_file():
    from ep_compiler.cli_cmds import CLIError, stats_data
    try:
        stats_data(os.path.join(TMP, "nope.e"))
        raise AssertionError("expected CLIError")
    except CLIError as e:
        assert "Not found" in str(e)
test("Stats: missing file raises friendly CLIError", test_stats_missing_file)


# ── tracks ──

def test_tracks_channel_table():
    from ep_compiler.cli_cmds import tracks_report
    rep = tracks_report(write_src())
    assert "CH" in rep and "AvgVel" in rep
    m = re.search(r"^\s*0\s+3\s+C4\s+C5\s+90$", rep, re.M)
    assert m, rep
test("Tracks: channel 0 table row with note count and avg velocity", test_tracks_channel_table)


def test_tracks_midi_channels_and_track_meta():
    from ep_compiler.cli_cmds import tracks_report
    mid = write_midi("multi.mid", [(60, 0, 0, 480, 80), (64, 2, 480, 480, 90)],
                     track_names=["Piano L"])
    rep = tracks_report(mid)
    assert re.search(r"^\s*0\s+1\s+C4\s+C4\s+80$", rep, re.M), rep
    assert re.search(r"^\s*2\s+1\s+E4\s+E4\s+90$", rep, re.M), rep
    assert "Piano L" in rep and re.search(r"Piano L\s+2\s", rep), rep
test("Tracks: .mid per-channel rows + per-track table from TRK metadata", test_tracks_midi_channels_and_track_meta)


# ── inspect ──

def test_inspect_format():
    from ep_compiler.cli_cmds import inspect_lines
    lines = inspect_lines(write_src())
    assert lines[0].startswith("HELLFORGE inspect"), lines
    assert lines[1] == "T0 N60(C4) D500 V80 CH0", lines
    assert "N64(E4)" in lines[2] and "T250" in lines[2], lines
test("Inspect: T<ms> N<midi>(<name>) D<ms> V<vel> CH<n> format", test_inspect_format)


def test_inspect_sorted_and_limit():
    from ep_compiler.cli_cmds import inspect_lines
    # unsorted source; output must be sorted by timestamp
    path = os.path.join(TMP, "unsorted.e")
    with open(path, "w") as f:
        f.write("@bpm 120\nT1000 N72 D100 V80\nT0 N60 D100 V80\n")
    lines = inspect_lines(path)
    assert "T0 N60" in lines[1] and "T1000 N72" in lines[2], lines
    one = inspect_lines(path, 1)
    assert len(one) == 2 and "T0 N60" in one[1], one
test("Inspect: sorts by timestamp, honors N limit", test_inspect_sorted_and_limit)


# ── new ──

def test_new_scaffolds_project():
    from ep_compiler.cli_cmds import scaffold_project
    out = os.path.join(TMP, "proj_a")
    root = scaffold_project("my-song", out)
    assert os.path.isfile(os.path.join(root, "index.ei"))
    assert os.path.isfile(os.path.join(root, "parts", "main.e"))
    assert os.path.isfile(os.path.join(root, "README.md"))
    with open(os.path.join(root, "index.ei")) as f:
        idx = f.read()
    assert 'project "my-song"' in idx and 'include "parts/main.e" as main' in idx
    assert 'section "Main"' in idx and "play main" in idx
test("New: scaffolds index.ei + parts/main.e + README.md", test_new_scaffolds_project)


def test_new_scaffold_compiles():
    from ep_compiler.cli_cmds import scaffold_project
    from ep_compiler.compile import compile_file
    out = os.path.join(TMP, "proj_b")
    root = scaffold_project("compile-me", out)
    ev, bp = compile_file(os.path.join(root, "index.ei"))
    assert len(ev) > 0, "scaffolded project should compile to events"
    assert any(e["midi"] > 0 for e in ev), ev
test("New: scaffolded project compiles (index.ei -> events)", test_new_scaffold_compiles)


# ── transpose ──

def test_transpose_shifts_and_clamps():
    from ep_compiler.cli_cmds import transpose_events
    src = write_src("transp.e")
    ev, bp = transpose_events(src, 12)
    midis = sorted(e["midi"] for e in ev)
    assert midis == [72, 76, 84], midis
    # clamp: N127 + 12 -> 127
    path = os.path.join(TMP, "clamp.e")
    with open(path, "w") as f:
        f.write("@bpm 120\nT0 N127 D100 V80\n")
    ev2, _ = transpose_events(path, 12)
    assert ev2[0]["midi"] == 127, ev2
test("Transpose: shifts midi by semitones and clamps at 127", test_transpose_shifts_and_clamps)


def test_transpose_writes_default_mid():
    from ep_compiler.cli_cmds import transpose_file
    src = write_src("transp2.e")
    report = transpose_file(src, -5)
    out = os.path.join(TMP, "transp2_transposed.mid")
    assert out in report, report
    assert os.path.exists(out)
    assert count_midi_notes(out) == 3
test("Transpose: writes <file>_transposed.mid readable by mido", test_transpose_writes_default_mid)


# ── tempo ──

def test_tempo_rescales_word_durations():
    from ep_compiler.cli_cmds import tempo_events
    from ep_compiler.compile import compile_source
    path = os.path.join(TMP, "word.e")
    with open(path, "w") as f:
        f.write("@bpm 120\nplay note(C4) @dur:q @vel:mf\n")
    ev120, _ = compile_source(open(path).read())
    ev240, bp = tempo_events(path, 240)
    assert bp == 240.0
    assert ev240[0]["duration"] < ev120[0]["duration"], (ev240, ev120)
    assert ev240[0]["duration"] == 250, ev240  # quarter note halves at 240bpm
test("Tempo: recompile rescales word durations", test_tempo_rescales_word_durations)


def test_tempo_writes_mid_with_new_bpm():
    from ep_compiler.cli_cmds import tempo_file
    src = write_src("tempo2.e")
    report = tempo_file(src, 180)
    out = os.path.join(TMP, "tempo2_tempo.mid")
    assert out in report, report
    assert os.path.exists(out)
    assert abs(midi_bpm(out) - 180) < 1.0
test("Tempo: writes <file>_tempo.mid with new set_tempo", test_tempo_writes_mid_with_new_bpm)


# ── merge ──

def test_merge_offsets_and_counts():
    from ep_compiler.cli_cmds import merge_events
    a = write_src("merge_a.e")
    b = os.path.join(TMP, "merge_b.e")
    with open(b, "w") as f:
        f.write("@bpm 120\nT0 N50 D100 V70\n")
    merged, bp, na, nb, offset = merge_events(a, b)
    assert na == 3 and nb == 1 and len(merged) == 4, (na, nb, len(merged))
    assert offset == 2000, offset
    b_note = [e for e in merged if e["midi"] == 50]
    assert b_note and b_note[0]["timestamp"] == 2000, b_note
    ts = [e["timestamp"] for e in merged]
    assert ts == sorted(ts), ts
test("Merge: offsets file b after file a, sums note counts, sorts", test_merge_offsets_and_counts)


def test_merge_writes_default_mid():
    from ep_compiler.cli_cmds import merge_files
    a = write_src("merge_c.e")
    b = write_src("merge_d.e")
    report = merge_files(a, b)
    out = os.path.join(TMP, "merge_c_merged.mid")
    assert out in report, report
    assert os.path.exists(out)
    assert count_midi_notes(out) == 6
test("Merge: writes <a>_merged.mid with combined note count", test_merge_writes_default_mid)


# ── eshell + run.py integration ──

def test_eshell_handlers_registered():
    import eshell
    for name in ("do_stats", "do_tracks", "do_inspect", "do_new", "do_transpose", "do_tempo", "do_merge"):
        assert hasattr(eshell, name), f"eshell missing {name}"
    # stats must no longer alias do_info
    assert eshell.do_stats is not eshell.do_info
test("eshell: all 7 v5 handlers exist, stats decoupled from info", test_eshell_handlers_registered)


def test_run_py_stats_missing_exit1_no_traceback():
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "run.py"), "stats", os.path.join(TMP, "missing.e")],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 1, r
    assert "Not found" in r.stdout, r.stdout
    assert "Traceback" not in r.stdout + r.stderr
test("run.py: stats missing file -> exit 1, friendly error, no traceback", test_run_py_stats_missing_exit1_no_traceback)


def test_run_py_transpose_happy_path():
    src = write_src("rt_transp.e")
    out = os.path.join(TMP, "rt_transposed.mid")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "run.py"), "transpose", src, "7", "-o", out],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "HELLFORGE transpose" in r.stdout, r.stdout
    assert os.path.exists(out)
    assert count_midi_notes(out) == 3
test("run.py: transpose subcommand exits 0 and writes output", test_run_py_transpose_happy_path)


def test_run_py_merge_and_inspect():
    a = write_src("rt_a.e")
    b = write_src("rt_b.e")
    r = subprocess.run(
        [sys.executable, os.path.join(ROOT, "run.py"), "merge", a, b],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r.returncode == 0, r.stdout + r.stderr
    assert os.path.exists(os.path.join(TMP, "rt_a_merged.mid"))
    r2 = subprocess.run(
        [sys.executable, os.path.join(ROOT, "run.py"), "inspect", a, "2"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "T0 N60(C4) D500 V80 CH0" in r2.stdout, r2.stdout
    assert r2.stdout.count("CH0") == 2  # N=2 events shown
test("run.py: merge + inspect subcommands work end-to-end", test_run_py_merge_and_inspect)


shutil.rmtree(TMP, ignore_errors=True)

print(f"\n{'='*50}")
print(f"CLI COMMAND TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL CLI COMMAND TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
