# LURE — LuaJIT Runtime Accelerator

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [lure](lure.md) | [portbaby](portbaby.md) | [commands](../commands/lure-commands.md)

---

## Overview

**LURE v3.0.0** (author Tentari) is the Lua Runtime Accelerator for E. It
accelerates the compilation hot path using LuaJIT: fast string parsing and
bulk event math live in LURE while Python manages state, cursors, project
resolution and error handling. Requires `pip install lupa` (bundles
LuaJIT 5.3+) and **gracefully falls back to Python** when unavailable.

## What it accelerates

- Batch line parsing (`parse_lines_batch`) and single-line parsing
- Scale quantization
- MIDI tick calculation / event math
- Math expression evaluation — registered as a math evaluator at
  **priority 10**; the Python fallback evaluator is always registered at
  priority 100

## Async engine

A per-thread pool of LuaRuntimes provides non-blocking compile via
`ep_compiler.async_compile` (`async_compile_batch`); the Python
`ThreadPoolExecutor` fallback covers platforms without lupa. See
[Async docs](../async/lure-async.md).

## Commands

`lure status|benchmark|async` — see [LURE commands](../commands/lure-commands.md).
