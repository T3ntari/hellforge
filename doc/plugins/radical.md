# Radical — GPU Shader Math Core

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [commands](../commands/radical-commands.md)

---

## Overview

**radical v1.0.0** (author Tentari) is the GPU Shader Math Core. It
compiles E math ASTs into **GLSL compute shaders** and executes them on GPU
shader cores, registered as a math evaluator at **priority 5** (above
LURE's 10). Fallback chain: Radical → LURE → Python. Requires
`pip install PyOpenGL glfw` — gracefully unavailable when missing.

## Pipeline

1. The E math AST is analyzed
2. GLSL compute shader source is generated
3. The shader is compiled and cached (`shader_cache`)
4. The compute dispatch runs; results feed back into the expression result

## Multi-GPU & VRAM

- Enumerates all GPUs at startup; `radical gpu <index>` switches the
  active device (context re-init requires a shell restart), `radical gpu
  list` shows the table.
- `radical vram <MB>` caps VRAM usage; `radical vram off` disables the
  cap.

## Commands

`radical status|benchmark|shaders|gpu|vram|info` — see
[Radical commands](../commands/radical-commands.md).

## Dependencies

Used by OPENapi, Vulkanizer, EAudio and TensorSHARP (`api.require("Radical")`).
