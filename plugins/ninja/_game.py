"""Ninja — corridor walker game logic: player physics + frame orchestration.

Rendering is delegated to NinjaEngine (plugins/ninja/_engine.py) when its
files exist; the physics and the params contract are pure python so the game
can be simulated headless without a GPU. The FIRE is animated per frame by
Lua-derived parameters (plugins/ninja/_lua.py, LURE or python twin).
"""

import math
import os
import sys
import time

import numpy as np

# ── Corridor geometry (matches the scene shader + FSR contract) ──
HALF_WIDTH = 2.75          # corridor is 5.5 m wide
WALL_MARGIN = 0.6          # player keeps this much clearance from walls
WALL_LIMIT = HALF_WIDTH - WALL_MARGIN      # 2.15
CORRIDOR_Z0, CORRIDOR_Z1 = 0.0, 50.0       # corridor ends (end wall at z=50)
STAIR_Z0, STAIR_Z1 = 20.0, 26.0            # stairs occupy z in [20, 26]
STAIR_LEN = STAIR_Z1 - STAIR_Z0            # 6.0 m
STAIR_HEIGHT = 1.8                         # eye ramp: 1.7 -> 3.5 over the stairs
EYE_BASE = 1.7
WALK_SPEED = 3.2
RUN_SPEED = 6.0
TURN_RATE = 1.6                            # rad/s (q/e)
FOV_RAD = 1.1                              # ~63 degrees, radians (shader tan(fov/2))
BRAZIER_SPACING = 6.0
BRAZIER_FIRST_Z = 3.0
CEILING_HEIGHT = 3.5


class NinjaEngineUnavailable(Exception):
    """Raised when the rendering engine (plugins/ninja/_engine.py + shaders)
    cannot be initialized — the game still runs physics headless."""


def halton(base, i):
    """i-th Halton sequence value in [0, 1) (i is 1-based)."""
    f = 1.0
    r = 0.0
    while i > 0:
        f /= base
        r += f * (i % base)
        i //= base
    return r


class Player:
    """Player with forward/back/strafe movement along yaw + turn (q/e)."""

    def __init__(self, x=0.0, z=0.0, yaw=0.0, pitch=0.0, eye_height=EYE_BASE):
        self.x = float(x)
        self.z = float(z)
        self.yaw = float(yaw)
        self.pitch = float(pitch)
        self.eye_height = float(eye_height)
        self.on_stairs = False
        self.t = 0.0

    def update(self, dt, keys):
        """Advance physics by dt. keys: dict with forward/back/left/right/run
        bools (and optional turn_left/turn_right, look_up/look_down)."""
        keys = keys or {}
        fwd = 1.0 if keys.get("forward") else 0.0
        back = 1.0 if keys.get("back") else 0.0
        strafe = (1.0 if keys.get("right") else 0.0) - (1.0 if keys.get("left") else 0.0)
        turn = (1.0 if keys.get("turn_right") else 0.0) - (1.0 if keys.get("turn_left") else 0.0)
        speed = RUN_SPEED if keys.get("run") else WALK_SPEED

        self.yaw += turn * TURN_RATE * dt
        self.pitch = max(-1.3, min(1.3, self.pitch + (
            (1.0 if keys.get("look_up") else 0.0) -
            (1.0 if keys.get("look_down") else 0.0)) * 1.2 * dt))

        v = speed * dt * (fwd - back)
        s = speed * dt * strafe
        self.x += math.sin(self.yaw) * v + math.cos(self.yaw) * s
        self.z += math.cos(self.yaw) * v - math.sin(self.yaw) * s
        self.t += dt

        # Walls: hard clamp to |x| <= halfwidth - 0.6
        self.x = max(-WALL_LIMIT, min(WALL_LIMIT, self.x))
        # Corridor ends: end wall at z=50 stops the player; z<0 clamps
        if self.z < CORRIDOR_Z0:
            self.z = CORRIDOR_Z0
        if self.z > CORRIDOR_Z1:
            self.z = CORRIDOR_Z1

        # Stairs: eye height ramps linearly over z in [20, 26]
        if STAIR_Z0 <= self.z <= STAIR_Z1:
            k = (self.z - STAIR_Z0) / STAIR_LEN
            self.eye_height = EYE_BASE + STAIR_HEIGHT * k
            self.on_stairs = True
        else:
            self.eye_height = EYE_BASE
            self.on_stairs = False

    def state(self, frame_idx):
        return {
            "x": self.x, "z": self.z, "yaw": self.yaw, "pitch": self.pitch,
            "eye_height": self.eye_height, "on_stairs": self.on_stairs,
            "frame_idx": frame_idx,
        }


def write_ppm(path, frame):
    """Minimal P6 PPM writer (RGB, alpha dropped) — no deps needed."""
    h, w = frame.shape[:2]
    with open(path, "wb") as f:
        f.write(b"P6\n%d %d\n255\n" % (w, h))
        f.write(np.ascontiguousarray(frame[:, :, :3]).tobytes())


class NinjaGame:
    """Owns Player + NinjaEngine (lazy init on first frame)."""

    def __init__(self, width=960, height=540, render_scale=0.5, seed=1337):
        self.width = int(width)
        self.height = int(height)
        self.render_scale = float(render_scale)
        self.seed = int(seed)
        self.player = Player()
        self.frame_index = 0
        self.t = 0.0
        self.fps = 0.0
        self.fsr_preset = "quality"
        self.weather = {
            "rain": 1.0,        # 0..1 storm intensity
            "open_roof": True,  # rainy open trench (no ceiling)
            "wetness": 1.0,     # puddles + wet sheen
            "grass": 0.85,      # grass tufts along walls / mud
            "wind": 0.35,       # rain slant
            "speed": 2.2,       # rain fall speed
            "mud": 1.0,         # mud patches
        }
        self.taa = True
        self.accum = 4
        self.sharpen = 0.6
        self.exposure = 1.0
        self._engine = None
        self._engine_failed = None      # error string once init failed
        self._menu = None
        self._last_frame = None
        self._gpu_name = ""
        self._ts_gflops = 0.0
        self._ts_label = ""
        self.dump_paths = []
        self._last_time = time.perf_counter()

    # ── engine lifecycle ──

    def _get_engine(self):
        """Lazily create the NinjaEngine once. Raises NinjaEngineUnavailable."""
        if self._engine is not None:
            return self._engine
        if self._engine_failed:
            raise NinjaEngineUnavailable(self._engine_failed)
        try:
            from plugins.ninja._engine import NinjaEngine
            eng = NinjaEngine(self.width, self.height, self.render_scale, self.seed)
            eng.init()
            eng.set_fsr_preset(self.fsr_preset)
            eng.set_taa(self.taa)
            eng.set_accumulation(self.accum)
            eng.set_sharpen(self.sharpen)
            eng.set_exposure(self.exposure)
            self._engine = eng
            try:
                info = eng.gpu_info()
                if isinstance(info, dict):
                    self._gpu_name = str(info.get("name", info.get("gpu_name", "")))
            except Exception:
                pass
        except Exception as e:
            self._engine_failed = f"NinjaEngine init failed ({type(e).__name__}: {e})"
            raise NinjaEngineUnavailable(self._engine_failed) from e
        return self._engine

    def shutdown(self):
        if self._engine is not None:
            try:
                self._engine.shutdown()
            except Exception:
                pass
            self._engine = None

    def set_resolution(self, width, height):
        """Change render resolution (menu field); rebuilds the engine lazily."""
        self.width, self.height = int(width), int(height)
        self.shutdown()

    # ── frame pipeline ──

    def _step_physics(self, dt, keys):
        self.player.update(dt, keys)
        self.frame_index += 1
        self.t += dt

    def _build_params(self):
        """Build the 128-float param buffer per the engine contract."""
        from ._lua import compute_fire
        p = self.player
        fire = compute_fire(self.t, self.frame_index, self.seed)
        jx = (halton(2, self.frame_index) - 0.5) * (1.0 / self.render_scale)
        jy = (halton(3, self.frame_index) - 0.5) * (1.0 / self.render_scale)
        params = np.zeros(128, dtype=np.float32)
        params[0:3] = (p.x, 0.0, p.z)                 # cam xyz (base y=0)
        params[3] = math.pi - p.yaw                   # shader yaw: yaw=0 faces +z
        params[4] = p.pitch
        params[5] = FOV_RAD
        params[6] = self.t
        params[7] = float(self.seed)
        params[8], params[9] = jx, jy                 # TAA jitter (px)
        params[10] = self.render_scale
        params[11] = p.eye_height
        params[12] = HALF_WIDTH
        params[13] = CORRIDOR_Z1 - CORRIDOR_Z0
        params[14] = STAIR_Z0
        params[15] = STAIR_LEN
        params[16] = STAIR_HEIGHT
        params[17] = BRAZIER_SPACING
        params[18] = BRAZIER_FIRST_Z
        params[19] = CEILING_HEIGHT
        params[20] = fire["fire_freq"]
        params[21] = fire["fire_amp"]
        params[22] = fire["wind_x"]
        params[23] = fire["palette_shift"]
        params[24:34] = fire["phases"]
        params[34] = 1.0 if self.taa else 0.0
        params[35] = float(self.accum)
        params[36] = 1.0                              # fire_shape
        params[37] = self.width * self.render_scale   # render w (shader dispatch)
        params[38] = self.height * self.render_scale  # render h
        w = self.weather
        params[39] = w["rain"]        # rain intensity
        params[40] = 1.0 if w["open_roof"] else 0.0
        params[41] = w["wetness"]     # puddle/wet-sheen strength
        params[42] = w["grass"]       # grass density
        params[43] = w["wind"]        # rain slant
        params[44] = w["speed"]       # rain fall speed
        params[45] = w["mud"]         # mud amount
        params[68] = self.sharpen
        params[69] = self.exposure
        params[70] = float(self.frame_index)
        return params

    @property
    def weather_preset(self):
        w = self.weather
        for name in ("Storm", "Rain", "Light", "Dry"):
            from ._menu import _WEATHER_MAP
            m = _WEATHER_MAP[name]
            if all(abs(w[k] - m[k]) < 1e-6 for k in m):
                return name
        return "Storm"

    @weather_preset.setter
    def weather_preset(self, name):
        from ._menu import _WEATHER_MAP
        if name in _WEATHER_MAP:
            self.weather = dict(_WEATHER_MAP[name])

    def frame(self, dt, keys, auto=False):
        """Advance one frame. Returns (frame_rgba, state_dict)."""
        self._step_physics(dt, keys)
        eng = self._get_engine()
        params = self._build_params()
        eng.set_params(params)
        overlay = None
        if self._menu is not None and self._menu.active:
            overlay = self._menu.text_overlay(self.width, self.height)
        frame = eng.render(overlay) if overlay is not None else eng.render()
        self._last_frame = frame
        if self._menu is not None:
            from ._menu import ts_step
            ts_step(self, frame, self.frame_index)
        now = time.perf_counter()
        self.fps = 1.0 / max(now - self._last_time, 1e-6)
        self._last_time = now
        return frame, self.player.state(self.frame_index)

    # ── output ──

    def save_frame(self, frame, stem):
        """Save a numpy RGBA frame to screenshots/ — PNG via PIL when
        available, else a dependency-free P6 PPM."""
        out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        os.makedirs(out_dir, exist_ok=True)
        try:
            from PIL import Image
            path = os.path.join(out_dir, stem + ".png")
            Image.fromarray(np.ascontiguousarray(frame), "RGBA").save(path)
        except Exception:
            path = os.path.join(out_dir, stem + ".ppm")
            write_ppm(path, frame)
        self.dump_paths.append(path)
        return path

    # ── headless demo ──

    def auto_walk(self, steps=600, dump_every=30, dt=0.016):
        """Headless straight walk: forces forward each frame, records the
        player state, dumps a frame every dump_every frames. Returns the
        state trace (list of dicts)."""
        keys = {"forward": True, "run": True}
        trace = []
        for i in range(int(steps)):
            frame, state = self.frame(dt, keys, auto=True)
            trace.append(state)
            if dump_every and (i + 1) % dump_every == 0:
                self.save_frame(frame, f"auto_{self.frame_index:05d}")
        return trace

    # ── interactive ──

    def play(self, dt=1.0 / 60.0):
        """Interactive play. Windowed (glfw + PyOpenGL) when a display and the
        deps exist; otherwise a terminal-driven session with live status and
        non-blocking keys (W/S fwd/back, A/D strafe, Q/E turn, Shift run,
        M menu, Q/Esc quit)."""
        display = os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
        if display and _module_importable("glfw") and _module_importable("OpenGL.GL"):
            return self._play_windowed(dt)
        return self._play_terminal(dt)

    def _play_terminal(self, dt):
        print(f"  Ninja: terminal mode (no display/OpenGL) — "
              f"W/S fwd/back, A/D strafe, Q/E turn, Shift run, M menu, Q quit; "
              f"in menu: WASD navigate, Enter select, Esc close")
        run = True
        interactive = sys.stdin.isatty()
        while run:
            keys = {}
            menu_active = self._menu is not None and self._menu.active
            if interactive:
                raw = _poll_keys()
                for k in raw:
                    if menu_active:
                        if k in ("w", "W"):
                            keys["menu_up"] = True
                        elif k in ("s", "S"):
                            keys["menu_down"] = True
                        elif k in ("a", "A"):
                            keys["menu_left"] = True
                        elif k in ("d", "D", "\n", "\r", " "):
                            keys["menu_right"] = True
                        elif k in ("\x1b", "m", "M"):
                            keys["menu_close"] = True
                    else:
                        if k in ("w", "W"):
                            keys["forward"] = True
                        elif k in ("s", "S"):
                            keys["back"] = True
                        elif k in ("a", "A"):
                            keys["left"] = True
                        elif k in ("d", "D"):
                            keys["right"] = True
                        elif k in ("q", "Q"):
                            run = False
                        elif k in ("e", "E"):
                            keys["turn_right"] = True
                        elif k == "\t":
                            keys["turn_left"] = True
                        elif k in ("m", "M"):
                            keys["menu_toggle"] = True
                        elif k == "\x1b":
                            run = False
            else:
                keys["forward"] = True
                keys["run"] = True
            if self._menu is not None:
                self._menu.tick(keys)
            t0 = time.perf_counter()
            try:
                frame, state = self.frame(dt, keys)
            except NinjaEngineUnavailable as e:
                print(f"  Ninja: {e}")
                return
            if state["frame_idx"] % 30 == 0:
                stairs = "STAIRS" if state["on_stairs"] else "flat"
                print(f"\r  [f{state['frame_idx']}] x={state['x']:+.2f} "
                      f"z={state['z']:5.2f} eye={state['eye_height']:.2f} "
                      f"{stairs}  menu={'on' if self._menu and self._menu.active else 'off'}  "
                      f"fps={self.fps:4.1f}", end="", flush=True)
            if not interactive and state["frame_idx"] >= 300:
                break
            time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
        print()
        self.shutdown()

    def _play_windowed(self, dt):
        """GLFW window + PyOpenGL glDrawPixels present path (guarded)."""
        import glfw
        from OpenGL import GL as gl
        glfw.init()
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        win = glfw.create_window(self.width, self.height,
                                 "Ninja — corridor walker (FSR 3.1)", None, None)
        if not win:
            glfw.terminate()
            return self._play_terminal(dt)
        glfw.make_context_current(win)
        glfw.set_swap_interval(1)
        keys = {}
        pressed = set()

        def on_key(win, key, scancode, action, mods):
            if action == glfw.PRESS:
                pressed.add(key)
            elif action == glfw.RELEASE:
                pressed.discard(key)
        glfw.set_key_callback(win, on_key)

        def map_keys():
            out = {}
            if glfw.KEY_W in pressed:
                out["forward"] = True
            if glfw.KEY_S in pressed:
                out["back"] = True
            if glfw.KEY_A in pressed:
                out["left"] = True
            if glfw.KEY_D in pressed:
                out["right"] = True
            if glfw.KEY_LEFT_SHIFT in pressed or glfw.KEY_RIGHT_SHIFT in pressed:
                out["run"] = True
            if glfw.KEY_LEFT in pressed:
                out["turn_left"] = True
            if glfw.KEY_RIGHT in pressed:
                out["turn_right"] = True
            if glfw.KEY_UP in pressed:
                out["menu_up"] = True
            if glfw.KEY_DOWN in pressed:
                out["menu_down"] = True
            if glfw.KEY_ENTER in pressed:
                out["menu_right"] = True
            if glfw.KEY_ESCAPE in pressed:
                out["menu_close"] = True
            if glfw.KEY_M in pressed:
                out["menu_toggle"] = True
            return out

        print("  Ninja: windowed mode — WASD move, arrows turn, Shift run, "
              "M menu, Esc quit")
        try:
            while not glfw.window_should_close(win):
                if self._menu is not None:
                    self._menu.tick(map_keys())
                t0 = time.perf_counter()
                try:
                    frame, state = self.frame(dt, map_keys())
                except NinjaEngineUnavailable as e:
                    print(f"  Ninja: {e}")
                    return
                gl.glDrawPixels(self.width, self.height, gl.GL_RGBA,
                                gl.GL_UNSIGNED_BYTE, frame[::-1])
                glfw.swap_buffers(win)
                glfw.poll_events()
                time.sleep(max(0.0, dt - (time.perf_counter() - t0)))
        finally:
            glfw.terminate()
            self.shutdown()

    def menu(self):
        """FSR 3.1 settings menu state machine (lazily created, toggled by M)."""
        if self._menu is None:
            from ._menu import FSRMenu
            self._menu = FSRMenu(self)
        return self._menu


def _module_importable(name):
    try:
        __import__(name)
        return True
    except Exception:
        return False


def _poll_keys(timeout=0.0):
    """Non-blocking read of available stdin bytes (POSIX select)."""
    try:
        import select
        if not select.select([sys.stdin], [], [], timeout)[0]:
            return ""
        return os.read(0, 64).decode("utf-8", errors="ignore")
    except Exception:
        return ""
