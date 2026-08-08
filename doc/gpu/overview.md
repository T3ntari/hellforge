**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](gpu/overview.md) | [radical-gpu](gpu/radical-gpu.md) | [opengl-api](gpu/opengl-api.md) | [vulkan-api](gpu/vulkan-api.md) | [tensor-cores](gpu/tensor-cores.md) | [shader-compilation](gpu/shader-compilation.md)

## GPU Acceleration Overview

The Piano DSL runtime includes a comprehensive GPU acceleration layer capable of targeting OpenGL 4.6+ and Vulkan 1.3+ backends.

### Multi-GPU Detection

At startup, the runtime enumerates all available GPU devices:

```
piano gpu list
```

Output includes device name, driver version, VRAM, compute capability, and supported features (ray tracing, tensor cores, etc.).

### Backend Selection

- **OPENapi** — OpenGL 4.6+ primitives for game engine integration
- **Vulkanizer** — Vulkan compute, ray tracing, and upscaling
- Auto-selection prefers Vulkan when available

### Feature Matrix

| Feature | OPENapi | Vulkanizer |
|---|---|---|
| Compute shaders | Yes | Yes |
| Ray tracing | Limited | Full |
| Tensor Cores | No | Yes |
| Upscaling | No | Yes |
| Multi-GPU | No | Yes |

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**