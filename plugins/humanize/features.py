"""Per-note context extraction for the Humanize MoE.

Builds a (N, 6) feature matrix from compiled events:
  0. pitch           MIDI / 127
  1. velocity        MIDI / 127
  2. position in bar phase (0..1)  — beat-relative
  3. local density   notes/sec within +/- 0.5s window
  4. previous offset (ms, /15)
  5. previous velocity delta (/10)

Deterministic, pure numpy — no state.
"""

import numpy as np

N_FEATURES = 6


def extract_features(events, bpm=120):
    """events: list of dicts with timestamp/midi/velocity (sorted optional).
    Returns (np.float32 (N, 6), np.float32 (N, 2) prev-state matrix)."""
    n = len(events)
    if n == 0:
        return np.zeros((0, N_FEATURES), dtype=np.float32), np.zeros((0, 2), dtype=np.float32)

    ts = np.array([e["timestamp"] for e in events], dtype=np.float64)
    midi = np.array([e["midi"] for e in events], dtype=np.float32)
    vel = np.array([e["velocity"] for e in events], dtype=np.float32)
    order = np.argsort(ts, kind="stable")
    ts, midi, vel = ts[order], midi[order], vel[order]

    beat_ms = 60000.0 / max(1, bpm)
    pos_in_bar = (ts % beat_ms) / beat_ms

    # local density: notes within +/-500ms
    density = np.zeros(n, dtype=np.float32)
    for i in range(n):
        window = (ts >= ts[i] - 500.0) & (ts <= ts[i] + 500.0)
        density[i] = float(window.sum()) / 1.001  # notes per ~1s window

    # previous state (continuation): offset/delta from previous event
    prev_off = np.zeros(n, dtype=np.float32)
    prev_vel = np.zeros(n, dtype=np.float32)
    if n > 1:
        prev_off[1:] = 0.0  # applied offsets unknown pre-humanization; humanizer feeds back its predicted offsets
        prev_vel[1:] = vel[1:] - vel[:-1]  # velocity delta from previous note

    x = np.stack([midi / 127.0, vel / 127.0, pos_in_bar.astype(np.float32),
                  density / 20.0, prev_off / 15.0, prev_vel / 10.0], axis=1)
    return x.astype(np.float32), order
