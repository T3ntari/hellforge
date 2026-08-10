"""Ninja game plugin tests — real Vulkan render path, headless.

Runs the actual engine on the available GPU (RTX 3050 / Intel Mesa).
Skips gracefully when Vulkan is unavailable.

Run: .venv/bin/python tests/ninja_test.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np

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
        print(f"  [FAIL] {name}: {e}")


def _params(seed=1.0, t=0.0, cam=(0.0, 0.0, 0.0), yaw=0.0, pitch=0.0,
            jitter=(0.0, 0.0), scale=0.67, w=960, h=540,
            taa=1.0, accum=1.0, frame=0):
    p = np.zeros(128, dtype=np.float32)
    p[0], p[1], p[2] = cam
    p[3], p[4], p[5] = yaw, pitch, 1.1
    p[6], p[7] = t, seed
    p[8], p[9] = jitter
    p[10] = scale
    p[11] = 1.7          # eye height
    p[12] = 2.75         # corridor halfwidth (5.5m apart)
    p[13] = 50.0         # corridor length
    p[14], p[15], p[16] = 20.0, 6.0, 1.8   # stairs z0/len/height
    p[17], p[18] = 2.0, 1.0   # brazier spacing / first z
    p[19] = 4.0          # ceiling
    p[20], p[21], p[22] = 1.3, 1.0, 0.4    # fire freq/amp/wind
    p[23] = 0.5          # palette shift
    p[24:34] = np.zeros(10, dtype=np.float32)  # phases
    p[34] = taa
    p[35] = accum
    p[36] = 1.0          # fire shape
    p[37], p[38] = max(8, int(w * scale)), max(8, int(h * scale))
    p[39] = 1.0          # rain
    p[40] = 1.0          # open roof
    p[41] = 1.0          # wetness
    p[42] = 0.85         # grass
    p[43] = 0.35         # rain wind
    p[44] = 2.2          # rain speed
    p[45] = 1.0          # mud
    p[66], p[67] = w, h
    p[68] = 0.6          # sharpen
    p[69] = 1.0          # exposure
    p[70] = frame
    return p


def test_shader_assets():
    from pathlib import Path
    for name in ("scene", "upscale", "accumulate", "sharpen"):
        spv = Path("plugins/ninja/shaders") / f"{name}.spv"
        assert spv.is_file() and spv.stat().st_size > 500, f"{name}.spv missing"
        data = spv.read_bytes()
        assert data[:4] == b"\x03\x02\x23\x07", f"{name}.spv bad magic"


def test_engine_init_and_gpu():
    eng = _engine()
    info = eng.gpu_info()
    assert info.get("name"), "no gpu name"
    assert eng.width == 320 and eng.height == 180
    internal = (eng.internal_w, eng.internal_h)
    assert internal[0] == 160 and internal[1] == 90, f"internal {internal}"
    eng.shutdown()


def test_render_deterministic():
    eng = _engine()
    p1 = _params(t=1.0, taa=0.0)
    eng.set_params(p1)
    f1 = eng.render()
    eng.set_params(_params(t=1.0, taa=0.0))
    f2 = eng.render()
    assert np.array_equal(f1, f2), "same seed+t must produce identical frames"
    assert f1.shape == (180, 320, 4) and f1.dtype == np.uint8
    assert f1.any(), "frame is all black"
    assert f1.std() > 5, f"frame flat (std {f1.std():.1f})"
    eng.shutdown()


def test_fire_animates():
    eng = _engine()
    eng.set_params(_params(t=0.0, taa=0.0))
    a = eng.render()
    eng.set_params(_params(t=2.5, taa=0.0))
    b = eng.render()
    diff = np.abs(a.astype(int) - b.astype(int)).mean()
    assert diff > 0.2, f"fire not animating (mean |Δ| {diff:.2f})"
    eng.shutdown()


def test_walk_straight_physics():
    from plugins.ninja._game import Player
    pl = Player()
    pl.yaw = 0.0
    for _ in range(1000):
        pl.update(0.016, {"forward": True, "back": False, "left": False,
                          "right": False, "run": False})
    assert abs(pl.x) < 1e-9, f"drifted off axis: x={pl.x}"
    assert abs(pl.z - 50.0) < 1e-6, f"did not clamp at end wall: z={pl.z}"
    # stairs: eye height rises over [20, 26]
    pl2 = Player()
    for _ in range(2000):
        pl2.update(0.016, {"forward": True, "back": False, "left": False,
                           "right": False, "run": False})
        z = pl2.z
        if 20.0 < z < 26.0:
            assert pl2.on_stairs, f"stairs flag off at z={z}"
            expect = 1.7 + 1.8 * (z - 20.0) / 6.0
            assert abs(pl2.eye_height - expect) < 0.06, \
                f"eye {pl2.eye_height:.3f} != {expect:.3f} at z={z:.2f}"
        else:
            assert not pl2.on_stairs, f"stairs flag on at z={z}"
    assert pl2.eye_height == 1.7, f"eye not reset: {pl2.eye_height}"


def test_fsr_preset_resizes():
    eng = _engine()
    eng.set_fsr_preset("performance")
    assert eng.render_scale == 0.5
    assert eng.internal_w == 160 and eng.internal_h == 90
    eng.set_fsr_preset("native")
    assert eng.internal_w == 320 and eng.internal_h == 180
    eng.shutdown()


def test_taa_toggle_changes_output():
    eng = _engine()
    eng.set_params(_params(t=0.5, taa=0.0))
    a = eng.render()
    eng.set_params(_params(t=0.5, taa=1.0))
    b = eng.render()
    assert not np.array_equal(a, b), "TAA toggle had no effect"
    eng.shutdown()


def test_accumulation_differs():
    eng = _engine()
    eng.set_params(_params(t=0.2, accum=1.0))
    a = eng.render()
    eng.set_params(_params(t=0.2, accum=16.0))
    b = eng.render()
    assert not np.array_equal(a, b), "accumulation had no effect"
    eng.shutdown()


def test_lua_matches_python_twin():
    from plugins.ninja._lua import compute_fire as fire_params
    from plugins.ninja._lua import _fire_py
    for i in range(3):
        lua = fire_params(0.1 * i, i, 7.0)
        py = _fire_py(0.1 * i, i, 7.0)
        assert lua, "lua returned nothing"
        for k in ("fire_freq", "fire_amp", "wind_x", "wind_y", "palette_shift"):
            assert abs(lua[k] - py[k]) < 1e-9, f"{k} diverged"
        assert len(lua["phases"]) == 10
        assert all(abs(a - b) < 1e-9 for a, b in zip(lua["phases"], py["phases"]))


def test_menu_overlay():
    from plugins.ninja._menu import FSRMenu
    from plugins.ninja._game import NinjaGame
    game = NinjaGame(width=320, height=180)
    menu = FSRMenu(game)
    menu.active = True
    overlay = menu.text_overlay(320, 180)
    assert overlay is not None
    assert overlay.shape == (180, 320, 4)
    assert (overlay[..., 3] > 0).sum() > 200, "overlay too sparse"


def test_auto_walk_dump():
    from plugins.ninja import _game
    eng = _engine()
    game = _game.NinjaGame()
    game._engine = eng
    game._engine_failed = None
    trace = game.auto_walk(steps=12, dump_every=6, dt=0.016)
    assert len(trace) == 12
    zs = [t["z"] for t in trace]
    assert all(b >= a for a, b in zip(zs, zs[1:])), "z not monotonic"
    assert all(abs(t["x"]) <= 2.15 for t in trace), "wall clamp violated"
    from pathlib import Path
    dumps = sorted(Path("plugins/ninja/screenshots").glob("auto_*.png"))
    assert len(dumps) >= 2, f"expected >=2 dumps, got {len(dumps)}"
    eng.shutdown()


import atexit
_ALIVE = []


def _shutdown_all():
    for e in _ALIVE:
        try:
            e.shutdown()
        except Exception:
            pass


atexit.register(_shutdown_all)


def _engine():
    from plugins.ninja._engine import NinjaEngine
    eng = NinjaEngine(width=320, height=180, render_scale=0.5, seed=2.0)
    eng.init()
    if not eng._ready:
        raise RuntimeError("engine not ready")
    _ALIVE.append(eng)
    return eng


def test_weather_changes_scene():
    eng = _engine()
    eng.set_params(_params(t=1.0))
    rain = eng.render()
    p = _params(t=1.0)
    p[39] = 0.0                      # no rain
    eng.set_params(p)
    dry = eng.render()
    assert not np.array_equal(rain, dry), "rain toggle had no effect"
    p2 = _params(t=1.0)
    p2[40] = 0.0                     # closed roof
    eng.set_params(p2)
    closed = eng.render()
    assert not np.array_equal(rain, closed), "roof toggle had no effect"
    p3 = _params(t=1.0)
    p3[41] = 0.0                     # no wetness (dry stone)
    eng.set_params(p3)
    matte = eng.render()
    assert not np.array_equal(rain, matte), "wetness toggle had no effect"
    eng.shutdown()


def test_rain_animates():
    eng = _engine()
    eng.set_params(_params(t=0.0))
    a = eng.render()
    eng.set_params(_params(t=0.7))
    b = eng.render()
    # rain + ripples are time-animated even with fire static-ish params
    diff = np.abs(a.astype(int) - b.astype(int)).mean()
    assert diff > 0.05, f"rain not animating (mean |Δ| {diff:.3f})"
    eng.shutdown()


test("Ninja: weather toggles (rain/roof/wetness)", test_weather_changes_scene)
test("Ninja: rain animates over time", test_rain_animates)
test("Ninja: shader assets (4x .spv valid)", test_shader_assets)
test("Ninja: engine init + GPU info", test_engine_init_and_gpu)
test("Ninja: render deterministic (same seed+t -> identical)", test_render_deterministic)
test("Ninja: fire animates between times", test_fire_animates)
test("Ninja: walk straight — no drift, end wall, stairs", test_walk_straight_physics)
test("Ninja: FSR preset resizes internal res", test_fsr_preset_resizes)
test("Ninja: TAA toggle changes output", test_taa_toggle_changes_output)
test("Ninja: accumulation 16 != 1", test_accumulation_differs)
test("Ninja: Lua fire params == python twin", test_lua_matches_python_twin)
test("Ninja: menu overlay renders", test_menu_overlay)
test("Ninja: auto-walk monotonic + wall clamp + PNG dumps", test_auto_walk_dump)

print(f"\nNINJA TESTS: {passed}/{passed + failed} passed")
sys.exit(1 if failed else 0)
