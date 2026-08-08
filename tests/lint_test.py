#!/usr/bin/env python3
"""HELLFORGE linter tests — catalog size, severity, core checks, integrations."""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ep_compiler.lint import (
    lint_source,
    format_diags,
    catalog_stats,
    CATALOG,
    FATAL,
    ERROR,
    WARNING,
    INFO,
)

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


# === Catalog size ===

def test_catalog_size():
    stats = catalog_stats()
    assert stats["errors"] >= 200, f"need 200+ errors, got {stats['errors']}"
    assert stats["warnings"] >= 100, f"need 100+ warnings, got {stats['warnings']}"
    assert stats["fatals"] >= 1
    print(f"   errors={stats['errors']}, warnings={stats['warnings']}, info={stats['info']}")
test("Catalog: 200+ errors, 100+ warnings", test_catalog_size)


def test_catalog_codes_unique():
    codes = list(CATALOG.keys())
    assert len(codes) == len(set(codes)), "duplicate codes!"
    e_codes = [c for c in codes if c.startswith("E")]
    w_codes = [c for c in codes if c.startswith("W")]
    assert len(e_codes) == 240, f"expected 240 E codes, got {len(e_codes)}"
    assert len(w_codes) == 120, f"expected 120 W codes, got {len(w_codes)}"
test("Catalog: 240 E-codes + 120 W-codes, all unique", test_catalog_codes_unique)


# === Severity ===

def test_severity_fatal():
    diags = lint_source("/* unclosed\nT0 N60 D500 V80")
    assert any(d["code"] == "E001" and d["severity"] == FATAL for d in diags)
test("Severity: unclosed comment is FATAL", test_severity_fatal)


def test_severity_error():
    diags = lint_source("@bpm 500\nT0 N60 D500 V80")
    assert any(d["code"] == "E036" and d["severity"] == ERROR for d in diags)
test("Severity: bad @bpm is ERROR", test_severity_error)


def test_severity_warning():
    diags = lint_source("@bpm 120\n@tempo 90\nT0 N60 D500 V80")
    assert any(d["code"] == "W008" and d["severity"] == WARNING for d in diags)
test("Severity: @tempo alias is WARNING", test_severity_warning)


# === Core checks ===

def test_bad_note_range():
    diags = lint_source("@bpm 120\nT0 N200 D500 V80")
    assert any(d["code"] == "E053" for d in diags)
test("Check: note out of range", test_bad_note_range)


def test_piano_range_warning():
    diags = lint_source("@bpm 120\nT0 N10 D500 V80")
    assert any(d["code"] == "W018" for d in diags)
test("Check: outside piano range warns", test_piano_range_warning)


def test_missing_vel():
    diags = lint_source("play note(C4) @dur:q")
    assert any(d["code"] == "E063" for d in diags)
test("Check: missing @vel on play note", test_missing_vel)


def test_unknown_directive():
    diags = lint_source("@bpm 120\n@bogus 5\nT0 N60 D500 V80")
    assert any(d["code"] == "E035" for d in diags)
test("Check: unknown directive", test_unknown_directive)


def test_bad_for_loop():
    diags = lint_source("@bpm 120\nfor $i = 0 7 {\n}")
    assert any(d["code"] == "E131" for d in diags)
test("Check: malformed for loop", test_bad_for_loop)


def test_negative_repeat():
    diags = lint_source("@bpm 120\nrepeat 0 {\nT0 N60 D100\n}")
    assert any(d["code"] == "E134" for d in diags)
test("Check: zero repeat count", test_negative_repeat)


def test_v1_deprecated():
    diags = lint_source("#MACHINE\nT0 N60 D500 V80")
    assert any(d["code"] == "W001" for d in diags)
test("Check: v1 deprecation warning", test_v1_deprecated)


def test_unused_variable():
    diags = lint_source("@bpm 120\n$unused = 5\nT0 N60 D500 V80")
    assert any(d["code"] == "W023" for d in diags)
test("Check: unused variable", test_unused_variable)


def test_missing_bpm():
    diags = lint_source("T0 N60 D500 V80")
    assert any(d["code"] == "W011" for d in diags)
test("Check: missing @bpm warns", test_missing_bpm)


def test_clean_file_minimal_warnings():
    diags = lint_source("@bpm 120\n@key C_Major\nT0 N60 D500 V80")
    assert not any(d["severity"] in (FATAL, ERROR) for d in diags)
test("Check: clean file has no errors", test_clean_file_minimal_warnings)


def test_duplicate_events_warning():
    diags = lint_source("@bpm 120\nT0 N60 D500 V80\nT0 N60 D500 V80")
    assert any(d["code"] == "W022" for d in diags)
test("Check: duplicate events warn", test_duplicate_events_warning)


def test_machine_velocity_float_warning():
    diags = lint_source("@bpm 120\nT0 N60 D500 V80.5")
    assert any(d["code"] == "W019" for d in diags)
test("Check: float velocity warns", test_machine_velocity_float_warning)


def test_inherit_missing_file():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "proj.ei")
        with open(p, "w") as f:
            f.write('inherit "nope.e"\n')
        diags = lint_source(open(p).read(), path=p)
        assert any(d["code"] == "E221" for d in diags)
test("Check: missing inherit target", test_inherit_missing_file)


def test_empty_file():
    diags = lint_source("   \n  \n")
    assert any(d["code"] == "E229" for d in diags)
test("Check: empty file", test_empty_file)


def test_format_diags_output():
    out = format_diags([{"code": "E036", "severity": ERROR, "line": 1, "message": "x"}])
    assert "ERROR" in out and "E036" in out
test("Format: human-readable report", test_format_diags_output)


def test_docstring_examples_lint_clean():
    """The lint module's own docstring examples are valid E."""
    diags = lint_source("@bpm 120\nT0 N60 D500 V80\nT500 N64 D500 V80")
    assert not any(d["severity"] == FATAL for d in diags)
test("Regression: basic docstring example clean", test_docstring_examples_lint_clean)


# === Revamp: versions, comments, v2/v3 values, real-file patterns ===

def test_version_detection_v2():
    diags = lint_source("// v2 DEPRECATED\nVersion: v2 (semantic mode) - DEPRECATED\n"
                        "[Section: Intro]\nKey: C_Major\nplay(C4, q, mf)\n")
    codes = [d["code"] for d in diags]
    assert "W002" in codes and "I003" in codes, codes
    assert "E056" not in codes, codes
test("Version: v2 detected from comments, no false E056", test_version_detection_v2)


def test_version_detection_v3():
    diags = lint_source("// v3 supported\nVersion: v3 (consolidated engine)\nC4 q\nC4 q mf\n")
    codes = [d["code"] for d in diags]
    assert "W003" in codes and "I002" in codes, codes
test("Version: v3 detected", test_version_detection_v3)


def test_comment_todo_markers():
    diags = lint_source("// TODO: fix this\n// FIXME: here\n// XXX: urgent\nT0 N60 D500 V80\n")
    codes = [d["code"] for d in diags]
    assert "I016" in codes and "I017" in codes and "I018" in codes, codes
test("Comments: TODO/FIXME/XXX infos", test_comment_todo_markers)


def test_v2_value_validation():
    diags = lint_source("// v2\nplay(H9, q, ff)\nplay(C4, xyz, mf)\nplay(C4, q, 500)\n")
    codes = [d["code"] for d in diags]
    assert "E060" in codes, codes
    assert "E054" in codes, codes
    assert "E055" in codes, codes
test("v2 values: bad note/dur/vel flagged", test_v2_value_validation)


def test_v3_value_validation():
    diags = lint_source("// v3\nC4 q\nC5 xyz\n")
    codes = [d["code"] for d in diags]
    assert "E054" in codes, codes
    assert "E056" not in codes, codes
test("v3 values: bad duration flagged, no E056", test_v3_value_validation)


def test_human_numeric_ranges():
    diags = lint_source("play note(C4) @dur:q @vel:500\nplay chord(C, major) @pan:5 @ch:99\n")
    codes = [d["code"] for d in diags]
    assert "E055" in codes and "E040" in codes and "E043" in codes, codes
test("Human: numeric value ranges (vel/pan/ch)", test_human_numeric_ranges)


def test_machine_hash_comments():
    diags = lint_source("T8728 N62 D3273 V0.35          # D4 — held 3 beats\n")
    codes = [d["code"] for d in diags]
    assert "E056" not in codes, codes
test("Machine: E++ style # comments allowed", test_machine_hash_comments)


def test_fraction_velocity_policy():
    src = "// v4\n" + "\n".join(f"T{i*100} N{60+i%12} D500 V0.4{i%10}" for i in range(8))
    diags = lint_source(src)
    codes = [d["code"] for d in diags]
    assert "W019" not in codes, codes
    assert "I020" in codes, codes
test("Velocity: fraction scale -> single I020, no W019 flood", test_fraction_velocity_policy)


def test_mixed_velocity_scale_keeps_warnings():
    src = "// v4\nT0 N60 D500 V80\nT100 N62 D500 V0.5\nT200 N64 D500 V90\n"
    diags = lint_source(src)
    codes = [d["code"] for d in diags]
    assert "W019" in codes, codes
    assert "I020" not in codes, codes
test("Velocity: mixed scales keep W019 per note", test_mixed_velocity_scale_keeps_warnings)


print(f"\n{'='*50}")
print(f"LINTER TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LINTER TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
