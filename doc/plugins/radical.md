# **HELLFORGE v1.0.0.0 ALPHA — radical: GPU Shader Math Core**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [fentclient](fentclient.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

The **radical** plugin is the GPU Shader Math Core of HELLFORGE. It transforms Piano DSL AST nodes into GLSL shader source code and manages the GPU compute runtime across multiple vendors.

## AST-to-GLSL Compilation

radical walks the compiled AST and emits GLSL 4.60-compatible source for vertex, fragment, and compute shaders. Key transformations:

| DSL Construct | GLSL Output |
|---------------|-------------|
| `kernel`      | `#version 460 core` + `layout(local_size_x=...)` compute shader |
| `parallel for`| `for` loop with `uint idx = gl_GlobalInvocationID.x` |
| `float4`      | `vec4` |
| `mat4`        | `mat4` |
| `dot(a,b)`    | `dot(a,b)` |

## Compute Runtime

radical provides a hardware abstraction layer for executing compute shaders:

- Dynamic shader compilation and caching
- Automatic work-group sizing based on GPU capabilities
- Asynchronous dispatch with fence synchronization
- Profiling hooks for per-shader timing

## Multi-GPU Switching

radical enumerates all available GPUs and supports explicit device selection at the DSL level via `@gpu(index)`. It manages per-device memory contexts and can split workloads across GPUs.

## VRAM Limits

radical tracks available VRAM per device and enforces allocation caps. When a GPU is within 10% of its VRAM limit, radical falls back to the next available device or stages data through system memory with automatic paging.

---

**API Reference:** `#include <radical/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — radical: GPU Shader Math Core**
