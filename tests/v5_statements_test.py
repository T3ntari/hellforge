#!/usr/bin/env python3
"""v5 statement-level features tests: print, assert, include, !fn macros,
prog progressions, perc percussion, extended loops, @seed + pick/rand."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ep_compiler.compile import compile_source

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


# ── print ──

def test_print_literal():
    compile_source('print "hello"\nT0 N60 D500 V80')
test("Print: literal string compiles", test_print_literal)


def test_print_resolves():
    compile_source('print {2 + 3}\nT0 N60 D500 V80')
    compile_source('print N60\nT0 N60 D500 V80')
test("Print: expr and note forms compile", test_print_resolves)


def test_print_in_loop():
    compile_source('for $i in 1..3 { print {$i}\nT0 N60 D100 V80 }')
test("Print: inside loop body compiles", test_print_in_loop)


# ── assert ──

def test_assert_passes():
    compile_source('assert {2 + 2} == 4, "ok"\nT0 N60 D500 V80')
test("Assert: true condition passes", test_assert_passes)


def test_assert_fails():
    try:
        compile_source('assert {2 + 2} == 5, "math broken"\nT0 N60 D500 V80')
        raise AssertionError("assert should have failed")
    except (AssertionError, Exception) as e:
        assert "math broken" in str(e) or "assert failed" in str(e) or "v5 ERROR" in str(e), str(e)
test("Assert: false condition raises", test_assert_fails)


def test_assert_var():
    compile_source('$x = 60\nassert $x == 60, "x"\nT0 N60 D500 V80')
test("Assert: $var conditions", test_assert_var)


# ── include ──

def test_include_inlines():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "hook.e"), "w") as f:
        f.write("T0 N60 D500 V80\n")
    ev, _ = compile_source('include "hook.e"\nT100 N64 D500 V80', base_dir=d)
    assert len(ev) == 2, f"expected 2 events, got {len(ev)}"
    assert [e["timestamp"] for e in ev] == [0, 100]
test("Include: inlines file relative to source dir", test_include_inlines)


def test_include_missing():
    try:
        compile_source('include "nope_missing_file.e"\nT0 N60 D500 V80')
        raise AssertionError("should have failed")
    except Exception as e:
        assert "cannot find" in str(e)
test("Include: missing file raises", test_include_missing)


def test_include_cycle():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "a.e"), "w") as f:
        f.write('include "b.e"\nT0 N60 D100 V80\n')
    with open(os.path.join(d, "b.e"), "w") as f:
        f.write('include "a.e"\n')
    try:
        compile_source('include "a.e"', base_dir=d)
        raise AssertionError("should have failed")
    except Exception as e:
        assert "circular" in str(e).lower() or "depth" in str(e).lower()
test("Include: circular include rejected", test_include_cycle)


# ── !fn macros ──

def test_fn_literal_args():
    ev, _ = compile_source('!fn f(ts, note) = T{$ts * 100} N{$note} D200 V80\n!f(0, 60)\n!f(1, 64)')
    assert [(e["timestamp"], e["midi"]) for e in ev] == [(0, 60), (100, 64)]
test("!fn: literal args expand", test_fn_literal_args)


def test_fn_loop_var():
    ev, _ = compile_source('!fn f(ts, note) = T{$ts * 100} N{$note} D200 V80\n'
                           'for $i in 0..3 { !f($i, 60) }')
    assert [e["timestamp"] for e in ev] == [0, 100, 200, 300]
test("!fn: loop-variable args", test_fn_loop_var)


def test_fn_expr_arg():
    ev, _ = compile_source('!fn f(ts, note) = T{$ts * 100} N{$note} D200 V80\n!f({2 + 3}, 60)')
    assert ev[0]["timestamp"] == 500
test("!fn: expression arg composes", test_fn_expr_arg)


def test_fn_note_arg():
    ev, _ = compile_source('!fn n(note, d) = T0 N $note D{$d * 500} V80\n!n(C4, 1)\n!n(E4, 2)')
    assert [(e["midi"], e["duration"]) for e in ev] == [(60, 500), (64, 1000)]
test("!fn: note-name args", test_fn_note_arg)


# ── prog ──

def test_prog_chords():
    ev, _ = compile_source('prog(C:q, G:q, Am:h, F:q)')
    # C major (3) + G major (3) + A minor (3) + F major (3)
    assert len(ev) == 12, f"expected 12 chord notes, got {len(ev)}"
    assert ev[0]["midi"] == 60 and ev[3]["midi"] == 67 and ev[6]["midi"] == 69
    assert ev[0]["duration"] == 500 and ev[6]["duration"] == 1000
test("Prog: progression expands to chords", test_prog_chords)


# ── perc ──

def test_perc_channel9():
    ev, _ = compile_source('perc(kick)\nperc(snare)\nperc(hihat)')
    assert [(e["midi"], e["channel"]) for e in ev] == [(36, 9), (38, 9), (42, 9)]
test("Perc: GM drums on channel 9", test_perc_channel9)


def test_perc_unknown():
    try:
        compile_source('perc(notadrum)')
        raise AssertionError("should have failed")
    except Exception as e:
        assert "unknown drum" in str(e).lower()
test("Perc: unknown drum rejected", test_perc_unknown)


# ── loops: list / range / scale / run / break / continue ──

def test_loop_list():
    ev, _ = compile_source('for $n in [C4 E4 G4] { T0 N $n D100 V80 }')
    assert [e["midi"] for e in ev] == [60, 64, 67]
test("Loop: for-in-list", test_loop_list)


def test_loop_range():
    ev, _ = compile_source('for $i in 1..4 { T{$i * 100} N60 D100 V80 }')
    assert [e["timestamp"] for e in ev] == [100, 200, 300, 400]
test("Loop: for-in-range (1..N)", test_loop_range)


def test_loop_scale():
    ev, _ = compile_source('for $n in scale(C major, 4, 1) { T0 N $n D100 V80 }')
    assert [e["midi"] for e in ev] == [60, 62, 64, 65, 67, 69, 71]
test("Loop: for-in-scale", test_loop_scale)


def test_loop_scale_minor_2oct():
    ev, _ = compile_source('for $n in scale(A minor, 4, 2) { T0 N $n D100 V80 }')
    assert len(ev) == 14 and ev[0]["midi"] == 69 and ev[-1]["midi"] == 91
test("Loop: scale 2 octaves", test_loop_scale_minor_2oct)


def test_loop_run():
    ev, _ = compile_source('for $n in run(C4, E4) { T0 N $n D100 V80 }')
    assert [e["midi"] for e in ev] == [60, 61, 62, 63, 64]
test("Loop: for-in-run chromatic", test_loop_run)


def test_loop_break():
    ev, _ = compile_source('for $n in [C4 E4 G4 F4] {\n    T0 N $n D100 V80\n    break\n}')
    assert [e["midi"] for e in ev] == [60]
test("Loop: break exits block", test_loop_break)


def test_loop_continue():
    ev, _ = compile_source('for $n in [C4 E4 G4 F4] {\n    continue\n    T0 N $n D100 V80\n}\n'
                           'T0 N72 D100 V80')
    assert [e["midi"] for e in ev] == [72]
test("Loop: continue skips body", test_loop_continue)


def test_loop_repeat_break():
    ev, _ = compile_source('repeat 5 {\n    T0 N60 D100 V80\n    break\n}')
    assert len(ev) == 1
test("Loop: break in repeat", test_loop_repeat_break)


# ── @seed + pick/rand ──

def test_pick_deterministic():
    ev, _ = compile_source('@seed 42\n$x = pick(60 64 67)\nT0 N{$x} D100 V80')
    ev2, _ = compile_source('@seed 42\n$x = pick(60 64 67)\nT0 N{$x} D100 V80')
    assert ev[0]["midi"] == ev2[0]["midi"], "same seed must give same pick"
test("Seed: pick deterministic per seed", test_pick_deterministic)


def test_pick_different_seed():
    ev, _ = compile_source('@seed 1\n$x = pick(60 64 67)\nT0 N{$x} D100 V80')
    ev2, _ = compile_source('@seed 2\n$x = pick(60 64 67)\nT0 N{$x} D100 V80')
    assert ev[0]["midi"] in (60, 64, 67)
test("Seed: different seeds allowed", test_pick_different_seed)


def test_rand_range():
    ev, _ = compile_source('@seed 9\n$y = rand(1, 4)\nT0 N{$y} D100 V80')
    assert 1 <= ev[0]["midi"] <= 4
test("Seed: rand within range", test_rand_range)


# ── backwards compatibility ──

def test_plain_v1_still_default():
    ev, _ = compile_source('T0 N60 D500 V80\nT500 N64 D500 V90')
    assert len(ev) == 2
test("Compat: plain machine lines still compile", test_plain_v1_still_default)


def test_v4_features_still_compile():
    ev, _ = compile_source('[C4 E4](3:2)\nT0 N60 D500 V80')
    assert len(ev) >= 2
test("Compat: v4 polyrhythm still compiles", test_v4_features_still_compile)


print(f"\n{'='*50}")
print(f"V5 STATEMENT TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL V5 STATEMENT TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
