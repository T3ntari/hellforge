**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](gpu/overview.md) | [radical-gpu](gpu/radical-gpu.md) | [opengl-api](gpu/opengl-api.md) | [vulkan-api](gpu/vulkan-api.md) | [tensor-cores](gpu/tensor-cores.md) | [shader-compilation](gpu/shader-compilation.md)

## Vulkanizer — Vulkan Compute + Ray Tracing + Upscale

Vulkanizer is the Vulkan 1.3 backend for Piano DSL, providing the full GPU compute, ray tracing, and upscaling pipeline.

### Compute

- Vulkan compute pipelines generated from Radical kernel expressions
- Push constants for small uniform data
- Descriptor set management with automatic layout inference
- Timeline semaphore synchronization

### Ray Tracing

- Acceleration structure building from Piano DSL geometry descriptions
- Ray tracing pipelines with any-hit, closest-hit, and miss shaders
- Integration with audio spatialization for sound propagation tracing

### Upscaling

- Built-in temporal upscaling for audio visualization workloads
- Integration with TensorSHARP for AI-based upscaling
- Frame interpolation for smooth parameter animation

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**