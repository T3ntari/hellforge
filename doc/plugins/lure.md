# **HELLFORGE v1.0.0.0 ALPHA — lure: LuaJIT Accelerator**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**lure** integrates LuaJIT as the high-speed scripting backend for HELLFORGE. It embeds a Lua 5.1 VM with the FFI library enabled, allowing Piano DSL scripts to call C functions directly without bindings.

## Batch Parsing

lure pre-compiles groups of related DSL files into a single Lua chunk, reducing parse overhead. Batch size is adaptive based on file count and available memory.

## Async Engine

lure maintains a dedicated Lua coroutine scheduler for asynchronous operations:

- `async http.get(url)` — non-blocking HTTP requests via libcurl
- `async fs.read(path)` — overlapped I/O on Windows, `io_uring` on Linux
- `async gpu.launch(shader)` — non-blocking GPU dispatch via radical

Coroutines yield on I/O and resume on completion, all within a single OS thread.

## Evaluator Priority 10

As the highest-priority evaluator, lure runs first during AST evaluation. It intercepts all DSL nodes tagged `@lua` or `@async` and executes them directly in the LuaJIT VM, bypassing the slower interpreter path.

---

**API Reference:** `#include <lure/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — lure: LuaJIT Accelerator**
