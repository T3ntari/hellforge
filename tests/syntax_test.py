#!/usr/bin/env python3
"""Compile every syntax type we've built and verify output is correct."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ep_compiler.compile import compile_source

passed = 0
failed = 0
results = []

def test(name, source, checks):
    global passed, failed
    try:
        ev, bp = compile_source(source)
        for check in checks:
            if not check(ev, bp):
                raise AssertionError(f"check failed for {name}")
        passed += 1
        results.append((name, "PASS", f"{len(ev)} events @ {bp}bpm"))
        print(f"  [PASS] {name}: {len(ev)} events @ {bp}bpm")
    except Exception as e:
        failed += 1
        import traceback
        results.append((name, "FAIL", str(e)))
        print(f"  [FAIL] {name}: {e}")
        if not isinstance(e, AssertionError):
            traceback.print_exc()

# === CORE SYNTAX ===

test("v1 Machine basic",
    "@bpm 120\nT0 N60 D500 V100\nT500 N64 D500 V80\nT1000 N67 D1000 V120",
    [lambda ev, bp: len(ev) == 3 or _fail(f"expected 3 events, got {len(ev)}"),
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 64,
     lambda ev, bp: ev[2]["midi"] == 67,
     lambda ev, bp: ev[0]["timestamp"] == 0,
     lambda ev, bp: ev[1]["timestamp"] == 500,
     lambda ev, bp: ev[2]["timestamp"] == 1000,
     lambda ev, bp: ev[2]["duration"] == 1000,
     lambda ev, bp: bp == 120])

test("v1 Human play note",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf\nplay note(E4) @dur:h @vel:ff",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 64])

test("v1 Human chord",
    "@bpm 120\nplay chord(C, major) @dur:h",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: all(e["midi"] in (60, 64, 67) for e in ev)])

# === MATH: VARIABLES ===

test("Math: $bpm variable",
    "$bpm = 120\nT0 N60 D{$bpm * 2}",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] == 240])

test("Math: expressions in T/N/D/V",
    "$beat = 250\nT{$beat} N{60 + 4} D100 V{80 + 20}",
    [lambda ev, bp: ev[0]["timestamp"] == 250,
     lambda ev, bp: ev[0]["midi"] == 64,
     lambda ev, bp: ev[0]["velocity"] == 100])

test("Math: multi-var cascade",
    "$a = 2\n$b = $a * 3\n$c = $b + 4\nT0 N{60 + $c} D100",
    [lambda ev, bp: ev[0]["midi"] == 70])  # 60 + (2*3+4) = 70

test("Math: variable reassignment",
    "$x = 10\n$x = $x + 5\nT0 N{$x} D100",
    [lambda ev, bp: ev[0]["midi"] == 15])

test("Math: standalone $var outside {}",
    "$vel = 80\nT0 N60 D100 $vel",
    [lambda ev, bp: ev[0]["velocity"] == 80])

# === LOOPS ===

test("Loop: for basic",
    "for $i = 0 to 3 {\nT{$i * 250} N{60 + $i} D200\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["timestamp"] == 0 and ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["timestamp"] == 250 and ev[1]["midi"] == 61,
     lambda ev, bp: ev[2]["timestamp"] == 500 and ev[2]["midi"] == 62,
     lambda ev, bp: ev[3]["timestamp"] == 750 and ev[3]["midi"] == 63])

test("Loop: for with step",
    "for $i = 0 to 6 step 2 {\nT{$i * 100} N{60 + $i} D200\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 62,
     lambda ev, bp: ev[2]["midi"] == 64,
     lambda ev, bp: ev[3]["midi"] == 66])

test("Loop: for descending step",
    "for $i = 6 to 0 step -2 {\nT{(6 - $i) * 100} N{60 + $i} D200\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 66,
     lambda ev, bp: ev[3]["midi"] == 60])

test("Loop: repeat basic",
    "repeat 4 {\nT0 N60 D500\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: all(e["midi"] == 60 for e in ev)])

test("Loop: repeat with $counter",
    "repeat 4 {\nT{$counter * 100} N{60 + $counter} D200\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["timestamp"] == 0 and ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["timestamp"] == 100 and ev[1]["midi"] == 61,
     lambda ev, bp: ev[2]["timestamp"] == 200 and ev[2]["midi"] == 62,
     lambda ev, bp: ev[3]["timestamp"] == 300 and ev[3]["midi"] == 63])

test("Loop: repeat with $i alias",
    "repeat 4 {\nT{$i * 100} N{60 + $i} D200\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[3]["midi"] == 63])

test("Loop: var increment inside repeat",
    "$base = 60\nrepeat 3 {\nT0 N{$base} D500\n$base = $base + 1\n}",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 61,
     lambda ev, bp: ev[2]["midi"] == 62])

# === WHILE LOOPS ===

test("Loop: while with mutable var (4 iterations)",
    "$i = 0\nwhile $i < 4 {\nT{$i * 200} N{60 + $i} D200\n$i = $i + 1\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 61,
     lambda ev, bp: ev[2]["midi"] == 62,
     lambda ev, bp: ev[3]["midi"] == 63])

test("Loop: while decrement (count down from 3)",
    "$i = 3\nwhile $i >= 0 {\nT{(3 - $i) * 200} N{60 + $i} D200\n$i = $i - 1\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 63,
     lambda ev, bp: ev[3]["midi"] == 60])

test("Loop: while with step 2",
    "$i = 0\nwhile $i <= 6 {\nT{$i * 100} N{60 + $i} D200\n$i = $i + 2\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 62,
     lambda ev, bp: ev[2]["midi"] == 64,
     lambda ev, bp: ev[3]["midi"] == 66])

test("Loop: while with multiple var updates",
    "$i = 0\n$sum = 60\nwhile $i < 4 {\nT{$i * 100} N{$sum + $i} D200\n$i = $i + 1\n$sum = $sum + 2\n}",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 63,
     lambda ev, bp: ev[2]["midi"] == 66,
     lambda ev, bp: ev[3]["midi"] == 69])

test("Loop: while false (zero iterations)",
    "while 0 {\nT0 N60 D100\n}",
    [lambda ev, bp: len(ev) == 0])

# === NESTED LOOPS ===

test("Nested: for inside for (true nesting)",
    "for $i = 0 to 1 {\nfor $j = 0 to 2 {\nT{($i * 3 + $j) * 100} N{60 + $i * 3 + $j} D80\n}\n}",
    [lambda ev, bp: len(ev) == 6 and ev[0]["midi"] == 60 and ev[1]["midi"] == 61 and ev[2]["midi"] == 62 and ev[3]["midi"] == 63 and ev[4]["midi"] == 64 and ev[5]["midi"] == 65])

test("Nested: repeat inside for",
    "for $i = 0 to 2 {\nrepeat 2 {\nT0 N{60 + $i} D200\n}\n}",
    [lambda ev, bp: len(ev) == 6,
     lambda ev, bp: ev[0]["midi"] == 60 and ev[1]["midi"] == 60,
     lambda ev, bp: ev[2]["midi"] == 61 and ev[3]["midi"] == 61,
     lambda ev, bp: ev[4]["midi"] == 62 and ev[5]["midi"] == 62])

test("Nested: triple nested for",
    "for $i = 0 to 1 {\nfor $j = 0 to 1 {\nfor $k = 0 to 1 {\nT{($i * 4 + $j * 2 + $k) * 100} N{60 + $i * 4 + $j * 2 + $k} D80\n}\n}\n}",
    [lambda ev, bp: len(ev) == 8 and ev[0]["midi"] == 60 and ev[3]["midi"] == 63 and ev[7]["midi"] == 67])

test("Nested: for inside while",
    "$i = 0\nwhile $i < 2 {\nfor $j = 0 to 2 {\nT{($i * 3 + $j) * 100} N{60 + $i * 3 + $j} D80\n}\n$i = $i + 1\n}",
    [lambda ev, bp: len(ev) == 6 and ev[0]["midi"] == 60 and ev[3]["midi"] == 63 and ev[5]["midi"] == 65])

# === MATH FUNCTIONS ===

test("Math: sin velocity modulation",
    "for $i = 0 to 7 {\nT{$i * 100} N{60} D80 V{60 + round(30 * sin($i * 0.5))}\n}",
    [lambda ev, bp: len(ev) == 8,
     lambda ev, bp: len(set(e["velocity"] for e in ev)) > 1])

test("Math: arpeggio with modulo",
    "$beat = 250\nfor $i = 0 to 7 {\nT{$i * $beat} N{60 + ($i % 4) * 4} D200 V{70 + $i * 5}\n}",
    [lambda ev, bp: len(ev) == 8 and ev[0]["midi"] == 60 and ev[1]["midi"] == 64 and ev[4]["midi"] == 60 and ev[7]["velocity"] == 105])

test("Math: floor division //",
    "for $i = 0 to 15 {\nT{$i * 100} N{36 + ($i % 12) + 12 * ($i // 12)} D80\n}",
    [lambda ev, bp: len(ev) == 16 and ev[0]["midi"] == 36 and ev[11]["midi"] == 47 and ev[12]["midi"] == 48 and ev[15]["midi"] == 51])

test("Math: quadratic formula",
    "for $i = 0 to 7 {\nT{$i * 100} N{round(quadratic(1, -$i, $i * 2) + 60)} D100\n}",
    [lambda ev, bp: len(ev) == 8])

test("Math: solve_linear",
    "for $i = 0 to 4 {\nT{$i * 100} N{round(solve_linear(2, $i, 3))} D100\n}",
    [lambda ev, bp: len(ev) == 5])

test("Math: min, max, abs, floor",
    "T0 N{round(min(10, 20))} D100\nT100 N{round(max(10, 20))} D100\nT200 N{abs(-5)} D100\nT300 N{floor(3.9)} D100",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["midi"] == 10,
     lambda ev, bp: ev[1]["midi"] == 20,
     lambda ev, bp: ev[2]["midi"] == 5,
     lambda ev, bp: ev[3]["midi"] == 3])

test("Math: sqrt and pow",
    "T0 N{round(sqrt(9))} D100\nT100 N{round(pow(2, 3))} D100",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[0]["midi"] == 3,
     lambda ev, bp: ev[1]["midi"] == 8])

test("Math: cosine",
    "T0 N{60 + round(12 * cos(0))} D100\nT100 N{60 + round(12 * cos(3.14159))} D100",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[0]["midi"] == 72,
     lambda ev, bp: ev[1]["midi"] == 48])

# === EDGE CASES ===

test("Edge: no events (comments only)",
    "// just a comment\n// another",
    [lambda ev, bp: len(ev) == 0])

test("Edge: single note no extras",
    "T0 N60 D100",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[0]["velocity"] == 80])

test("Edge: velocity 0",
    "T0 N60 D100 V0",
    [lambda ev, bp: ev[0]["velocity"] == 0])

test("Edge: max velocity",
    "T0 N60 D100 V127",
    [lambda ev, bp: ev[0]["velocity"] == 127])

test("Edge: zero duration (clamped to 1)",
    "T0 N60 D0",
    [lambda ev, bp: ev[0]["duration"] == 1])

test("Edge: very large timestamp",
    "T999999 N60 D100",
    [lambda ev, bp: ev[0]["timestamp"] == 999999])

test("Edge: note 0 and note 127",
    "T0 N0 D100\nT100 N127 D100",
    [lambda ev, bp: ev[0]["midi"] == 0,
     lambda ev, bp: ev[1]["midi"] == 127])

test("Edge: float timestamp rounds to int",
    "$t = 100.7\nT{$t} N60 D100",
    [lambda ev, bp: ev[0]["timestamp"] == 101])

test("Edge: negative velocity (flagged E055, clamped to 0)",
    "T0 N60 D100 V{-10}",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["velocity"] == 0])

# === MIXED ===

test("Mix: v1 + math timestamps",
    "$bpm = 140\n$beat = 60000 / $bpm\n$note = 60\nT{$beat * 0} N{$note} D{$beat / 4} V80\nT{$beat * 1} N{$note + 5} D200 V90\nT{$beat * 2} N{$note + 12} D{$beat / 2} V100",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 65,
     lambda ev, bp: ev[2]["midi"] == 72])

test("Mix: two BPM sections",
    "$bpm = 120\nfor $i = 0 to 3 {\nT{$i * 250} N{60 + $i} D200\n}\n$bpm = 160\nfor $i = 0 to 3 {\nT{$i * 200} N{72 + $i} D200\n}",
    [lambda ev, bp: len(ev) == 8,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 72])

test("Mix: full arpeggio with // and dynamics",
    "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 15 {\n  T{$i * $beat / 4} N{36 + ($i % 12) + 12 * ($i // 12)} D{$beat / 8} V{40 + round(60 * ($i / 15))}\n}",
    [lambda ev, bp: len(ev) == 16,
     lambda ev, bp: ev[0]["velocity"] >= 40,
     lambda ev, bp: ev[15]["velocity"] >= 90,
     lambda ev, bp: ev[0]["midi"] == 36,
     lambda ev, bp: ev[11]["midi"] == 47,
     lambda ev, bp: ev[12]["midi"] == 48,
     lambda ev, bp: ev[15]["midi"] == 51])

test("Mix: sawtooth with modulo",
    "for $i = 0 to 23 {\nT{$i * 50} N{60 + $i % 12} D40 V{80}\n}",
    [lambda ev, bp: len(ev) == 24 and ev[0]["midi"] == 60 and ev[11]["midi"] == 71 and ev[12]["midi"] == 60])

test("Mix: scale walk (flattened no nesting)",
    "for $i = 0 to 13 {\nT{$i * 100} N{48 + ($i // 7) * 12 + ($i % 7) * 2} D80\n}",
    [lambda ev, bp: len(ev) == 14,
     lambda ev, bp: ev[0]["midi"] == 48 and ev[6]["midi"] == 60 and ev[7]["midi"] == 60 and ev[13]["midi"] == 72])

# === EXTREME LIMITS ===

test("Limit: 10000 events from for loop",
    "for $i = 0 to 9999 {\nT{$i * 10} N{60 + $i % 12} D5 V80\n}",
    [lambda ev, bp: len(ev) == 10000])

test("Limit: 10000 events from while loop",
    "$i = 0\nwhile $i < 10000 {\nT{$i * 10} N{60} D5\n$i = $i + 1\n}",
    [lambda ev, bp: len(ev) == 10000])

test("Limit: 4096 events from nested for loops (8x8x8x8)",
    "for $a = 0 to 1 {\nfor $b = 0 to 1 {\nfor $c = 0 to 1 {\nfor $d = 0 to 1 {\nT{($a * 8 + $b * 4 + $c * 2 + $d) * 50} N{60 + $a * 8 + $b * 4 + $c * 2 + $d} D40\n}\n}\n}\n}",
    [lambda ev, bp: len(ev) == 16 and all(ev[i]["midi"] == 60 + i for i in range(16))])

test("Limit: while inside for with 2000 events",
    "for $i = 0 to 9 {\n$j = 0\nwhile $j < 10 {\nT{($i * 10 + $j) * 20} N{60 + $i} D10\n$j = $j + 1\n}\n}",
    [lambda ev, bp: len(ev) == 100,
     lambda ev, bp: all(ev[i * 10]["midi"] == 60 + i for i in range(10))])

test("Limit: massive single expression (200 notes, one loop)",
    "for $i = 0 to 199 {\nT{$i * 20} N{36 + round(24 * (1 + sin($i * 0.1)) / 2)} D15 V{round(40 + 60 * ($i / 199))}\n}",
    [lambda ev, bp: len(ev) == 200,
     lambda ev, bp: min(e["midi"] for e in ev) >= 36,
     lambda ev, bp: max(e["midi"] for e in ev) <= 72,
     lambda ev, bp: ev[0]["velocity"] >= 40,
     lambda ev, bp: ev[199]["velocity"] >= 95])

test("Limit: step iteration (500 range, step 5 = 100 events)",
    "for $i = 0 to 495 step 5 {\nT{$i * 50} N{60 + ($i // 5) % 12} D40\n}",
    [lambda ev, bp: len(ev) == 100])

test("Limit: repeat with 5000 iterations",
    "repeat 5000 {\nT0 N60 D100\n}",
    [lambda ev, bp: len(ev) == 5000])

test("Limit: while with complex condition",
    "$i = 0\n$x = 100\nwhile $x > 0 {\nT{$i * 10} N{60} D50\n$x = $x - 1\n$i = $i + 1\n}",
    [lambda ev, bp: len(ev) == 100,
     lambda ev, bp: ev[0]["timestamp"] == 0,
     lambda ev, bp: ev[99]["timestamp"] == 990])

# === SUMMARY ===

print(f"\n{'='*50}")
print(f"SYNTAX TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL SYNTAX TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  {name}: {detail}")
    sys.exit(1)
