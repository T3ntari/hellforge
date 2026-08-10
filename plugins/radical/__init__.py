"""Radical v1.0.0 — GPU Shader Math Core.
Compiles E math ASTs into GLSL compute shaders and executes them on GPU shader cores.
Registered as math evaluator at priority 5 (above LURE's 10).
Supports multi-GPU switching, VRAM limits, and compute shader pipeline.

Install: pip install PyOpenGL glfw  (optional — graceful fallback if missing)"""

VERSION = "1.0.0"
author = "Tentari"
description = "GPU Shader Math Core — GLSL compute shader evaluation, multi-GPU, VRAM control"

_engine = None

# ── Config (GPU selection, VRAM limit) ──
_CONFIG = {"selected_gpu": 0, "max_vram_mb": 0}  # 0 = auto, >0 = MB limit


def _save_config():
    try:
        import json
        import os
        from ep_core import IDENTITY_DIR
        p = os.path.join(str(IDENTITY_DIR), ".radical_config.json")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump(_CONFIG, f)
    except Exception:
        pass


def _load_config():
    global _CONFIG
    try:
        import json
        import os
        from ep_core import IDENTITY_DIR
        p = os.path.join(str(IDENTITY_DIR), ".radical_config.json")
        if os.path.exists(p):
            with open(p) as f:
                _CONFIG.update(json.load(f))
    except Exception:
        pass


def register(api):
    api.add_boot_step(f"Radical v{VERSION}", "loading")
    global _engine
    _load_config()

    try:
        from .gpu_detect import detect_gpu
        gpu_info = detect_gpu()
    except Exception:
        gpu_info = {"available": False, "reason": "gpu_detect failed"}

    # Apply user-selected GPU if configured
    selected_idx = _CONFIG.get("selected_gpu", 0)
    max_vram = _CONFIG.get("max_vram_mb", 0)
    if selected_idx > 0 and gpu_info.get("gpus") and selected_idx < len(gpu_info["gpus"]):
        gpu_info["primary"] = selected_idx
        sel = gpu_info["gpus"][selected_idx]
        gpu_info["name"] = sel["name"]
        gpu_info["vendor"] = sel["vendor"]
        gpu_info["vram_mb"] = sel.get("vram_mb", 0)

    if gpu_info.get("available"):
        try:
            from .compute_runtime import RadicalEngine
            eng = RadicalEngine(gpu_info, max_vram_mb=max_vram)
            if eng.available:
                _engine = eng
                api.set_config("radical_available", True)

                def _radical_eval(ast_dict, variables):
                    return _engine.eval_ast(ast_dict, variables)
                api.register_math_evaluator("Radical", _radical_eval, priority=5)

                api.add_command("radical", _cmd, "Radical: radical status|benchmark|shaders|gpu|vram|info")
                gpu_name = gpu_info.get("name", "Unknown GPU")
                sel_str = f" [GPU {selected_idx}]" if selected_idx else ""
                vram_str = f" VRAM limit {max_vram}MB" if max_vram else ""
                api.add_boot_step(f"Radical: GPU active ({gpu_name}{sel_str}{vram_str})", "done")
            else:
                api.set_config("radical_available", False)
                api.add_command("radical", _cmd, "Radical: radical status|benchmark|shaders|gpu|vram|info")
                api.add_boot_step(f"Radical: engine init failed ({eng.diagnostic})", "skip")
        except Exception as e:
            api.set_config("radical_available", False)
            api.add_command("radical", _cmd, "Radical: radical status|benchmark|shaders|gpu|vram|info")
            api.add_boot_step(f"Radical: init error ({e})", "skip")
    else:
        reason = gpu_info.get("reason", "no GPU detected")
        api.set_config("radical_available", False)
        api.add_boot_step(f"Radical: unavailable ({reason})", "skip")
        api.add_command("radical", _cmd, "Radical: radical status|info")

    api.add_help_section("Radical (GPU math)", [
        "radical status                  GPU + engine status",
        "radical benchmark               Run GPU shader benchmark",
        "radical shaders                 Shader cache stats",
        "radical gpu <idx|list>          Select / list GPUs",
        "radical vram                    VRAM usage",
        "radical info                    Engine + evaluator info",
        "",
        "Radical is the GPU math core: compiles E math ASTs to GLSL",
        "compute shaders, evaluates them on the GPU, and accelerates",
        "matrix ops via RadicalEngine. Also feeds the math evaluator",
        "chain used by every plugin (tensorsharp -> radical -> lure).",
    ])

    try:
        from .shader_cache import get_cache_stats
        stats = get_cache_stats()
        if stats["count"] > 0:
            api.add_boot_step(f"Radical: {stats['count']} shaders cached", "done")
    except Exception:
        pass


def get_engine():
    return _engine


def _cmd(args):
    if not args or args[0] == "status":
        from .gpu_detect import detect_gpu
        gi = detect_gpu()
        print(f"  Radical v{VERSION}")
        print(f"  Primary GPU: {gi.get('name', 'Unknown')} ({gi.get('vendor', '?')})")
        print(f"  GPU type: {gi.get('gpu_type', 'unknown')}")
        print(f"  VRAM: {gi.get('vram_mb', 0)} MB")
        print(f"  OpenGL: {gi.get('gl_version', 'N/A')}")
        print(f"  GLSL: {gi.get('glsl_version', 'N/A')}")
        print(f"  Compute shaders: {'yes' if gi.get('compute') else 'no'}")
        if gi.get('compute_max_invocations'):
            print(f"  Max compute invocations: {gi['compute_max_invocations']}")
        if _engine and _engine.available:
            s = _engine.stats()
            print(f"  Shaders compiled: {s.get('compile_count', 0)}")
            print(f"  Expressions evaluated: {s.get('eval_count', 0)}")

        # List ALL GPUs
        if gi.get("gpus"):
            print(f"\n  All GPUs ({len(gi['gpus'])} detected):")
            for idx, g in enumerate(gi["gpus"]):
                marker = ">" if idx == gi.get("primary", 0) else " "
                apis = []
                if gi.get("apis", {}).get("cuda") and g.get("vendor") == "NVIDIA":
                    apis.append("CUDA")
                if gi.get("apis", {}).get("vulkan"):
                    apis.append("Vulkan")
                if gi.get("apis", {}).get("opencl"):
                    apis.append("OpenCL")
                if gi.get("apis", {}).get("directx"):
                    apis.append("DirectX")
                api_str = f" ({', '.join(apis)})" if apis else ""
                vram_s = f" {g.get('vram_mb', 0)}MB" if g.get('vram_mb') else ""
                print(f"    {marker} [{g.get('type', '?')}] {g.get('name', 'Unknown')}{vram_s}{api_str}")

        # API status
        apis = gi.get("apis", {})
        print(f"\n  API support:")
        for api_name in ("opengl", "vulkan", "opencl", "directx", "cuda", "metal"):
            if apis.get(api_name):
                print(f"    {api_name}: available")
        if not any(apis.values()):
            print(f"    (none detected)")

        if not gi.get("available"):
            print(f"\n  Reason: {gi.get('reason', 'unknown')}")

    elif args[0] == "shaders":
        if _engine and _engine.available:
            try:
                from .shader_cache import (
                    get_cache_stats,
                    list_shaders,
                )
                stats = get_cache_stats()
                print(f"  Shader cache: {stats['count']} shaders, {stats['size_kb']}KB")
                for entry in list_shaders()[:10]:
                    print(f"    [{entry['hash'][:12]}] {entry['source_preview'][:60]}")
                if stats['count'] > 10:
                    print(f"    ... and {stats['count'] - 10} more")
            except Exception as e:
                print(f"  Shader cache: {e}")
        else:
            print(f"  Radical inactive — no shaders")

    elif args[0] == "benchmark":
        _run_benchmark()

    elif args[0] == "gpu":
        _cmd_gpu(args[1:])

    elif args[0] == "vram":
        _cmd_vram(args[1:])

    elif args[0] == "info":
        print(f"  Radical v{VERSION} — GPU Shader Math Core")
        print(f"  Registers math evaluator at priority 5")
        print(f"  Compiles E math AST -> GLSL compute shader -> GPU execution")
        print(f"  Falls back: Radical -> LURE -> Python")
        print(f"  Multi-GPU switching: radical gpu <index>")
        print(f"  VRAM limit: radical vram <MB>")
        if _engine and _engine.available:
            print(f"  GPU compute: available")
        else:
            print(f"  GPU compute: unavailable — using CPU fallback")

    else:
        print(f"  Usage: radical status|benchmark|shaders|gpu|vram|info")


def _cmd_gpu(args):
    """Switch active GPU: radical gpu <index> or radical gpu list"""
    from .gpu_detect import detect_gpu
    gi = detect_gpu()
    gpus = gi.get("gpus", [])

    if args and args[0] == "list":
        print(f"  Available GPUs:")
        for idx, g in enumerate(gpus):
            marker = ">" if idx == gi.get("primary", 0) else " "
            print(f"    {marker} [{idx}] {g['name']} ({g['vendor']}, {g.get('type','?')}) {g.get('vram_mb',0)}MB")
        print(f"  Current: GPU {_CONFIG.get('selected_gpu', 0)}")
        return

    if not args:
        print(f"  Current GPU: {_CONFIG.get('selected_gpu', 0)} ({gi.get('name', '?')})")
        print(f"  Switch: radical gpu <index>")
        print(f"  List:   radical gpu list")
        return

    try:
        idx = int(args[0])
    except ValueError:
        print(f"  Invalid GPU index: {args[0]}")
        return

    if idx < 0 or idx >= len(gpus):
        print(f"  GPU index {idx} out of range (0-{len(gpus)-1})")
        print(f"  Run 'radical gpu list' to see available GPUs")
        return

    _CONFIG["selected_gpu"] = idx
    _save_config()
    selected = gpus[idx]
    print(f"  Switched to GPU {idx}: {selected['name']}")
    print(f"  Restart required: full reboot or 'radical gpu <index>' + reboot shell")
    print(f"  (GPU context re-initialization requires shell restart)")


def _cmd_vram(args):
    """Set max VRAM limit: radical vram <MB> or radical vram off"""
    if not args:
        current = _CONFIG.get("max_vram_mb", 0)
        if current:
            print(f"  VRAM limit: {current} MB")
        else:
            print(f"  VRAM limit: off (no limit)")
        print(f"  Set: radical vram <MB>")
        print(f"  Off: radical vram off")
        return

    if args[0] == "off":
        _CONFIG["max_vram_mb"] = 0
        _save_config()
        print(f"  VRAM limit disabled")
        return

    try:
        mb = int(args[0])
        if mb < 0:
            print(f"  VRAM limit must be >= 0")
            return
        _CONFIG["max_vram_mb"] = mb
        _save_config()
        from .gpu_detect import detect_gpu
        gi = detect_gpu()
        total = gi.get("vram_mb", 0)
        pct = (mb / total * 100) if total else 0
        print(f"  VRAM limit set to {mb} MB ({pct:.0f}% of {total} MB total)")
    except ValueError:
        print(f"  Invalid VRAM size: {args[0]}")


def _run_benchmark():
    import time
    from ep_compiler.math_engine import (
        build_ast,
        ast_to_dict,
    )
    from ep_compiler.variables import (
        evaluate_expression,
        _evaluators,
    )

    print(f"  Radical Benchmark:")
    print(f"  {'Expression':<30} {'GPU':>10} {'CPU':>10} {'Speedup':>8}")
    print(f"  " + "-" * 60)

    exprs = [
        ("sin(x) + cos(y)", {"x": 0.5, "y": 0.3}),
        ("a * b + c / d", {"a": 10, "b": 20, "c": 30, "d": 5}),
        ("sqrt(a*a + b*b)", {"a": 3, "b": 4}),
        ("quadratic(1, -5, 6)", {}),
        ("sin(x)*cos(y) + sin(y)*cos(x)", {"x": 0.2, "y": 0.7}),
    ]

    for label, vars_dict in exprs:
        ast, _ = build_ast(label)
        ad = ast_to_dict(ast)

        # CPU timing
        t0 = time.time()
        for _ in range(1000):
            evaluate_expression(label, None)
        t_cpu = (time.time() - t0) * 1000

        # GPU timing
        t_gpu = float("inf")
        if _engine and _engine.available:
            t0 = time.time()
            for _ in range(1000):
                _engine.eval_ast(ad, vars_dict)
            t_gpu = (time.time() - t0) * 1000

        speedup = t_cpu / t_gpu if t_gpu < float("inf") else 0
        gpu_ms = f"{t_gpu:.1f}ms" if t_gpu < float("inf") else "N/A"
        print(f"  {label:<30} {gpu_ms:>10} {t_cpu:.1f}ms {speedup:>7.1f}x")
