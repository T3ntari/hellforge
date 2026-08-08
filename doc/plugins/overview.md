# **HELLFORGE v1.0.0.0 ALPHA — Plugin System Overview**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

HELLFORGE's plugin architecture provides a modular, extensible runtime for DSL compilation, GPU compute, graphics rendering, spatial audio, and scripting. Each plugin registers with the core engine through a unified plugin interface and participates in a deterministic boot chain.

## Boot Order

Plugins load in the following sequence:

1. **lure** — LuaJIT Accelerator (evaluator priority 10)
2. **radical** — GPU Shader Math Core (evaluator priority 9)
3. **tensorsharp** — Tensor Core acceleration (evaluator priority 8)
4. **openapi** — OpenGL Graphics API (evaluator priority 7)
5. **vulkanizer** — Vulkan API (evaluator priority 6)
6. **eaudio** — 3D Spatial Audio API (evaluator priority 5)
7. **talisman** — Audio culling & privacy (evaluator priority 4)
9. **portbaby** — Syntax version porting (evaluator priority 2)

## Dependency Chain

- **lure** has no dependencies and loads first.
- **radical** depends on **lure** for scripted shader composition.
- **tensorsharp** depends on **radical** for GPU context.
- **openapi** depends on **radical** and **tensorsharp**.
- **vulkanizer** depends on **radical**.
- **eaudio** is independent of GPU plugins.
- **talisman** depends on **eaudio**.
- **portbaby** depends on all syntax-aware plugins.

## Evaluator Priorities

Each plugin registers a DSL evaluator with the core priority scheduler. Higher numeric priority runs first during AST evaluation:

| Priority | Plugin     |
|----------|------------|
| 10       | lure       |
| 9        | radical    |
| 8        | tensorsharp|
| 7        | openapi    |
| 6        | vulkanizer |
| 5        | eaudio     |
| 4        | talisman   |
| 2        | portbaby   |

---

**HELLFORGE v1.0.0.0 ALPHA — Plugin System Overview**
