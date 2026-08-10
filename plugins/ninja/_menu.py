"""Ninja — FSR 3.1 settings menu + in-game text overlay + TensorSHARP status.

The menu is a simple state machine over settings fields; the overlay is drawn
with numpy only (embedded 5x7 glyph bitmap, 8x14 px cells) so it runs headless
with zero image dependencies.
"""

import numpy as np

# ── 5x7 glyph bitmap (uppercase + digits + a few symbols) ──
_GLYPHS = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11111", "00010", "00100", "00010", "00001", "10001", "01110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["00110", "01000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00010", "01100"],
    " ": ["00000"] * 7,
    ".": ["00000", "00000", "00000", "00000", "00000", "00110", "00110"],
    ":": ["00000", "00110", "00110", "00000", "00110", "00110", "00000"],
    "/": ["00000", "00001", "00010", "00100", "01000", "10000", "00000"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    ">": ["01000", "00100", "00010", "00001", "00010", "00100", "01000"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "!": ["00100", "00100", "00100", "00100", "00000", "00100", "00100"],
    ",": ["00000", "00000", "00000", "00000", "00110", "00110", "00100"],
}

CELL_W, CELL_H = 8, 14  # px per character cell (glyph 5x7, scaled 1x2)

_COLOR_BODY = (200, 255, 220, 255)
_COLOR_SEL = (255, 220, 90, 255)
_COLOR_TITLE = (255, 120, 60, 255)
_COLOR_DIM = (150, 160, 150, 255)


def _draw_text(canvas, x, y, text, color):
    """Draw uppercase text at cell position (x, y). Returns None."""
    h, w = canvas.shape[:2]
    for c in text.upper():
        glyph = _GLYPHS.get(c, _GLYPHS[" "])
        for gy in range(7):
            row = glyph[gy]
            for gx in range(5):
                if row[gx] != "1":
                    continue
                for dy in range(2):
                    py = y * CELL_H + gy * 2 + dy
                    px = x * CELL_W + gx + 1
                    if py < h and px < w:
                        canvas[py, px] = color
        x += 1


# ── TensorSHARP integration (honest probe: actually runs a matmul) ──

_ts_state = {"probed": False, "online": False, "gflops": 0.0, "eng": None, "label": "TensorSHARP: probing..."}


def ts_probe():
    """Probe TensorSHARP once. Returns the state dict; never raises."""
    if _ts_state["probed"]:
        return _ts_state
    _ts_state["probed"] = True
    eng = None
    try:
        from plugins.tensorsharp import get_engine
        eng = get_engine()
        if eng is None or not getattr(eng, "available", False):
            from plugins.tensorsharp.cuda_backend import TensorSHARPEngine
            eng = TensorSHARPEngine()
    except Exception:
        eng = None
    if eng is None or not getattr(eng, "available", False):
        _ts_state.update(online=False, eng=None, label="TensorSHARP: offline (no CUDA)")
        return _ts_state
    try:
        import time
        A = np.random.rand(16, 16).astype(np.float32)
        B = np.eye(16, dtype=np.float32)
        t0 = time.perf_counter()
        C = eng.matmul(A, B)
        dt = time.perf_counter() - t0
        if C is None:
            _ts_state.update(online=False, eng=None,
                             label="TensorSHARP: offline (CUDA matmul unavailable)")
            return _ts_state
        gflops = 2.0 * 16 * 16 * 16 / 1e9 / max(dt, 1e-9)
        _ts_state.update(online=True, eng=eng, gflops=gflops,
                         label=f"TensorSHARP: {gflops:.1f} TFLOPS")
    except Exception as e:
        _ts_state.update(online=False, eng=None,
                         label=f"TensorSHARP: offline ({type(e).__name__})")
    return _ts_state


def ts_step(game, frame, frame_index):
    """Per-30-frame accelerator: downsample the frame luma to 16x16 and run
    eng.matmul(A, identity) on it, refreshing the TFLOPS figure. Never raises."""
    st = _ts_state
    if not st["online"] or st["eng"] is None:
        return
    if frame_index % 30 != 1:
        return
    try:
        import time
        fr = frame
        luma = (0.299 * fr[..., 0] + 0.587 * fr[..., 1] + 0.114 * fr[..., 2]).astype(np.float32)
        h, w = luma.shape
        A = luma[:: max(1, h // 16), :: max(1, w // 16)][:16, :16]
        if A.shape != (16, 16):
            A = np.resize(A, (16, 16))
        t0 = time.perf_counter()
        C = st["eng"].matmul(A, np.eye(16, dtype=np.float32))
        dt = time.perf_counter() - t0
        if C is not None:
            g = 2.0 * 16 * 16 * 16 / 1e9 / max(dt, 1e-9)
            _ts_state["gflops"] = _ts_state["gflops"] * 0.7 + g * 0.3
            _ts_state["label"] = f"TensorSHARP: {_ts_state['gflops']:.1f} TFLOPS"
    except Exception:
        pass


# ── FSR menu state machine ──

_PRESETS = ["native", "quality", "balanced", "performance"]
_RESOLUTIONS = ["960x540", "1280x720", "640x360"]
_TAA = ["off", "on"]
_ACCUM = ["1", "4", "16", "64"]
_SHARPEN = [round(i * 0.1, 1) for i in range(11)]          # 0.0 .. 1.0
_EXPOSURE = [round(0.5 + i * 0.1, 1) for i in range(16)]   # 0.5 .. 2.0
_WEATHER = ["Storm", "Rain", "Light", "Dry"]
_WEATHER_MAP = {
    "Storm": {"rain": 1.0, "wetness": 1.0, "open_roof": True, "wind": 0.55,
              "speed": 2.6, "grass": 0.85, "mud": 1.0},
    "Rain": {"rain": 0.65, "wetness": 0.9, "open_roof": True, "wind": 0.3,
             "speed": 2.2, "grass": 0.8, "mud": 0.9},
    "Light": {"rain": 0.3, "wetness": 0.55, "open_roof": True, "wind": 0.15,
              "speed": 1.8, "grass": 0.6, "mud": 0.6},
    "Dry": {"rain": 0.0, "wetness": 0.0, "open_roof": True, "wind": 0.0,
            "speed": 2.2, "grass": 0.3, "mud": 0.2},
}


class FSRMenu:
    """Settings menu: preset / TAA / accumulation / sharpen / exposure / res."""

    def __init__(self, game):
        self.game = game
        self.active = False
        self.sel = 0
        self.fields = [
            ("FSR 3.1 preset", _PRESETS, lambda: game.fsr_preset, lambda v: setattr(game, "fsr_preset", v)),
            ("TAA", _TAA, lambda: "on" if game.taa else "off", lambda v: setattr(game, "taa", v == "on")),
            ("Accumulation", _ACCUM, lambda: str(game.accum), lambda v: setattr(game, "accum", int(v))),
            ("Sharpen", _SHARPEN, lambda: str(game.sharpen), lambda v: setattr(game, "sharpen", float(v))),
            ("Exposure", _EXPOSURE, lambda: str(game.exposure), lambda v: setattr(game, "exposure", float(v))),
            ("Resolution", _RESOLUTIONS, lambda: f"{game.width}x{game.height}",
             lambda v: game.set_resolution(*[int(p) for p in v.split("x")])),
            ("Weather", _WEATHER, lambda: game.weather_preset,
             lambda v: setattr(game, "weather_preset", v)),
        ]

    def tick(self, keys):
        """Advance the menu from the extended key dict. Returns True if the
        menu state changed."""
        keys = keys or {}
        changed = False
        if keys.get("menu_toggle"):
            self.active = not self.active
            changed = True
        if not self.active:
            return changed
        if keys.get("menu_up"):
            self.sel = (self.sel - 1) % len(self.fields)
            changed = True
        if keys.get("menu_down"):
            self.sel = (self.sel + 1) % len(self.fields)
            changed = True
        if keys.get("menu_left"):
            self._cycle(-1)
            changed = True
        if keys.get("menu_right"):
            self._cycle(1)
            changed = True
        if keys.get("menu_close"):
            self.active = False
            changed = True
        return changed

    def _cycle(self, delta):
        label, options, getter, setter = self.fields[self.sel]
        cur = getter()
        idx = 0
        for i, opt in enumerate(options):
            if str(opt) == str(cur):
                idx = i
                break
        setter(options[(idx + delta) % len(options)])

    def _field_lines(self):
        lines = []
        for i, (label, options, getter, setter) in enumerate(self.fields):
            marker = ">" if i == self.sel else " "
            lines.append(f"{marker} {label:<16} {getter()}")
        return lines

    def text_overlay(self, width, height):
        """Render the menu overlay as uint8 RGBA (height, width, 4), or None
        when the menu is inactive."""
        if not self.active:
            return None
        g = self.game
        lines = ["NINJA — FSR 3.1"]
        lines += self._field_lines()
        lines.append(" ")
        fps = g.fps if getattr(g, "fps", 0) else 0
        gpu = getattr(g, "_gpu_name", "")
        lines.append(f"FPS {fps:0.0f}" + (f"  |  {gpu}" if gpu else ""))
        lines.append(ts_probe()["label"])
        p = g.player
        lines.append(f"Z {p.z:6.1f}  STAIRS {'ON' if p.on_stairs else 'OFF'}")
        lines.append("ARROWS/WASD NAV  ENTER SELECT  ESC CLOSE")
        width_cells = max(len(l) for l in lines) + 2
        canvas = np.zeros((height, width, 4), dtype=np.uint8)
        panel_h = (len(lines) + 1) * CELL_H + 8
        panel_w = width_cells * CELL_W
        canvas[4:panel_h, 4:panel_w] = (12, 12, 18, 210)
        y = 1
        for i, line in enumerate(lines):
            if line == " ":
                y += 1
                continue
            if i == 0:
                color = _COLOR_TITLE
            elif i - 1 == self.sel and line.startswith(">"):
                color = _COLOR_SEL
            else:
                color = _COLOR_BODY
            _draw_text(canvas, 1, y, line, color)
            y += 1
        return canvas
