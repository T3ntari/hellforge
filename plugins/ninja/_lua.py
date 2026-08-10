"""Ninja — fire parameters driven by Lua (via LURE), with a deterministic
pure-python fallback.

The corridor fires are animated by parameters computed each frame in a Lua
script executed through plugins.lure's LuaJIT runtime. If LURE is missing or
fails, the exact same formulas run in Python — the two paths are kept
identical so a given (t, frame_index, seed) always produces the same fire.
"""

import math

# LuaJIT script — receives globals t, frame_index, seed, returns a table.
LUA_SCRIPT = r"""
-- ninja fire: animated brazier parameters, derived from (t, frame_index, seed)
local s = (seed % 97) / 97.0
local phases = {}
for i = 1, 10 do
    phases[i] = i * 0.618 + math.sin(t * 0.1 + i) * 0.3
end
return {
    fire_freq     = 1.2 + 0.3 * math.sin(t * 0.7 + s),
    fire_amp      = 0.8 + 0.4 * math.sin(t * 0.31 + 1.0 + s),
    wind_x        = 0.3 + 0.2 * math.sin(t * 0.13 + s),
    wind_y        = 0.2 + 0.15 * math.sin(t * 0.11 + 2.0 + s),
    palette_shift = 0.5 + 0.5 * math.sin(t * 0.17 + s),
    phases        = phases,
}
"""


def _fire_py(t, frame_index, seed):
    """Pure-python twin of the Lua script — same formulas, same determinism."""
    s = (seed % 97) / 97.0
    phases = [i * 0.618 + math.sin(t * 0.1 + i) * 0.3 for i in range(1, 11)]
    return {
        "fire_freq": 1.2 + 0.3 * math.sin(t * 0.7 + s),
        "fire_amp": 0.8 + 0.4 * math.sin(t * 0.31 + 1.0 + s),
        "wind_x": 0.3 + 0.2 * math.sin(t * 0.13 + s),
        "wind_y": 0.2 + 0.15 * math.sin(t * 0.11 + 2.0 + s),
        "palette_shift": 0.5 + 0.5 * math.sin(t * 0.17 + s),
        "phases": phases,
    }


def _lua_table_to_dict(tbl):
    out = {}
    for k in tbl:
        out[k] = tbl[k]
    return out


def compute_fire(t, frame_index, seed):
    """Return dict {fire_freq, fire_amp, wind_x, wind_y, palette_shift, phases}.
    Runs through LuaJIT when LURE is available, else the identical python twin."""
    try:
        from plugins.lure import get_engine
        eng = get_engine()
        if eng is not None and eng.available and eng.lua is not None:
            g = eng.lua.globals()
            g.t = float(t)
            g.frame_index = int(frame_index)
            g.seed = int(seed)
            tbl = eng.lua.execute(LUA_SCRIPT)
            out = _lua_table_to_dict(tbl)
            phases_tbl = out.get("phases")
            if phases_tbl is not None:
                out["phases"] = [float(phases_tbl[i]) for i in range(1, 11)]
            return out
    except Exception:
        pass
    return _fire_py(t, frame_index, seed)


def available():
    """True when the Lua path is actually in use."""
    try:
        from plugins.lure import get_engine
        eng = get_engine()
        return eng is not None and eng.available and eng.lua is not None
    except Exception:
        return False
