**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [radical-gpu](radical-gpu.md) | [opengl-api](opengl-api.md) | [vulkan-api](vulkan-api.md) | [tensor-cores](tensor-cores.md) | [shader-compilation](shader-compilation.md)

## GPU Acceleration Overview

HELLFORGE's GPU layer is driven by the **K-rip hypervisor** (GPU
selection + default engine) on top of the Radical / TensorSHARP /
OPENapi / Vulkanizer driver plugins.

### GPU selection (K-rip)

The hypervisor owns GPU allocation — every process it spawns inherits it:

```
krip gpu list         # show detected GPUs
krip gpu auto         # detect at runtime (default)
krip gpu all          # use every GPU
krip gpu 0,1          # GPUs 0 and 1 (multi-GPU) — sets CUDA_VISIBLE_DEVICES
krip gpu 2 3          # same, space-separated
krip engine vulkan    # default graphics engine (vulkan|opengl)
krip vulkanrt on      # Vulkan runtime support
krip tensor on        # tensor support (on|off|auto)
krip status           # current allocation
```

Persisted in `krip.json` at the project root. See
[K-rip commands](../commands/krip-commands.md).

### Driver plugins

- **Radical** — GPU shader math: E math ASTs compiled to GLSL compute
  shaders; per-plugin GPU switching (`radical gpu <index>`) and VRAM caps
  (`radical vram <MB>`)
- **TensorSHARP** — NVIDIA Tensor Core acceleration (CuPy, TF32/FP16),
  evaluator priority 3
- **OPENapi** — low-level OpenGL API (context, shaders, buffers,
  textures, render, window)
- **Vulkanizer** — low-level Vulkan API (instance, pipelines, commands,
  ray-tracing detection, upscaling)

### Feature Matrix

| Feature | OPENapi | Vulkanizer |
|---|---|---|
| Compute shaders | Yes | Yes |
| Ray tracing | Extension-detectable | `VK_KHR_ray_tracing` detection |
| Tensor Cores | No | Upscaling can use them |
| Upscaling | No | Custom temporal upscaling |

### Fallback chain

Math evaluation falls back TensorSHARP → Radical → LURE → Python, so
everything still works on machines with no GPU.

---

**HELLFORGE OS v0.1.14.41-beta** — hypervisor-allocated GPU