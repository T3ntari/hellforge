**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](async/overview.md) | [lure-async](async/lure-async.md) | [radical-async](async/radical-async.md)

## LURE Async Engine

LURE is the primary asynchronous execution engine for the Piano DSL compiler. It maintains a pool of LuaRuntimes, one per thread, enabling parallel compilation of independent compilation units.

### Architecture

- Thread-local LuaRuntimes with isolated state
- Job queue with work-stealing scheduler
- Lock-free communication channels between runtimes
- Shared immutable AST cache

### Benefits

- Zero-GIL parallelism (pure native code paths)
- Low overhead context switching
- Direct integration with Lua-based pipeline plugins
- Graceful degradation to the Python pool on unsupported platforms

### Configuration

```
piano config set async.engine lure
piano config set lure.threads auto
```

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**