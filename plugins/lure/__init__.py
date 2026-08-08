"""LURE — Lua Runtime Accelerator for E.
Accelerates the compilation hot path using LuaJIT.
Async engine provides non-blocking compile via per-thread LuaRuntimes.

Python manages: state, cursor, project resolution, error handling.
LURE manages: fast string parsing, bulk event math.

Requires: pip install lupa  (bundles LuaJIT 5.3+)
Gracefully falls back to Python if unavailable."""

VERSION = "3.0.0"
author = "Tentari"
description = "Lua Runtime Accelerator for E — LuaJIT-powered hot-path parsing + async compile"

# Initialize engines at import time
try:
    from .lua_engine import LUREngine
    _engine = LUREngine()
except Exception:
    _engine = None

_async_engine = None


def register(api):
    api.add_boot_step(f"LURE v{VERSION}", "loading")

    # Register sync evaluators
    if _engine and _engine.available:
        api.set_config("lure_available", True)
        api.add_command("lure", _cmd, "LURE: lure status|benchmark|async")

        # Register LuaJIT math evaluator (priority 10 — highest)
        def _lure_eval(ast_dict, variables):
            return _engine.eval_ast(ast_dict, variables)
        api.register_math_evaluator("LURE", _lure_eval, priority=10)

        api.add_boot_step("LURE: LuaJIT accelerator + math active", "done")
    else:
        diag = _engine._diagnostic if _engine else "not initialized"
        api.add_boot_step(f"LURE: not available ({diag})", "skip")

    # Always register Python fallback evaluator (priority 100 — lowest)
    def _py_eval(ast_dict, variables):
        from .math_python import eval_python
        return eval_python(ast_dict, variables)
    api.register_math_evaluator("Python", _py_eval, priority=100)

    # Register async engine
    _async = get_async_engine()
    if _async and _async.available:
        api.set_config("lure_async_available", True)
        api.add_boot_step(f"LURE: async engine active ({_async._max_workers} workers)", "done")
    else:
        diag = _async._diagnostic if _async else "not available"
        api.set_config("lure_async_available", False)
        api.add_boot_step(f"LURE: async engine not available ({diag})", "skip")


def get_engine():
    """Return the LUREngine singleton."""
    return _engine


def get_async_engine():
    """Return the AsyncLUREngine singleton (creates on first call)."""
    global _async_engine
    if _async_engine is None:
        try:
            from .async_engine import AsyncLUREngine
            _async_engine = AsyncLUREngine()
        except Exception:
            _async_engine = None
    return _async_engine


def parse_line(line):
    """Accelerated line parser. Returns event dict or None.
    For single-line use (not batch)."""
    if _engine and _engine.available:
        try:
            return _engine.parse_line(line)
        except Exception:
            pass
    return None


def parse_lines_batch(lines):
    """Accelerated batch line parser. Returns list of event or None."""
    if _engine and _engine.available and len(lines) > 10:
        try:
            return _engine.parse_lines_batch(lines)
        except Exception:
            pass
    return None


def quantize(events, scale_name):
    """Accelerated scale quantization."""
    if _engine and _engine.available and len(events) > 50:
        try:
            return _engine.quantize(events, scale_name)
        except Exception:
            pass
    return None


def _cmd(args):
    """LURE status and benchmark command."""
    if not args or args[0] == "status":
        print(f"  LURE v{VERSION}")
        if _engine and _engine.available:
            s = _engine.summary()
            print(f"  Sync engine: active")
            print(f"  Lines parsed: {s.get('parse_count', 0)}")
            print(f"  Events processed: {s.get('event_count', 0)}")
        else:
            print(f"  Sync engine: inactive (pip install lupa)")
        _async = get_async_engine()
        if _async and _async.available:
            s = _async.summary()
            print(f"  Async engine: active ({s.get('max_workers', '?')} workers)")
        else:
            print(f"  Async engine: inactive")
    elif args[0] == "benchmark":
        _run_benchmark()
    elif args[0] == "async":
        _run_async_benchmark()
    else:
        print("  Usage: lure status|benchmark|async")


def _run_benchmark():
    """Compare Python vs LURE parse speed (batch mode)."""
    import time
    from ep_compiler.mode_v1_machine import parse_machine_line

    if not _engine or not _engine.available:
        print("  LURE not available")
        return

    lines = [f"T{i*100} N{60+(i%12)} D500 V0.8" for i in range(10000)]

    t0 = time.time()
    for l in lines:
        parse_machine_line(l, {})
    t_py = time.time() - t0

    t0 = time.time()
    _engine.parse_lines_batch(lines)
    t_lure = time.time() - t0

    ratio = t_py / t_lure if t_lure > 0 else 1
    speed_label = "faster" if ratio > 1 else "slower"
    print(f"  Python: {t_py*1000:.1f}ms")
    print(f"  LURE:   {t_lure*1000:.1f}ms")
    print(f"  LURE is {ratio:.1f}x {speed_label} than Python")

    # Mixed syntax benchmark (where LURE really shines)
    mixed = []
    for i in range(2000):
        if i % 3 == 0:
            mixed.append(f"T{i*100} N{60+(i%12)} D500 V0.8")
        elif i % 3 == 1:
            mixed.append(f"play note(C4) @dur:q @vel:mf")
        else:
            mixed.append(f"T{i*100} N{60+(i%12)}")
    t0 = time.time()
    for l in mixed:
        parse_machine_line(l, {})
    t_py_mix = time.time() - t0
    t0 = time.time()
    _engine.parse_lines_batch(mixed)
    t_lure_mix = time.time() - t0
    ratio_mix = t_py_mix / t_lure_mix if t_lure_mix > 0 else 1
    print(f"  Mixed syntax - Python: {t_py_mix*1000:.1f}ms  LURE: {t_lure_mix*1000:.1f}ms  ({ratio_mix:.1f}x)")
    # Also run the actual compile benchmark
    from ep_compiler.compile import compile_source
    import time as _time
    test_text = "@bpm 120\n" + "\n".join(mixed)
    t0 = _time.time()
    compile_source(test_text)
    t_full = _time.time() - t0
    print(f"  Full compile pipeline: {t_full*1000:.1f}ms")


def _run_async_benchmark():
    """Benchmark async compilation vs synchronous."""
    import asyncio
    import time as _time

    print(f"  Async Benchmark (LURE async vs sync):")

    # Build test sources
    sources = []
    for batch in range(5):
        lines = [f"T{j*100} N{60+(j%12)} D500 V0.8" for j in range(2000)]
        src = "@bpm 120\n" + "\n".join(lines)
        sources.append(src)

    # Synchronous benchmark
    from ep_compiler.compile import compile_source
    t0 = _time.time()
    for src in sources:
        compile_source(src)
    t_sync = _time.time() - t0
    print(f"  Synchronous (5 x 2000 lines): {t_sync*1000:.1f}ms")

    # Async benchmark
    from ep_compiler.async_compile import async_compile_batch
    t0 = _time.time()
    asyncio.run(async_compile_batch(sources))
    t_async = _time.time() - t0
    ratio = t_sync / t_async if t_async > 0 else 1
    label = "faster" if ratio > 1 else "slower"
    print(f"  Async batch (5 x 2000 lines): {t_async*1000:.1f}ms")
    print(f"  Async is {ratio:.1f}x {label} than synchronous")
