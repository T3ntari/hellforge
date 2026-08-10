# HELLFORGE — LURE Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [lure-commands](lure-commands.md)

The **lure** plugin (v3.0.0) is the LuaJIT runtime accelerator — fast
batch parsing and bulk event math on the compile hot path, plus an async
compile engine. Requires `pip install lupa`; falls back to Python
otherwise.

## lure status
**Syntax:** `lure status`
**Description:** Show the sync engine state (lines parsed, events processed) and the async engine state (worker count).
**Example:** `lure status`

## lure benchmark
**Syntax:** `lure benchmark`
**Description:** Benchmark LURE vs the Python parser: batch machine-mode lines, mixed syntax, and the full compile pipeline — reports the speedup factor.
**Example:** `lure benchmark`

## lure async
**Syntax:** `lure async`
**Description:** Benchmark async batch compilation (`ep_compiler.async_compile`) against synchronous compilation over several multi-thousand-line sources.
**Example:** `lure async`

---

**Plugin:** lure · see [LURE plugin page](../plugins/lure.md) and [Async docs](../async/lure-async.md)
