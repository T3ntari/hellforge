"""Tensorsharp v1.0.0 — NVIDIA Tensor Core acceleration for E math.
Depends on Radical for GPU compute runtime.
Registers math evaluator at priority 3 (above Radical's 5).
Uses CuPy for Tensor Core matmul (TF32/FP16 mixed precision).
Graceful fallback: Tensorsharp -> Radical -> LURE -> Python.

Install: pip install cupy-cuda12x  (requires CUDA toolkit + NVIDIA GPU)"""

VERSION = "1.0.0"
author = "Tentari"
description = "NVIDIA Tensor Core acceleration — mixed-precision matrix math"

_engine = None


def register(api):
    api.add_boot_step(f"Tensorsharp v{VERSION}", "loading")
    global _engine

    # Check if Radical is available (config flag set by Radical's own
    # register — robust against plugin scan order)
    radical_ok = bool(api.get_config("radical_available"))
    if not radical_ok:
        try:
            from plugins.radical import get_engine as get_radical
            radical = get_radical()
            radical_ok = bool(radical and radical.available)
        except Exception:
            radical_ok = False

    if not radical_ok:
        api.set_config("tensorsharp_available", False)
        api.add_boot_step("Tensorsharp: requires Radical (GPU shader core)", "skip")
        api.add_command("tensorsharp", _cmd, "Tensorsharp: tensorsharp status|info")
        return

    # Try to initialize CUDA/Tensor Core engine
    try:
        from .cuda_backend import TensorSHARPEngine
        eng = TensorSHARPEngine()
        if eng.available:
            _engine = eng
            api.set_config("tensorsharp_available", True)

            # Register math evaluator at priority 3 (highest)
            def _ts_eval(ast_dict, variables):
                return _engine.eval_ast(ast_dict, variables)
            api.register_math_evaluator("TensorSHARP", _ts_eval, priority=3)

            api.add_command("tensorsharp", _cmd,
                "TensorSHARP: tensorsharp status|benchmark|cores|info")

            tc = eng.tensor_cores
            api.add_boot_step(
                f"Tensorsharp: Tensor Cores active ({tc.get('count', '?')} cores, {tc.get('precision', 'FP32')})",
                "done"
            )
        else:
            api.set_config("tensorsharp_available", False)
            api.add_boot_step(f"Tensorsharp: unavailable ({eng.diagnostic})", "skip")
            api.add_command("tensorsharp", _cmd, "TensorSHARP: tensorsharp status|info")
    except Exception as e:
        api.set_config("tensorsharp_available", False)
        api.add_boot_step(f"Tensorsharp: init failed ({e})", "skip")
        api.add_command("tensorsharp", _cmd, "TensorSHARP: tensorsharp status|info")

    api.add_help_section("TensorSHARP (CUDA tensor cores)", [
        "tensorsharp status       Tensor-core + CUDA status",
        "tensorsharp benchmark    matmul GFLOPS benchmark",
        "tensorsharp cores        Tensor core capabilities",
        "tensorsharp info         Engine + evaluator info",
        "",
        "Tensor-core matmul accelerator + math AST evaluator (priority 3",
        "in the evaluator chain). The Ninja game menu reports its TFLOPS",
        "line when CUDA matmul is online.",
    ])


def get_engine():
    return _engine


def _cmd(args):
    if not args or args[0] == "status":
        if _engine and _engine.available:
            tc = _engine.tensor_cores
            print(f"  TensorSHARP v{VERSION}")
            print(f"  CUDA available: {_engine.cuda_available}")
            print(f"  Tensor Cores: {tc.get('count', 'N/A')}")
            print(f"  Precision: {tc.get('precision', 'N/A')}")
            print(f"  GPU: {tc.get('gpu_name', 'Unknown')}")
            print(f"  CuPy version: {tc.get('cupy_version', 'N/A')}")
            s = _engine.stats()
            print(f"  Ops executed: {s.get('op_count', 0)}")
            print(f"  Total GFLOPS: {s.get('total_gflops', 0):.1f}")
            print(f"  Evaluations: {s.get('eval_count', 0)}")
        else:
            print(f"  TensorSHARP v{VERSION}")
            print(f"  Status: inactive")
            diag = _engine.diagnostic if _engine else "not initialized"
            print(f"  Reason: {diag}")
            try:
                import cupy  # noqa
                print(f"  CuPy: installed")
            except ImportError:
                print(f"  CuPy: not installed (pip install cupy-cuda12x)")

    elif args[0] == "cores":
        if _engine and _engine.available:
            tc = _engine.tensor_cores
            print(f"  Tensor Core Configuration:")
            print(f"    GPU: {tc.get('gpu_name', 'Unknown')}")
            print(f"    Compute Capability: {tc.get('compute_cap', 'N/A')}")
            print(f"    Tensor Cores: {tc.get('count', 'N/A')}")
            print(f"    Max Precision: {tc.get('precision', 'N/A')}")
            print(f"    FP16: {'yes' if tc.get('has_fp16') else 'no'}")
            print(f"    TF32: {'yes' if tc.get('has_tf32') else 'no'}")
            print(f"    INT8: {'yes' if tc.get('has_int8') else 'no'}")
        else:
            print(f"  TensorSHARP inactive — no Tensor Core info")

    elif args[0] == "benchmark":
        _run_benchmark()

    elif args[0] == "info":
        print(f"  TensorSHARP v{VERSION} — Tensor Core Math Accelerator")
        print(f"  Registers math evaluator at priority 3 (highest)")
        print(f"  Depends on: Radical (GPU shader core)")
        print(f"  Uses: CuPy + CUDA Tensor Cores for mixed-precision matmul")
        print(f"  Falls back: TensorSHARP -> Radical -> LURE -> Python")
        if _engine and _engine.available:
            print(f"  Tensor Cores: available")
        else:
            print(f"  Tensor Cores: unavailable — using Radical/LURE/Python fallback")

    else:
        print(f"  Usage: tensorsharp status|benchmark|cores|info")


def _run_benchmark():
    import time
    print(f"  TensorSHARP Benchmark:")
    print(f"  {'Operation':<30} {'TensorSHARP':>12} {'Radical':>10} {'Speedup':>8}")
    print(f"  " + "-" * 62)

    # Matrix multiply benchmarks
    sizes = [(64, 64), (128, 128), (256, 256), (512, 512)]
    for M, N in sizes:
        label = f"matmul {M}x{N}"
        import numpy as np
        A = np.random.rand(M, N).astype(np.float32)
        B = np.random.rand(N, M).astype(np.float32)

        # TensorSHARP (GPU)
        t_ts = float("inf")
        if _engine and _engine.available:
            try:
                t0 = time.time()
                for _ in range(10):
                    _engine.matmul(A, B)
                t_ts = (time.time() - t0) / 10 * 1000
            except Exception:
                pass

        # Radical (shader cores)
        t_rad = float("inf")
        try:
            from plugins.radical.matrix_ops import matmul
            t0 = time.time()
            for _ in range(10):
                matmul(A, B)
            t_rad = (time.time() - t0) / 10 * 1000
        except Exception:
            pass

        ts_s = f"{t_ts:.2f}ms" if t_ts < float("inf") else "N/A"
        rad_s = f"{t_rad:.2f}ms" if t_rad < float("inf") else "N/A"
        speedup = t_rad / t_ts if (t_ts < float("inf") and t_rad < float("inf")) else 0
        spd = f"{speedup:.1f}x" if speedup else "N/A"
        print(f"  {label:<30} {ts_s:>12} {rad_s:>10} {spd:>8}")
