**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [lure-async](lure-async.md) | [radical-async](radical-async.md)

## LURE Async Engine

LURE (v3.0.0) ships an async compile engine: a pool of LuaRuntimes, one
per thread, for parallel compilation of independent compilation units —
the hot path (line parsing, event math) runs in LuaJIT while Python
manages state.

### Architecture

- Per-thread LuaRuntimes with isolated state
- Worker pool sized at runtime (`lure status` shows the count)
- Graceful fallback to the **Python `ThreadPoolExecutor`** when `lupa`
  is unavailable (or the engine is skipped with a diagnostic at boot)

### Entry points

- `ep_compiler/async_compile.py` — `async_compile_batch(sources)`
- `lure async` — benchmark async vs synchronous compilation

### Benefits

- Zero-GIL parallelism on the native (LuaJIT) hot path
- Low overhead context switching
- Deterministic fallback: LURE → Python pool, never a silent stall

---

**HELLFORGE OS v0.1.14.41-beta** — LURE async