**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](gpu/overview.md) | [radical-gpu](gpu/radical-gpu.md) | [opengl-api](gpu/opengl-api.md) | [vulkan-api](gpu/vulkan-api.md) | [tensor-cores](gpu/tensor-cores.md) | [shader-compilation](gpu/shader-compilation.md)

## Shader Compilation Pipeline

### GLSL to SPIR-V

Generated GLSL shaders are compiled to SPIR-V using the compiler cache.

1. Source GLSL is hashed (SHA-512) for cache lookup
2. Cache hit: load cached SPIR-V binary
3. Cache miss: compile via `glslang` or `shaderc`
4. SPIR-V is validated and stored in cache
5. Compiled shader is dispatched to GPU

### AST to GLSL Codegen

The Radical codegen translates Piano DSL AST nodes into GLSL:

- Vector operations map to GLSL `vec` types
- Audio DSP graphs become compute shader invocations
- Control flow is preserved with barrier synchronization
- Buffer bindings are auto-assigned and tracked

### Caching

Shader cache location: `~/.piano/cache/shaders/`. Cache entries expire after 7 days or on compiler version change.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**