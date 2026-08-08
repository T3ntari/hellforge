#!/usr/bin/env python3
"""Exhaustive async compilation tests — parallelism, fallback chain, edge cases."""
import sys
import os
import time
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


# === ASYNC COMPILE BASICS ===

# === ASYNC COMPILE BASICS ===

async def _do_basic():
    from ep_compiler.async_compile import async_compile_source
    ev, bp = await async_compile_source("@bpm 120\nT0 N60 D500 V100\nT500 N64 D500 V80")
    assert len(ev) == 2, f"expected 2 events got {len(ev)}"
    assert ev[0]["midi"] == 60
    assert ev[1]["midi"] == 64
test("Async compile: basic v1 machine", lambda: asyncio.run(_do_basic()))


async def _do_math():
    from ep_compiler.async_compile import async_compile_source
    ev, bp = await async_compile_source("$bpm = 120\nT0 N{$bpm / 2} D100")
    assert len(ev) == 1
    assert ev[0]["midi"] == 60
test("Async compile: math expressions", lambda: asyncio.run(_do_math()))


async def _do_for():
    from ep_compiler.async_compile import async_compile_source
    ev, bp = await async_compile_source("for $i = 0 to 99 {\nT{$i * 10} N{60 + $i % 12} D50\n}")
    assert len(ev) == 100, f"expected 100 events got {len(ev)}"
test("Async compile: for loop (100 events)", lambda: asyncio.run(_do_for()))


async def _do_while():
    from ep_compiler.async_compile import async_compile_source
    ev, bp = await async_compile_source("$i = 0\nwhile $i < 50 {\nT{$i * 20} N{60} D40\n$i = $i + 1\n}")
    assert len(ev) == 50, f"expected 50 events got {len(ev)}"
test("Async compile: while loop (50 events)", lambda: asyncio.run(_do_while()))


# === PARALLEL BATCH COMPILE ===

async def _do_batch10():
    from ep_compiler.async_compile import async_compile_batch
    sources = [
        f"for $i = 0 to 99 {{\nT{{$i * 10}} N{{{60 + j % 12}}} D50\n}}"
        for j in range(10)
    ]
    results = await async_compile_batch(sources)
    assert len(results) == 10, f"expected 10 results got {len(results)}"
    for ev, bp in results:
        assert len(ev) == 100, f"expected 100 events per source got {len(ev)}"
test("Async batch: 10 sources x 100 events each", lambda: asyncio.run(_do_batch10()))


async def _do_batch_mixed():
    from ep_compiler.async_compile import async_compile_batch
    sources = [
        "T0 N60 D500 V100",
        "play note(C4) @dur:q @vel:mf",
        "for $i = 0 to 7 {\nT{$i * 100} N{60 + $i} D80\n}",
        "$bpm = 140\n$beat = 60000 / $bpm\nT{$beat * 0} N60 D{$beat / 4}",
        "repeat 3 {\nT0 N60 D200\n}",
    ]
    results = await async_compile_batch(sources)
    assert len(results) == 5
    assert len(results[0][0]) == 1  # T0 N60
    assert len(results[2][0]) == 8  # for loop
    assert len(results[4][0]) == 3  # repeat
test("Async batch: mixed syntax types", lambda: asyncio.run(_do_batch_mixed()))


# === ASYNC MATH EVALUATION ===

async def _do_math_eval():
    from ep_compiler.async_compile import async_eval_math
    val, err = await async_eval_math("2 + 2")
    assert val == 4, f"expected 4 got {val}"
    val, err = await async_eval_math("sin(0)")
    assert val == 0, f"expected 0 got {val}"
    val, err = await async_eval_math("round(3.7)")
    assert val == 4, f"expected 4 got {val}"
test("Async math: basic expressions", lambda: asyncio.run(_do_math_eval()))


async def _do_math_vars():
    from ep_compiler.async_compile import async_eval_math
    val, err = await async_eval_math("$x + $y", {"x": 10, "y": 20})
    assert val == 30, f"expected 30 got {val}"
    val, err = await async_eval_math("$base * 2", {"base": 60})
    assert val == 120, f"expected 120 got {val}"
test("Async math: variable resolution", lambda: asyncio.run(_do_math_vars()))


async def _do_math_complex():
    from ep_compiler.async_compile import async_eval_math
    val, err = await async_eval_math("quadratic(1, -5, 6)")
    assert val is not None, "quadratic returned None"
    val, err = await async_eval_math("floor(3.9) + round(sqrt(9))")
    assert val == 6, f"expected 6 got {val}"
    val, err = await async_eval_math("min(10, 20) + max(5, 15)")
    assert val == 25, f"expected 25 got {val}"
test("Async math: complex functions (quadratic, floor, sqrt, min, max)", lambda: asyncio.run(_do_math_complex()))


# === ASYNC MATH BATCH ===

async def _do_math_batch():
    from ep_compiler.async_compile import async_eval_math_batch
    exprs = ["2 + 2", "3 * 4", "10 - 5", "20 / 4", "2 ^ 10"]
    results = await async_eval_math_batch(exprs)
    expected = [4, 12, 5, 5, 1024]
    for i, (val, err) in enumerate(results):
        assert val == expected[i], f"expr {i} '{exprs[i]}': expected {expected[i]} got {val}"
test("Async math batch: 5 expressions parallel", lambda: asyncio.run(_do_math_batch()))


# === STRESS / LIMIT TESTS ===

async def _do_stress_10k():
    from ep_compiler.async_compile import async_compile_source
    src = "for $i = 0 to 9999 {\nT{$i * 10} N{60 + $i % 12} D5\n}"
    ev, bp = await async_compile_source(src)
    assert len(ev) == 10000, f"expected 10000 events got {len(ev)}"
test("Async stress: 10000 events from for loop", lambda: asyncio.run(_do_stress_10k()))


async def _do_stress_50k_while():
    from ep_compiler.async_compile import async_compile_source
    src = "$i = 0\nwhile $i < 10000 {\nT{$i * 10} N{60} D5\n$i = $i + 1\n}"
    ev, bp = await async_compile_source(src)
    assert len(ev) == 10000, f"expected 10000 events got {len(ev)}"
test("Async stress: 10000 events from while loop", lambda: asyncio.run(_do_stress_50k_while()))


async def _do_50_parallel():
    from ep_compiler.async_compile import async_compile_batch
    sources = [
        "for $i = 0 to 199 {\nT{$i * 20} N{60 + $i % 12} D40\n}"
        for _ in range(50)
    ]
    # Delay-compensated: start all tasks nearly simultaneously
    t0 = time.time()
    results = await async_compile_batch(sources)
    t = time.time() - t0
    assert len(results) == 50
    for ev, bp in results:
        assert len(ev) == 200
    print(f"   50 x 200 events = 10000 total in {t*1000:.0f}ms ({t*1000/50:.1f}ms/source)")
test("Async stress: 50 sources x 200 events (10000 total, parallel)", lambda: asyncio.run(_do_50_parallel()))


async def _do_100_math_parallel():
    from ep_compiler.async_compile import async_eval_math_batch
    exprs = [f"sin({i * 0.1}) + cos({i * 0.05})" for i in range(100)]
    results = await async_eval_math_batch(exprs)
    assert len(results) == 100
    for val, err in results:
        assert val is not None, f"batch eval failed: {err}"
test("Async stress: 100 parallel math evaluations", lambda: asyncio.run(_do_100_math_parallel()))


async def _do_big_nested():
    from ep_compiler.async_compile import async_compile_source
    src = (
        "for $i = 0 to 3 {\n"
        "  for $j = 0 to 3 {\n"
        "    T{($i * 4 + $j) * 50} N{60 + $i * 4 + $j} D40\n"
        "  }\n"
        "}\n"
    )
    ev, bp = await async_compile_source(src)
    assert len(ev) == 16, f"expected 16 events got {len(ev)}"
    for i in range(16):
        assert ev[i]["midi"] == 60 + i, f"event {i}: expected MIDI {60+i} got {ev[i]['midi']}"
test("Async stress: nested for loops (4x4=16 events)", lambda: asyncio.run(_do_big_nested()))


# === ENGINE STATUS ===

def test_async_engine_status():
    from ep_compiler.async_compile import get_async_engines
    status = get_async_engines()
    assert "lure_async" in status
    assert "python_async" in status
    la = status["lure_async"]
    pa = status["python_async"]
    print(f"   LURE async: {'available' if la['available'] else 'unavailable'}")
    print(f"   Python async: {'available' if pa['available'] else 'unavailable'}")
    print(f"   LURE diag: {la.get('diagnostic', 'N/A')}")
test("Async engine: status check", test_async_engine_status)


async def _do_pool():
    from ep_compiler.async_compile import AsyncCompilePool
    pool = AsyncCompilePool(max_workers=4)
    ev, bp = await pool.compile_text("@bpm 120\nT0 N60 D500")
    assert len(ev) == 1
    assert ev[0]["midi"] == 60
    pool.shutdown()
test("Async pool: compile text via pool", lambda: asyncio.run(_do_pool()))


# === FALLBACK CHAIN ===

async def _do_fallback():
    from ep_compiler.async_compile import async_compile_source
    ev, bp = await async_compile_source("@bpm 120\nT0 N60 D500")
    assert len(ev) >= 1
test("Async fallback: compile works regardless of LURE status", lambda: asyncio.run(_do_fallback()))


async def _do_200_evals():
    from ep_compiler.async_compile import async_eval_math_batch
    exprs = [f"{i} + {i * 2}" for i in range(200)]
    results = await async_eval_math_batch(exprs)
    assert len(results) == 200
    for i, (val, err) in enumerate(results):
        assert val == i + i * 2, f"expr {i}: expected {i + i*2} got {val}"
test("Async eval batch: 200 expressions", lambda: asyncio.run(_do_200_evals()))


# === SUMMARY ===

print(f"\n{'='*50}")
print(f"ASYNC TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL ASYNC TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
