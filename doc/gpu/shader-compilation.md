**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [radical-gpu](radical-gpu.md) | [opengl-api](opengl-api.md) | [vulkan-api](vulkan-api.md) | [tensor-cores](tensor-cores.md) | [shader-compilation](shader-compilation.md)

## Shader Compilation Pipeline

### AST → GLSL

Radical compiles E math ASTs into GLSL compute shader source:

- Expression nodes map to GLSL expressions over the compute grid
- Shader source is generated per expression AST
- Precision follows the evaluator chain (TF32/FP16 on Tensor Cores,
  FP32 fallback)

### Compilation & caching

1. Source GLSL is hashed for cache lookup
2. Cache hit → load the cached shader
3. Cache miss → compile, then store in the shader cache
4. Compiled shader is dispatched to the GPU

`radical shaders` reports cache stats (count, KB) with previews of recent
entries.

### Dispatch

Dispatch happens inside Radical's compute runtime with the GPU selected
by the K-rip hypervisor (`krip gpu <auto|list|all|0,1|...>`), capped by
`radical vram <MB>` when set.

---

**HELLFORGE OS v0.1.14.41-beta** — shader pipeline