**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [radical-gpu](radical-gpu.md) | [opengl-api](opengl-api.md) | [vulkan-api](vulkan-api.md) | [tensor-cores](tensor-cores.md) | [shader-compilation](shader-compilation.md)

## Vulkanizer — Vulkan Compute + Ray Tracing + Upscale

Vulkanizer (v1.0.0) is the low-level **Vulkan** graphics & compute API
driver — instance, pipelines, buffers, commands, ray tracing and custom
temporal upscaling. Requires Radical for GPU detection and the Vulkan SDK
(`pip install vulkan glfw`).

### Primitives

- **Instance** — Vulkan instance, physical device selection, logical
  device, queues
- **Pipeline** — compute/graphics pipelines, shader modules, descriptor
  sets, push constants
- **Buffer** — device-local, host-visible, staging, buffer barriers
- **Command** — command pools, command buffers, submit, sync (semaphores,
  fences)
- **RayTrace** — `VK_KHR_ray_tracing` capability detection
- **Upscale** — custom temporal upscaling via compute shaders + Tensor
  Cores

### Querying the driver

```
vulkanizer status     # GPU, Vulkan version, driver, compute queues, RT
vulkanizer devices    # physical devices
vulkanizer info       # sub-API summary
```

Example engine: `examples/vulkan_engine.py`.

### Engine selection

K-rip sets **Vulkan** as the default graphics engine
(`krip engine vulkan` — `opengl` switches the default); `krip vulkanrt`
toggles the Vulkan runtime layer. See
[GPU overview](overview.md).

---

**HELLFORGE OS v0.1.14.41-beta** — Vulkan API driver