#!/usr/bin/env python3
"""Test all 7 piano-essential v4 features end-to-end."""
import sys
import os
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

def _fail(msg):
    raise AssertionError(msg)

# ============================================================
# 1. SUSTAIN PEDAL
# ============================================================

test("Sustain: pedal on/off statements",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf\npedal on\nplay note(E4) @dur:q @vel:mf\npedal off\nplay note(G4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) >= 5,
     lambda ev, bp: any(e.get("sustain") == 127 for e in ev),
     lambda ev, bp: any(e.get("sustain") == 0 for e in ev)])

test("Sustain: @pedal prop on note",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @pedal:100",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0].get("sustain") == 100])

test("Sustain: @sustain prop on note",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @sustain:64",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0].get("sustain") == 64])

test("Sustain: pedal events have no midi/vel impact",
    "@bpm 120\npedal on\npedal off",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[0].get("sustain") == 127 and ev[0].get("midi") == 0,
     lambda ev, bp: ev[1].get("sustain") == 0])

# ============================================================
# 2. RESTS
# ============================================================

test("Rest: rest q statement advances cursor",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf\nrest q\nplay note(D4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 62])

test("Rest: rest 500ms",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf\nrest 500ms\nplay note(D4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[1]["timestamp"] > ev[0]["timestamp"]])

test("Rest: R q shorthand",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf\nR q\nplay note(G4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 2])

test("Rest: rest h (half note)",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf\nrest h\nplay note(C5) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 2,
     lambda ev, bp: ev[1]["timestamp"] > ev[0]["timestamp"] + 500])

# ============================================================
# 3. ARTICULATIONS
# ============================================================

test("Articulation: staccato halves duration",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @art:staccato",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] < 500])

test("Articulation: accent adds velocity",
    "@bpm 120\nplay note(C4) @dur:q @vel:80 @art:accent",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["velocity"] >= 90])

test("Articulation: tenuto keeps full duration",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @art:tenuto",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] > 400])

test("Articulation: legato keeps full duration",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @art:legato",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] == 500])

# ============================================================
# 4. TUPLETS
# ============================================================

test("Tuplet: t3(C4 E4 G4) triplet",
    "@bpm 120\nt3(C4 E4 G4)",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[1]["midi"] == 64,
     lambda ev, bp: ev[2]["midi"] == 67])

test("Tuplet: tup(3,2,C4,E4,G4) explicit",
    "@bpm 120\ntup(3,2,C4,E4,G4)",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: ev[0]["midi"] == 60])

test("Tuplet: trip(C4 E4 G4) alias",
    "@bpm 120\ntrip(C4 E4 G4)",
    [lambda ev, bp: len(ev) == 3])

test("Tuplet: tuplet notes fit in time of 2 beats",
    "@bpm 120\nt3(C4 E4 G4)",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: ev[2]["timestamp"] < 2000])  # within 2 beats at 120bpm

# ============================================================
# 5. OCTAVE SHIFT
# ============================================================

test("Octave: @oct:+1 directive transposes up",
    "@oct:+1\n@bpm 120\nplay note(C4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["midi"] == 72])  # C4(60) + 12 = 72

test("Octave: @oct:-1 directive transposes down",
    "@oct:-1\n@bpm 120\nplay note(C4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["midi"] == 48])  # C4(60) - 12 = 48

test("Octave: @oct prop on note overrides directive",
    "@oct:+2\n@bpm 120\nplay note(C4) @dur:q @vel:mf @oct:-1",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["midi"] == 48])  # prop overrides directive

# ============================================================
# 6. VELOCITY CURVES
# ============================================================

test("Curve: @curve vel 40 127 global ramp",
    "@bpm 120\n@curve vel 40 127\nT0 N60 D100 V80\nT100 N62 D100 V80\nT200 N64 D100 V80\nT300 N65 D100 V80",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["velocity"] <= 45,
     lambda ev, bp: ev[3]["velocity"] >= 100])

test("Curve: @curve vel 127 40 descending",
    "@bpm 120\n@curve vel 127 40\nT0 N60 D100 V80\nT100 N62 D100 V80\nT200 N64 D100 V80\nT300 N65 D100 V80",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: ev[0]["velocity"] >= 100,
     lambda ev, bp: ev[3]["velocity"] <= 45])

test("Curve: different velocities across events",
    "@bpm 120\n@curve vel 40 127\nT0 N60 D100 V80\nT100 N62 D100 V80\nT200 N64 D100 V80\nT300 N65 D100 V80",
    [lambda ev, bp: len(ev) == 4,
     lambda ev, bp: len(set(e["velocity"] for e in ev)) > 1])

# ============================================================
# 7. TIES
# ============================================================

test("Tie: @tie prop merges same-pitch events",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @tie\nplay note(C4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[0]["duration"] > 500])

test("Tie: @tie does not merge different pitches",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @tie\nplay note(E4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 2])  # different pitches, no merge

test("Tie: three tied notes merge to one",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @tie\nplay note(C4) @dur:q @vel:mf @tie\nplay note(C4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] > 1000])

test("Tie: only same-pitch ties merge",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @tie\nplay note(D4) @dur:q @vel:mf @tie\nplay note(C4) @dur:q @vel:mf",
    [lambda ev, bp: len(ev) == 3])

test("Tie: C4~ q q tilde shorthand merges",
    "@bpm 120\nC4~ q q",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["midi"] == 60,
     lambda ev, bp: ev[0]["duration"] == 1000])

test("Tie: tilde shorthand with three tied notes",
    "@bpm 120\nC4~ q q q",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] == 1500])

# ============================================================
# 8. COMBINED
# ============================================================

test("Combined: pedal + rest + articulation",
    "@bpm 120\npedal on\nplay note(C4) @dur:q @vel:mf @art:staccato\nrest q\nplay note(E4) @dur:q @vel:mf @art:accent\npedal off",
    [lambda ev, bp: len(ev) >= 4,
     lambda ev, bp: any(e.get("sustain") == 127 for e in ev),
     lambda ev, bp: any(e.get("sustain") == 0 for e in ev)])

test("Combined: octave + curve + pedal",
    "@bpm 120\n@oct:+1\n@curve vel 60 120\npedal on\nT0 N60 D100 V80\nT100 N64 D100 V80\nT200 N67 D100 V80\npedal off",
    [lambda ev, bp: len(ev) >= 5,
     lambda ev, bp: any(e.get("sustain") == 127 for e in ev),
     lambda ev, bp: all(e["midi"] >= 72 for e in ev if e.get("midi", 0) > 0)])  # C4+oct = C5(72)

test("Combined: tuplet + rest + tie",
    "@bpm 120\nplay note(C4) @dur:q @vel:mf @tie\nplay note(C4) @dur:q @vel:mf\nrest e\nt3(E4 G4 C5)\nplay note(C5) @dur:q @vel:mf @art:accent",
    [lambda ev, bp: len(ev) == 5,  # 1 tied pair merged + 3 tuplet + 1 accent note
     lambda ev, bp: any(e["midi"] == 60 for e in ev),
     lambda ev, bp: any(e["velocity"] >= 90 for e in ev)])

test("Machine: S[art:staccato] halves duration",
    "@bpm 120\nT0 N60 D500 V80 S[art:staccato]",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["duration"] < 400])

test("Machine: S[art:accent] boosts velocity",
    "@bpm 120\nT0 N60 D500 V80 S[art:accent]",
    [lambda ev, bp: len(ev) == 1,
     lambda ev, bp: ev[0]["velocity"] == 92])

test("Machine: sustain events excluded from note count",
    "@bpm 120\npedal on\nT0 N60 D500 V80\npedal off",
    [lambda ev, bp: len(ev) == 3,
     lambda ev, bp: len([e for e in ev if e.get("sustain") is not None]) == 2])

# ============================================================
# SUMMARY
# ============================================================

print(f"\n{'='*50}")
print(f"PIANO FEATURES TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL PIANO FEATURE TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    for name, status, detail in results:
        if status == "FAIL":
            print(f"  {name}: {detail}")
    sys.exit(1)
