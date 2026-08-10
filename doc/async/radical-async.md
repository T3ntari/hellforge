**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [lure-async](lure-async.md) | [radical-async](radical-async.md)

## GPU / Fallback Async Chain

This page documents the async *fallback* story on the GPU side. Note: the
standalone async plugin of the early alpha is **gone** — its role was
replaced by the Python thread pool fallback described below.

### The chain

1. **LURE async engine** — preferred when `lupa` is installed (LuaJIT
   pool, per-thread runtimes)
2. **Python `ThreadPoolExecutor`** — the universal fallback when LURE is
   unavailable; this path now ships in the core
3. **Radical / TensorSHARP** — GPU shader compilation and dispatch stay
   on the synchronous compile path (per-expression), not in the async
   batch pipeline

### GPU work remains synchronous

Radical compiles GLSL and dispatches compute synchronously per expression
(evaluator priority 5); the batch *parsing* pipeline is where the async
pool applies. Combined with the evaluator fallback (TensorSHARP →
Radical → LURE → Python), every configuration degrades gracefully.

---

**HELLFORGE OS v0.1.14.41-beta** — async fallback chain