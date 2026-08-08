"""Humanize application — de-robots compiled events.

Takes compiled events + the MoE predictions and applies micro-timing
jitter + expressive velocity deltas, scaled by @humanize strength (0-100).

Key design: applied deltas are FED BACK as the 'previous offset / velocity'
features for the next note (continuation), so timing feels like a human
curve instead of independent noise. Pure numpy, single pass, instant.
"""

import numpy as np

from . import moe

MAX_JITTER_MS = 25.0


def apply_humanize(events, bpm=120, strength=None, params=None):
    """Apply humanization in place-safe manner; returns NEW event list.
    strength: 0-100 (default DEFAULT_STRENGTH). 0 or None-of-events → unchanged."""
    if strength is None:
        strength = moe.DEFAULT_STRENGTH
    strength = max(0.0, min(100.0, float(strength)))
    if strength <= 0 or not events:
        return list(events)
    if params is None:
        params, _ = moe.load_or_train()

    n = len(events)
    ts = np.array([e["timestamp"] for e in events], dtype=np.float64)
    midi = np.array([e["midi"] for e in events], dtype=np.float32)
    vel = np.array([e["velocity"] for e in events], dtype=np.float32)
    order = np.argsort(ts, kind="stable")
    ts, midi, vel = ts[order], midi[order], vel[order]
    inv = np.empty_like(order)
    inv[order] = np.arange(n)

    beat_ms = 60000.0 / max(1, bpm)
    pos_in_bar = (ts % beat_ms) / beat_ms

    # local density via sorted search — O(n log n), not O(n²)
    density = np.zeros(n, dtype=np.float32)
    if n > 1:
        order_ts = np.argsort(ts, kind="stable")
        sorted_ts = ts[order_ts]
        lo = np.searchsorted(sorted_ts, ts - 500.0, side="left")
        hi = np.searchsorted(sorted_ts, ts + 500.0, side="right")
        density = ((hi - lo) / 1.001).astype(np.float32)

    scale = strength / 100.0
    # 2-pass batched inference (continuation feedback):
    # pass 1 assumes zero previous state; pass 2 feeds pass-1 results back.
    # The model output is smooth, so 2 passes converge — no per-note loop.
    base = np.stack([midi / 127.0, vel / 127.0, pos_in_bar.astype(np.float32),
                     density / 20.0], axis=1)  # (N, 4)

    def _predict(prev_off, prev_delta):
        x = np.empty((n, moe.N_FEATURES), dtype=np.float32)
        x[:, :4] = base
        x[:, 4] = prev_off / 15.0
        x[:, 5] = prev_delta / 10.0
        return moe.predict(x, params)

    p1 = _predict(np.zeros(n, dtype=np.float32), np.zeros(n, dtype=np.float32))
    prev_off = np.concatenate([[0.0], p1[:-1, 0]])
    prev_delta = np.concatenate([[0.0], p1[:-1, 1]])
    p2 = _predict(prev_off, prev_delta)

    offsets = np.clip(p2[:, 0] * scale, -MAX_JITTER_MS, MAX_JITTER_MS)
    deltas = np.clip(p2[:, 1] * scale, -14.0, 14.0)

    # apply — clamp so notes never collapse backwards past the previous note
    new_ts = ts + offsets.astype(np.float64)
    for i in range(1, n):
        min_ok = new_ts[i - 1] + 5.0
        if new_ts[i] < min_ok:
            new_ts[i] = min_ok
    new_vel = np.clip(vel + deltas, 1.0, 127.0)

    result = []
    for i in range(n):
        e = dict(events[inv[i]])
        e["timestamp"] = int(round(float(new_ts[i])))
        e["velocity"] = int(round(float(new_vel[i])))
        result.append(e)
    return result
