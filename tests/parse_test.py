#!/usr/bin/env python3
"""HELLFORGE strict-parse + math + v4 + memory tests."""
import sys
import os
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ep_compiler.compile import compile_source, detect_syntax_version
from ep_compiler.mode_v1_machine import parse_machine_line, last_problems as mlp
from ep_compiler.mode_v1_human import parse_human_line, last_problems as hlp
from ep_compiler.loops import set_unroll_cap, get_unroll_cap, LoopError
from ep_compiler.variables import evaluate_expression

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


# === Strict machine parsing ===

def test_machine_garbage_trailing():
    mlp.clear()
    ev = parse_machine_line("T0 N60 D500 V80 GARBAGE", {"bpm": 120})
    assert ev is None, "trailing garbage must fail"
    assert any(p["code"] == "E056" for p in mlp)
test("Machine: trailing garbage -> E056", test_machine_garbage_trailing)


def test_machine_out_of_range_note():
    mlp.clear()
    ev = parse_machine_line("T0 N200 D500 V80", {"bpm": 120})
    assert ev is None
    assert any(p["code"] == "E053" for p in mlp)
test("Machine: N200 out of range -> E053 (no silent clamp)", test_machine_out_of_range_note)


def test_machine_word_forms():
    mlp.clear()
    ev = parse_machine_line("T0 N C4 D q V mf", {"bpm": 120})
    assert ev is not None and ev["midi"] == 60 and ev["duration"] == 500 and ev["velocity"] == 80
    assert not mlp
test("Machine: word forms N C4 D q V mf", test_machine_word_forms)


def test_machine_long_words():
    mlp.clear()
    ev = parse_machine_line("T0 N C4 D quarter V forte", {"bpm": 120})
    assert ev is not None and ev["midi"] == 60 and ev["velocity"] == 96
test("Machine: long-form words quarter/forte", test_machine_long_words)


def test_machine_ch0_no_brackets():
    mlp.clear()
    ev = parse_machine_line("CH0 T0 N60 D500 V80", {"bpm": 120})
    assert ev is not None and ev["channel"] == 0
test("Machine: CH0 without brackets accepted", test_machine_ch0_no_brackets)


def test_machine_bare_trailing_velocity():
    mlp.clear()
    ev = parse_machine_line("T0 N60 D100 80", {"bpm": 120})
    assert ev is not None and ev["velocity"] == 80
test("Machine: bare trailing number = velocity (legacy)", test_machine_bare_trailing_velocity)


def test_machine_unknown_dur_word():
    mlp.clear()
    ev = parse_machine_line("T0 N C4 D bogus V80", {"bpm": 120})
    assert ev is None
    assert any(p["code"] == "E054" for p in mlp)
test("Machine: unknown duration word -> E054", test_machine_unknown_dur_word)


# === Strict human parsing ===

def test_human_unknown_quality():
    hlp.clear()
    evs, _ = parse_human_line("play chord(C, bogus) @dur:h @vel:mf", 0, 120, {})
    assert any(p["code"] == "E059" for p in hlp)
test("Human: unknown quality -> E059 (no silent major)", test_human_unknown_quality)


def test_human_unknown_property():
    hlp.clear()
    evs, _ = parse_human_line("play note(C4) @dur:q @vel:mf @bogus:1", 0, 120, {})
    assert any(p["code"] == "E057" for p in hlp)
test("Human: unknown @property -> E057", test_human_unknown_property)


def test_human_bad_velocity_word():
    hlp.clear()
    evs, _ = parse_human_line("play note(C4) @dur:q @vel:bogus", 0, 120, {})
    assert any(p["code"] == "E055" for p in hlp)
test("Human: unknown velocity word -> E055", test_human_bad_velocity_word)


def test_human_missing_dur_vel():
    hlp.clear()
    evs, _ = parse_human_line("play note(C4)", 0, 120, {})
    assert any(p["code"] == "E062" for p in hlp)
    assert any(p["code"] == "E063" for p in hlp)
test("Human: missing @dur + @vel flagged", test_human_missing_dur_vel)


def test_human_valid():
    hlp.clear()
    evs, _ = parse_human_line("play note(C4) @dur:q @vel:mf", 0, 120, {})
    assert evs and len(evs) == 1 and not hlp
test("Human: valid line, zero problems", test_human_valid)


# === Math engine ===

def test_math_unary_pow():
    val, err = evaluate_expression("-2^2")
    assert err is None and val == -4, f"-2^2 = {val} (want -4)"
test("Math: -2^2 = -4 (unary precedence)", test_math_unary_pow)


def test_math_right_assoc_pow():
    val, err = evaluate_expression("2^3^2")
    assert err is None and val == 512, f"2^3^2 = {val} (want 512)"
test("Math: 2^3^2 = 512 (right-assoc)", test_math_right_assoc_pow)


def test_math_no_truncation():
    val, err = evaluate_expression("2 3")
    assert val is None and "Unexpected token" in err
test("Math: leftover tokens error (no truncation)", test_math_no_truncation)


def test_math_incomplete():
    val, err = evaluate_expression("5 +")
    assert val is None and "Incomplete" in err
test("Math: incomplete expression errors", test_math_incomplete)


def test_math_unknown_function():
    val, err = evaluate_expression("nofunc(2)")
    assert val is None and "Unknown function" in err
test("Math: unknown function errors", test_math_unknown_function)


def test_math_div_zero():
    val, err = evaluate_expression("1 / 0")
    assert val is None and "Division by zero" in err
test("Math: division by zero errors", test_math_div_zero)


def test_math_nested_calls():
    val, err = evaluate_expression("sin(sqrt(9))")
    assert err is None and abs(val - 0.141120) < 1e-4
test("Math: nested function calls", test_math_nested_calls)


# === v4 path ===

def test_v4_detection_polyrhythm():
    with open(os.path.join(ROOT, "samples", "v4-current", "generative", "polyrhythm_complex.e"),
              encoding="utf-8", errors="replace") as f:
        t = f.read()
    assert detect_syntax_version(t) == "v4"
test("v4: polyrhythm file detected as v4", test_v4_detection_polyrhythm)


def test_v4_polyrhythm_compiles():
    with open(os.path.join(ROOT, "samples", "v4-current", "generative", "polyrhythm_complex.e"),
              encoding="utf-8", errors="replace") as f:
        t = f.read()
    ev, bp = compile_source(t)
    assert len(ev) >= 10, f"polyrhythm should produce events, got {len(ev)}"
test("v4: polyrhythm no longer silently 0 events", test_v4_polyrhythm_compiles)


def test_v4_all_math_samples_compile():
    for p in sorted(glob.glob(os.path.join(ROOT, "samples", "v4-current", "math", "*.e"))):
        with open(p, encoding="utf-8", errors="replace") as f:
            t = f.read()
        ev, bp = compile_source(t)
        assert len(ev) >= 8, f"{os.path.basename(p)}: expected >=8 events, got {len(ev)}"
test("v4: all math samples produce events", test_v4_all_math_samples_compile)


def test_v4_converter_loop_roundtrip():
    from plugins.portbaby.v1_to_v4 import convert
    events = [{"timestamp": i * 100, "midi": 60 + i, "duration": 80,
               "velocity": 90, "pan": 0.0, "bend": 0, "channel": None}
              for i in range(24)]
    out = convert(events, 120)
    assert "for $i = 0 to 23" in out
    assert "$beat = 60000 / $bpm" in out
    assert "$i * $beat / 5" in out
    ev2, _ = compile_source(out)
    orig = sorted((e["timestamp"], e["midi"], e["duration"]) for e in events)
    new = sorted((e["timestamp"], e["midi"], e["duration"]) for e in ev2)
    assert orig == new, "round-trip mismatch"
test("v4 converter: loop+math emission, exact round-trip", test_v4_converter_loop_roundtrip)


def test_v4_converter_channel_ramp():
    from plugins.portbaby.v1_to_v4 import convert
    events = [{"timestamp": i * 250, "midi": 48 + i * 2, "duration": 200,
               "velocity": 60 + i * 6, "pan": 0.0, "bend": 0, "channel": 1}
              for i in range(10)]
    out = convert(events, 120)
    ev2, _ = compile_source(out)
    orig = sorted((e["timestamp"], e["midi"], e["duration"], e["velocity"], e.get("channel")) for e in events)
    new = sorted((e["timestamp"], e["midi"], e["duration"], e["velocity"], e.get("channel")) for e in ev2)
    assert orig == new
test("v4 converter: channel + velocity ramp round-trip", test_v4_converter_channel_ramp)


# === Memory cap ===

def test_mem_cap_graceful():
    old = get_unroll_cap()
    set_unroll_cap(5000)
    try:
        try:
            compile_source("repeat 200000 {\nT0 N60 D100\n}", strict=True)
            raise AssertionError("should have raised LoopError")
        except LoopError as e:
            assert "beyond 5000" in str(e)
    finally:
        set_unroll_cap(old)
test("Memory: hard cap raises clear LoopError (strict)", test_mem_cap_graceful)


def test_mem_cap_normal():
    old = get_unroll_cap()
    set_unroll_cap(100000)
    try:
        ev, _ = compile_source("repeat 10000 {\nT0 N60 D100\n}")
        assert len(ev) == 10000
    finally:
        set_unroll_cap(old)
test("Memory: normal compile unaffected by cap", test_mem_cap_normal)


# === Diagnostics surfaced from compile (lenient) ===

def test_compile_surfaces_loop_error():
    from ep_compiler.mode_v1_machine import last_problems
    old = get_unroll_cap()
    set_unroll_cap(300)
    last_problems.clear()
    try:
        compile_source("repeat 5000 {\nT0 N60 D100\n}")
        assert any(p["code"] == "E136" for p in last_problems), "loop error not surfaced"
    finally:
        set_unroll_cap(old)
test("Diagnostics: loop cap error surfaced to store", test_compile_surfaces_loop_error)


def test_strict_mode_raises_compile_error():
    try:
        compile_source("T0 N60 D500 V80 GARBAGE", strict=True)
        raise AssertionError("strict should have raised CompileError")
    except Exception as e:
        assert "Strict compile failed" in str(e), f"got {e}"
test("Strict: garbage line raises CompileError", test_strict_mode_raises_compile_error)


def test_strict_mode_clean_passes():
    ev, bp = compile_source("T0 N60 D500 V80", strict=True)
    assert len(ev) == 1
test("Strict: clean source compiles", test_strict_mode_clean_passes)


# === v4 punctuation ===

def test_punct_semicolons():
    ev, bp = compile_source("T0 N60 D500; T500 N62 D500; T1000 N64 D500")
    assert len(ev) == 3 and ev[0]["timestamp"] == 0 and ev[2]["timestamp"] == 1000
test("Punct: semicolon statement separator", test_punct_semicolons)


def test_punct_labeled_fields():
    ev, bp = compile_source("T:0 N:60 D:500 V:80; T:500 N:62 D:500 V:90")
    assert len(ev) == 2 and ev[0]["velocity"] == 80 and ev[1]["velocity"] == 90
test("Punct: labeled fields T:0 N:60 D:500 V:80", test_punct_labeled_fields)


def test_punct_labeled_words():
    ev, bp = compile_source("T:0 N:C4 D:q V:mf; T:500 N:D4 D:e V:f")
    assert len(ev) == 2 and ev[0]["midi"] == 60 and ev[0]["duration"] == 500
test("Punct: labeled word fields N:C4 D:q V:mf", test_punct_labeled_words)


def test_punct_comma_groups():
    ev, bp = compile_source("// v4\n[C4, E4, G4](3:2)")
    assert len(ev) == 3
test("Punct: comma-separated note groups", test_punct_comma_groups)


def test_punct_angle_brackets():
    ev, bp = compile_source("// v4\n<C4 E4 G4>(3:2)")
    assert len(ev) == 3
test("Punct: angle-bracket note groups", test_punct_angle_brackets)


def test_punct_pipe_chord():
    ev, bp = compile_source("// v4\n[C4|E4|G4](2:1)")
    assert len(ev) == 6
    assert sorted(set(e["midi"] for e in ev)) == [60, 64, 67]
test("Punct: pipe-parallel chords", test_punct_pipe_chord)


def test_punct_pipe_shorthand():
    ev, bp = compile_source("// v4\nCH0 3:2 C4|E4 e")
    assert len(ev) == 6
test("Punct: pipe chords in shorthand polyrhythm", test_punct_pipe_shorthand)


def test_punct_backslash():
    src = "// v4\nT0 N60 D500 \\\n T500 N62 D500"
    ev, bp = compile_source(src)
    assert len(ev) == 2
test("Punct: backslash line continuation", test_punct_backslash)


def test_punct_semicolon_protects_loop_math():
    src = "// v4\nfor $i = 0 to 3 { T{$i * 100} N60 D100 }; T500 N62 D500"
    ev, bp = compile_source(src)
    assert len(ev) == 5
test("Punct: semicolon outside loop braces", test_punct_semicolon_protects_loop_math)


def test_punct_semicolon_human():
    ev, bp = compile_source("// v4\nplay note(C4) @dur:q @vel:mf; play note(D4) @dur:q @vel:mf")
    assert len(ev) == 2
test("Punct: human statements on one line", test_punct_semicolon_human)


def test_punct_comment_protected():
    ev, bp = compile_source("// v4\nT0 N60 D500  // T; comment\nT100 N{60 + 2} D100")
    assert len(ev) == 2 and ev[1]["midi"] == 62
test("Punct: semicolons inside comments safe", test_punct_comment_protected)


def test_punct_single_line_loop():
    ev, bp = compile_source("for $i = 0 to 3 { T{$i * 100} N60 D100 }")
    assert len(ev) == 4
test("Punct: single-line for loop body", test_punct_single_line_loop)


def test_punct_converter_semicolons():
    from plugins.portbaby.v1_to_v4 import convert
    events = [{"timestamp": i * 100, "midi": 60 + (i % 12), "duration": 80,
               "velocity": 90, "pan": 0.0, "bend": 0, "channel": None}
              for i in range(30)]
    out = convert(events, 120)
    ev2, _ = compile_source(out)
    orig = sorted((e["timestamp"], e["midi"], e["duration"]) for e in events)
    new = sorted((e["timestamp"], e["midi"], e["duration"]) for e in ev2)
    assert orig == new
test("Punct: v4 converter output round-trips with ';' packing", test_punct_converter_semicolons)


print(f"\n{'='*50}")
print(f"PARSE/MATH/V4/MEM TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
