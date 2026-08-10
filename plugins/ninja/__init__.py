"""Ninja v1.0.0 — corridor walker ray-marched on Vulkan compute.

First-person ninja corridor rendered in a compute shader (scene.comp), with
FSR 3.1-style upscaling, TAA + frame accumulation handled by the engine
pipeline passes, Lua-driven fire animation (LURE / python twin) and a
TensorSHARP CUDA status meter. The game and menu run headless; the engine is
created lazily on first frame and every command degrades gracefully when
Vulkan is missing.
"""

import os
import sys

VERSION = "1.0.0"
author = "Tentari"
description = "Ninja corridor walker — Vulkan compute ray-marched ninja game (FSR 3.1 menu, TAA, accumulation, Lua fire)"

_game_singleton = None
_engine_error = None


def register(api):
    api.add_boot_step(f"Ninja v{VERSION}", "loading")

    # Require the Vulkanizer plugin. api.require() pip-installs whatever it
    # cannot import, so alias the plugin module under its display name first —
    # the import is side-effect free (Vulkanizer registers itself later in the
    # boot order) and only then declare the dependency.
    try:
        import vulkanizer
        sys.modules.setdefault("Vulkanizer", vulkanizer)
    except ImportError:
        pass
    api.require("Vulkanizer")

    gpu, diag = _probe_vulkan()
    if gpu:
        api.add_boot_step(f"Ninja: engine ready ({gpu})", "done")
    else:
        api.add_boot_step(f"Ninja: unavailable ({diag or 'unknown'})", "skip")

    if _shader_compiled("scene"):
        api.add_boot_step("Ninja: scene shader compiled", "done")
    api.add_boot_step("Ninja: corridor walker ready", "done")

    api.add_command("ninja", _cmd, "Ninja: ninja [demo|status] — Vulkan compute ninja corridor walker")


def _probe_vulkan():
    """Return (gpu_name_or_None, diagnostic_or_None) without building the
    engine: reuse Vulkanizer's registered API when it already exists, else
    probe a throwaway instance for the device name."""
    try:
        from plugins.vulkanizer import get_api
        vkapi = get_api()
        if vkapi is not None and getattr(vkapi, "available", False):
            return vkapi.instance.gpu_info.get("name", "Unknown GPU"), None
    except Exception as e:
        return None, f"vulkanizer probe: {e}"
    try:
        from plugins.vulkanizer._instance import VkInstance
        inst = VkInstance()
        if inst.available:
            name = inst.gpu_info.get("name", "Unknown GPU")
            inst._cleanup()
            return name, None
        return None, inst.diagnostic or "no Vulkan device"
    except ImportError:
        return None, "vulkanizer plugin not importable"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _shader_compiled(name):
    return os.path.exists(os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "shaders", f"{name}.spv"))


def get_game():
    """Lazy singleton game — engine itself is created on first frame.
    NB: named _game_singleton so the `from ._game import NinjaGame` submodule
    import cannot poison it — the import machinery rebinds the package
    attribute `_game` to the submodule, so any earlier `import
    plugins.ninja._game` would make the singleton return the module."""
    global _game_singleton
    if _game_singleton is None:
        from ._game import NinjaGame
        _game_singleton = NinjaGame()
    return _game_singleton


def _cmd(args):
    args = args or []
    if args and args[0] == "demo":
        _demo(args[1] if len(args) > 1 else None)
    elif args and args[0] == "status":
        _status()
    elif not args or args[0] in ("play", "run"):
        _play()
    else:
        print("  Usage: ninja [demo [frames]] | ninja status")


def _engine_available():
    """Pre-flight check so commands can print a graceful error upfront."""
    global _engine_error
    if _engine_error:
        return False
    try:
        import importlib.util
        spec = importlib.util.find_spec("plugins.ninja._engine")
        if spec is None:
            _engine_error = ("engine missing (plugins/ninja/_engine.py not "
                             "built yet — rendering unavailable, physics runs headless)")
            return False
        return True
    except Exception as e:
        _engine_error = f"engine probe failed ({e})"
        return False


def _play():
    if not _engine_available():
        print(f"  Ninja: {_engine_error}")
        print("  Ninja: play needs the engine; try 'ninja demo' once it exists")
        return
    game = get_game()
    game.menu()
    game.play()


def _demo(frames):
    if not _engine_available():
        print(f"  Ninja: {_engine_error}")
        return
    game = get_game()
    n = int(frames) if frames else 600
    print(f"  Ninja: headless demo — {n} frames, straight walk")
    try:
        trace = game.auto_walk(steps=n)
    except Exception as e:
        print(f"  Ninja: demo aborted ({type(e).__name__}: {e})")
        return
    last = trace[-1] if trace else {}
    print(f"  Ninja: done — {len(trace)} frames, z={last.get('z', '?')}, "
          f"x={last.get('x', '?')}, dumps: {len(game.dump_paths)}")
    for p in game.dump_paths:
        print(f"    {p}")
    game.shutdown()


def _status():
    game = get_game()
    p = game.player
    print(f"  Ninja v{VERSION} — corridor walker")
    print(f"  Player: x={p.x:+.2f} z={p.z:5.2f} eye={p.eye_height:.2f} "
          f"stairs={'on' if p.on_stairs else 'off'}")
    print(f"  Frame: {game.frame_index} | res: {game.width}x{game.height} "
          f"(render scale {game.render_scale})")
    print(f"  FSR 3.1 preset: {game.fsr_preset} | TAA: {'on' if game.taa else 'off'} "
          f"| accumulation: {game.accum} | sharpen: {game.sharpen} | "
          f"exposure: {game.exposure}")
    if not _engine_available():
        print(f"  Engine: unavailable ({_engine_error})")
        return
    try:
        eng = game._get_engine()
        info = eng.gpu_info()
        print(f"  Engine: {info.get('name', 'GPU')} ({info.get('vendor', '?')})")
        print(f"  Internal: {info.get('internal_w')}x{info.get('internal_h')} | "
              f"output: {info.get('output_w')}x{info.get('output_h')}")
        if info.get("frame_ms"):
            print(f"  Frame: {info['frame_ms']:.2f} ms (~{info.get('fps', 0):.0f} fps)")
    except Exception as e:
        print(f"  Engine: error ({type(e).__name__}: {e})")
    try:
        from ._menu import ts_probe
        print(f"  {ts_probe()['label']}")
    except Exception:
        pass
