"""Humanize MoE — a tiny Mixture-of-Experts model (pure numpy, ~50k params).

Takes per-note context (6 features) and predicts:
  - micro-timing offset (ms, typically -12..+12)
  - velocity delta (MIDI units, typically -8..+8)

Architecture:
  pre-encoder   6 -> 16        (shared)
  router        16 -> 8 experts (softmax gate)
  experts       8 x (16 -> 320 -> 2)   ReLU hidden

Total params ≈ 49k. Trained once with mini-batch SGD on a synthetic
human-performance regression task, cached to .fent_cache so inference
is instant afterwards. Deterministic (fixed seed) for reproducible output.
"""

import os
import time

import numpy as np

# ── Architecture ──
N_FEATURES = 6
PRE_HIDDEN = 16
N_EXPERTS = 8
EXPERT_HIDDEN = 320
N_OUTPUTS = 2

SEED = 1337
DEFAULT_STRENGTH = 15  # 0-100, scales predicted deltas

rng = np.random.default_rng(SEED)


# ── Model ──

def init_params():
    """Random init of all weights (Xavier-ish). Returns dict of arrays."""
    p = {}
    p["pre_w"] = (rng.standard_normal((N_FEATURES, PRE_HIDDEN)) * 0.5).astype(np.float32)
    p["pre_b"] = np.zeros(PRE_HIDDEN, dtype=np.float32)
    p["gate_w"] = (rng.standard_normal((PRE_HIDDEN, N_EXPERTS)) * 0.4).astype(np.float32)
    p["gate_b"] = np.zeros(N_EXPERTS, dtype=np.float32)
    exp_w1, exp_b1, exp_w2, exp_b2 = [], [], [], []
    for _ in range(N_EXPERTS):
        exp_w1.append((rng.standard_normal((PRE_HIDDEN, EXPERT_HIDDEN)) * 0.35).astype(np.float32))
        exp_b1.append(np.zeros(EXPERT_HIDDEN, dtype=np.float32))
        exp_w2.append((rng.standard_normal((EXPERT_HIDDEN, N_OUTPUTS)) * 0.25).astype(np.float32))
        exp_b2.append(np.zeros(N_OUTPUTS, dtype=np.float32))
    p["exp_w1"] = np.stack(exp_w1)  # (E, PRE, H)
    p["exp_b1"] = np.stack(exp_b1)  # (E, H)
    p["exp_w2"] = np.stack(exp_w2)  # (E, H, 2)
    p["exp_b2"] = np.stack(exp_b2)  # (E, 2)
    return p


def param_count(p):
    return int(sum(a.size for a in p.values()))


# ── Forward ──

def predict(x, p):
    """Vectorized MoE forward. x: (N, 6) float32 → (N, 2) float32.
    Returns predicted (offset_ms, velocity_delta) per note."""
    n = x.shape[0]
    h = np.tanh(x @ p["pre_w"] + p["pre_b"])                 # (N, PRE)
    gate = h @ p["gate_w"] + p["gate_b"]                     # (N, E)
    gate = np.exp(gate - gate.max(axis=1, keepdims=True))
    g = gate / gate.sum(axis=1, keepdims=True)               # softmax
    out = np.zeros((n, N_OUTPUTS), dtype=np.float32)
    for e in range(N_EXPERTS):                               # per-expert matmuls
        z = np.tanh(h @ p["exp_w1"][e] + p["exp_b1"][e])     # (N, H)
        o = z @ p["exp_w2"][e] + p["exp_b2"][e]              # (N, 2)
        out += g[:, e:e + 1] * o
    return out


# ── Synthetic human-performance regression task ──

def make_dataset(n=16000):
    """Generate (contexts, targets) simulating human playing:
    - slight anticipation on downbeats, lag on syncopation
    - jitter inversely proportional to local note density
    - expressive velocity swells + continuity from previous note
    - 'continuation' effect: humans keep curves going (prev deltas carry over)"""
    pitch = rng.uniform(21, 108, n)
    velocity = rng.uniform(0.05, 1.0, n)
    pos = rng.uniform(0, 1, n)                 # position in bar
    density = rng.uniform(1, 20, n)            # notes per second locally
    prev_off = rng.uniform(-15, 15, n)
    prev_vel = rng.uniform(-10, 10, n)
    x = np.stack([pitch / 127.0, velocity, pos, density / 20.0,
                  prev_off / 15.0, prev_vel / 10.0], axis=1).astype(np.float32)

    # micro-timing: early on beat 1, breathy lag mid-bar, jitter ∝ 1/√density
    offset = (-4.0 + 6.0 * np.cos(2 * np.pi * pos)
              + 3.0 * np.sin(4 * np.pi * pos)
              + 6.0 * np.sin(2 * np.pi * pos * density / 20.0)
              + rng.normal(0, 6.0 / (0.5 + np.sqrt(density)), n))
    # small human continuity: keep some of the previous note's timing
    offset += 0.15 * prev_off
    offset = np.clip(offset, -25, 25)

    # velocity: swell toward bar end, louder notes pull a bit, continue curve
    vel_delta = (5.0 * np.sin(2 * np.pi * pos)
                 + 4.0 * (velocity - 0.5)
                 + 0.35 * prev_vel
                 + rng.normal(0, 1.8, n))
    vel_delta = np.clip(vel_delta, -14, 14)

    y = np.stack([offset, vel_delta], axis=1).astype(np.float32)
    return x, y


def train(epochs=18, batch=512, lr=0.03, dataset_n=12000, progress=None):
    """Train the MoE with mini-batch SGD. Returns (params, time_s).
    Numerically stable: gradients are clipped elementwise so a bad random
    draw can never diverge the training to NaN (observed with numpy 2.x)."""
    GRAD_CLIP = 1.0  # max magnitude of any single gradient element

    def _step(name, grad):
        np.clip(grad, -GRAD_CLIP, GRAD_CLIP, out=grad)
        p[name] -= lr * grad

    t0 = time.time()
    x, y = make_dataset(dataset_n)
    p = init_params()
    n = x.shape[0]
    for epoch in range(epochs):
        perm = rng.permutation(n)
        for i in range(0, n, batch):
            idx = perm[i:i + batch]
            xb, yb = x[idx], y[idx]
            # ── forward ──
            h = np.tanh(xb @ p["pre_w"] + p["pre_b"])                 # (B, PRE)
            gate_logit = h @ p["gate_w"] + p["gate_b"]                # (B, E)
            g = np.exp(gate_logit - gate_logit.max(axis=1, keepdims=True))
            g = g / g.sum(axis=1, keepdims=True)                      # (B, E)
            zs, outs = [], []
            for e in range(N_EXPERTS):
                z = np.tanh(h @ p["exp_w1"][e] + p["exp_b1"][e])      # (B, H)
                o = z @ p["exp_w2"][e] + p["exp_b2"][e]               # (B, 2)
                zs.append(z)
                outs.append(o)
            pred = np.zeros_like(yb)
            for e in range(N_EXPERTS):
                pred += g[:, e:e + 1] * outs[e]
            # ── loss ──
            mse = np.mean((pred - yb) ** 2)
            balance = 1e-3 * float(np.mean(g * np.log(g + 1e-9)))
            loss = mse + balance
            # ── backprop (clipped) ──
            dpred = 2.0 * (pred - yb) / xb.shape[0]                   # (B, 2)
            D = np.zeros_like(g)                                      # Σ_k dpred·out_e
            for e in range(N_EXPERTS):
                D[:, e] = (dpred * outs[e]).sum(axis=1)
            dgate = g * (D - (g * D).sum(axis=1, keepdims=True))
            dgate += 1e-3 * g * (np.log(g + 1e-9) + 1.0)
            dh = dgate @ p["gate_w"].T
            g_w1, g_b1, g_w2, g_b2 = [], [], [], []
            for e in range(N_EXPERTS):
                dout = g[:, e:e + 1] * dpred                          # (B, 2)
                dz = (dout @ p["exp_w2"][e].T) * (1.0 - zs[e] * zs[e])  # (B, H)
                g_w2.append(zs[e].T @ dout)
                g_b2.append(dout.sum(axis=0))
                g_w1.append(h.T @ dz)
                g_b1.append(dz.sum(axis=0))
                dh += dz @ p["exp_w1"][e].T
            _step("exp_w2", np.stack(g_w2))
            _step("exp_b2", np.stack(g_b2))
            _step("exp_w1", np.stack(g_w1))
            _step("exp_b1", np.stack(g_b1))
            dh *= (1.0 - h * h)
            _step("gate_w", h.T @ dgate)
            _step("gate_b", dgate.sum(axis=0))
            _step("pre_w", xb.T @ dh)
            _step("pre_b", dh.sum(axis=0))
            # Divergence guard: never propagate non-finite params
            if not np.isfinite(p["pre_w"]).all():
                p = init_params()
        if progress:
            progress(epoch + 1, epochs)
    return p, time.time() - t0


# ── Weight cache ──

def cache_path():
    base = os.environ.get("HELLFORGE_HOME") or os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base, ".fent_cache", "humanize_weights.npz")


def load_or_train(force_retrain=False, progress=None):
    """Load cached weights, or train once and cache. Returns params dict."""
    path = cache_path()
    if not force_retrain and os.path.exists(path):
        try:
            data = np.load(path)
            p = {k: data[k] for k in data.files}
            return p, 0.0
        except Exception:
            pass
    p, dt = train(progress=progress)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        np.savez(path, **p)
    except Exception:
        pass
    return p, dt
