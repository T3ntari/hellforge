#!/usr/bin/env python3
"""HELLFORGE Humanize plugin tests — MoE model, directive, pipeline."""
import sys
import os
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import ep_core
ep_core.load_plugins()

from plugins.humanize import moe
from plugins.humanize.humanizer import apply_humanize
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


def _grid(n=30, base_vel=80):
    return [{"timestamp": i * 100, "midi": 60 + (i % 12), "duration": 80,
             "velocity": base_vel + (i % 5), "pan": 0.0, "bend": 0,
             "channel": None} for i in range(n)]


# === Model ===

def test_model_size():
    p = moe.init_params()
    n = moe.param_count(p)
    assert 40000 <= n <= 55000, f"expected ~50k params, got {n}"
test("Model: ~50k params", test_model_size)


def test_model_predicts():
    p, _ = moe.load_or_train()
    import numpy as np
    x = np.random.default_rng(1).uniform(0, 1, (64, 6)).astype(np.float32)
    out = moe.predict(x, p)
    assert out.shape == (64, 2)
    assert out[:, 0].min() >= -30 and out[:, 0].max() <= 30
test("Model: predicts offset + velocity delta", test_model_predicts)


def test_model_deterministic():
    import numpy as np
    p, _ = moe.load_or_train()
    x = np.random.default_rng(2).uniform(0, 1, (32, 6)).astype(np.float32)
    a = moe.predict(x, p)
    b = moe.predict(x, p)
    assert (a == b).all()
test("Model: deterministic inference", test_model_deterministic)


def test_inference_fast():
    p, _ = moe.load_or_train()
    t0 = time.time()
    apply_humanize(_grid(2000), bpm=120, strength=30, params=p)
    dt = (time.time() - t0) * 1000
    assert dt < 1000, f"inference too slow: {dt:.0f}ms for 2000 notes"
test("Model: instant CPU inference (<1s for 2000 notes)", test_inference_fast)


def test_strength_zero_unchanged():
    p, _ = moe.load_or_train()
    ev = _grid(12)
    out = apply_humanize(ev, bpm=120, strength=0, params=p)
    assert out == ev
test("Apply: strength 0 leaves events untouched", test_strength_zero_unchanged)


def test_apply_changes_events():
    p, _ = moe.load_or_train()
    ev = _grid(40)
    out = apply_humanize(ev, bpm=120, strength=80, params=p)
    ts_diff = [o["timestamp"] - e["timestamp"] for o, e in zip(out, ev)]
    vel_diff = [o["velocity"] - e["velocity"] for o, e in zip(out, ev)]
    assert any(d != 0 for d in ts_diff) or any(d != 0 for d in vel_diff)
    assert len(out) == len(ev)
test("Apply: strong humanization changes timing/dynamics", test_apply_changes_events)


# === Directive pipeline ===

def test_directive_applies():
    src = "@humanize:60\n" + "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(30))
    ev, _ = compile_source(src)
    src0 = "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(30))
    ev0, _ = compile_source(src0)
    assert len(ev) == len(ev0)
    diffs = [ev[i]["timestamp"] - ev0[i]["timestamp"] for i in range(len(ev))]
    assert sum(1 for d in diffs if d) >= 5, "expected most notes shifted"
test("Directive: @humanize:60 shifts compiled events", test_directive_applies)


def test_directive_off():
    src = "@humanize off\n" + "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(10))
    ev, _ = compile_source(src)
    src0 = "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(10))
    ev0, _ = compile_source(src0)
    assert [e["timestamp"] for e in ev] == [e["timestamp"] for e in ev0]
test("Directive: @humanize off disables", test_directive_off)


def test_directive_no_directive_unchanged():
    src = "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(10))
    ev, _ = compile_source(src)
    assert [e["timestamp"] for e in ev] == [i * 100 for i in range(10)]
test("Directive: no @humanize -> grid intact", test_directive_no_directive_unchanged)


def test_comment_mentions_dont_override():
    src = ("/* @humanize:15 subtle (default) */\n"
           "@humanize:70\n" + "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(20)))
    ev, _ = compile_source(src)
    src0 = "".join(f"T{i*100} N{60+i%12} D500 V{80+i%5}\n" for i in range(20))
    ev0, _ = compile_source(src0)
    diffs = [ev[i]["timestamp"] - ev0[i]["timestamp"] for i in range(len(ev))]
    assert sum(1 for d in diffs if d) >= 5, "comment mention must not block the real directive"
test("Directive: last @humanize wins over doc mentions", test_comment_mentions_dont_override)


def test_sample_compiles():
    p = os.path.join(ROOT, "samples", "v4-current", "humanize", "humanize_demo.e")
    with open(p, encoding="utf-8", errors="replace") as f:
        t = f.read()
    ev, bp = compile_source(t)
    assert len(ev) >= 8, f"sample should compile to events, got {len(ev)}"
test("Sample: humanize_demo.e compiles + humanizes", test_sample_compiles)


print(f"\n{'='*50}")
print(f"HUMANIZE TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL HUMANIZE TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
