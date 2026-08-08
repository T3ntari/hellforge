**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](async/overview.md) | [lure-async](async/lure-async.md) | [radical-async](async/radical-async.md)

## Async Compile Pipeline

The Piano DSL compiler uses a multi-tier asynchronous pipeline to maximize throughput during compilation.

### Fallback Chain

1. **LURE** — Primary async engine. Per-thread LuaRuntimes for parallel compilation.
2. **Python ThreadPoolExecutor** — fallback when LURE is unavailable.
3. **Radical** — GPU shader compilation dispatched asynchronously to the GPU queue.

Each tier can operate independently. The compiler selects the best available engine at startup, with LURE preferred on systems with Lua support.

### Pipeline Stages

- Parse (async)
- Type-check (async)
- IR generation (async)
- Optimization (async)
- Code generation (async)
- Signing (sync, enforced)
- Output (sync)

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**