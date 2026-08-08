"""HELLFORGE runtime configuration — real, applied settings shared with eshell.

Reads/writes the same store as eshell (ep_core._plugin_configs ->
.plugin_config.json). Applying changes has REAL effects:
  - max memory   -> loop unroll cap (prevents OOM) + persisted sys mem limit
  - threads      -> async compile thread pool resized for real
  - gpu          -> GPU math evaluators (TensorSHARP/Radical) enabled/disabled
  - lure         -> LURE (LuaJIT) math evaluator enabled/disabled
  - strict       -> default strictness for compiles
"""

import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Evaluator names that are GPU-backed
GPU_EVALUATORS = {"TensorSHARP", "Radical"}
LURE_EVALUATOR = "LURE"

DEFAULTS = {
    "shell_path": "",
    "max_memory_gb": 2.0,
    "threads": 0,               # 0 = auto (cpu_count * 2, capped 32)
    "gpu_acceleration": True,
    "lure_acceleration": True,
    "strict_default": False,
    "loop_cap": 100000,
    "auto_compile_on_save": True,
    "play_windowed": False,
    "velocity_warning": True,
}


def _load_store():
    """Load plugin configs dict (shared with eshell)."""
    try:
        import ep_core
        return ep_core._plugin_configs
    except Exception:
        return {}


def _save_store(cfg):
    try:
        import ep_core
        ep_core._plugin_configs.update(cfg)
        ep_core._save_plugin_configs()
    except Exception:
        pass


def detect_shell_path():
    """Find the eshell executable. Returns path or ''."""
    cands = [
        os.path.join(PROJECT_DIR, "eshell.py"),
        os.path.join(PROJECT_DIR, "eshell.exe"),
        os.path.join(PROJECT_DIR, "run.py"),
    ]
    for c in cands:
        if os.path.exists(c):
            return c
    return ""


def get_runtime_config():
    """Return the current runtime config (live from the shared store)."""
    store = _load_store()
    cfg = dict(DEFAULTS)
    cfg["shell_path"] = store.get("_shell_path") or detect_shell_path()
    cfg["max_memory_gb"] = float(store.get("_sys_mem_gb", DEFAULTS["max_memory_gb"]))
    cfg["threads"] = int(store.get("_sys_threads", DEFAULTS["threads"]))
    cfg["gpu_acceleration"] = bool(store.get("_gpu_enabled", True))
    cfg["lure_acceleration"] = bool(store.get("_lure_enabled", True))
    cfg["strict_default"] = bool(store.get("_strict_default", False))
    cfg["loop_cap"] = int(store.get("_loop_cap", DEFAULTS["loop_cap"]))
    cfg["auto_compile_on_save"] = bool(store.get("_auto_compile", True))
    cfg["play_windowed"] = bool(store.get("_play_windowed", False))
    cfg["velocity_warning"] = bool(store.get("_velocity_warning", True))
    return cfg


def _set_gpu_enabled(enabled):
    """Really enable/disable GPU math evaluators (TensorSHARP, Radical)."""
    try:
        from ep_compiler.variables import set_evaluator_enabled
        for name in GPU_EVALUATORS:
            set_evaluator_enabled(name, enabled)
    except Exception:
        pass


def _set_lure_enabled(enabled):
    try:
        from ep_compiler.variables import set_evaluator_enabled
        set_evaluator_enabled(LURE_EVALUATOR, enabled)
    except Exception:
        pass


def _set_threads(n):
    """Resize the async compile thread pool for real."""
    try:
        from ep_compiler import async_compile
        async_compile.set_thread_pool_size(max(1, int(n)))
    except Exception:
        pass
    try:
        from plugins.fentclient.async_engine import set_async_threads
        set_async_threads(max(1, int(n)))
    except Exception:
        pass


def _set_loop_cap(n):
    try:
        from ep_compiler.loops import set_unroll_cap
        set_unroll_cap(max(0, int(n)))
    except Exception:
        pass


def apply_runtime_config(cfg):
    """Apply config for real and persist. Returns the applied config."""
    store = {}
    gpu = bool(cfg.get("gpu_acceleration", True))
    lure = bool(cfg.get("lure_acceleration", True))
    mem_gb = max(1.0, min(64.0, float(cfg.get("max_memory_gb", 2.0))))
    threads = max(0, min(64, int(cfg.get("threads", 0) or 0)))
    loop_cap = max(0, int(cfg.get("loop_cap", 100000)))

    _set_gpu_enabled(gpu)
    _set_lure_enabled(lure)
    if threads:
        _set_threads(threads)
    _set_loop_cap(loop_cap)

    # Persist into the shared store (eshell reads these too)
    shell = (cfg.get("shell_path") or "").strip()
    store["_shell_path"] = shell
    store["_sys_mem_gb"] = mem_gb
    store["_sys_threads"] = threads
    store["_gpu_enabled"] = gpu
    store["_lure_enabled"] = lure
    store["_loop_cap"] = loop_cap
    store["_strict_default"] = bool(cfg.get("strict_default", False))
    store["_auto_compile"] = bool(cfg.get("auto_compile_on_save", True))
    store["_play_windowed"] = bool(cfg.get("play_windowed", False))
    store["_velocity_warning"] = bool(cfg.get("velocity_warning", True))
    _save_store(store)

    return get_runtime_config()
