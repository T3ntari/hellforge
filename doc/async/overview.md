**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [lure-async](lure-async.md) | [radical-async](radical-async.md)

## Async Compile Pipeline

Compilation can run asynchronously over batches of sources. The async
stack is layered:

1. **LURE async engine** — a pool of LuaRuntimes (one per thread) for
   parallel compilation of independent sources (requires `lupa`)
2. **Python `ThreadPoolExecutor` fallback** — used when LURE is
   unavailable (the standalone async plugin of the early alpha was
   removed; the thread pool is now part of the core)

The engine is selected at runtime; `lure status` shows which one is
active and the worker count.

### Pipeline stages

- Parse + event generation per source (async, pooled)
- Export/rendering stays synchronous

### Testing

`lure async` benchmarks the async batch path against synchronous
compilation over several multi-thousand-line sources — see
[LURE async](lure-async.md).

---

**HELLFORGE OS v0.1.14.41-beta** — async compile