**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](gpu/overview.md) | [radical-gpu](gpu/radical-gpu.md) | [opengl-api](gpu/opengl-api.md) | [vulkan-api](gpu/vulkan-api.md) | [tensor-cores](gpu/tensor-cores.md) | [shader-compilation](gpu/shader-compilation.md)

## Radical Compute Pipeline

Radical is the GPU compute engine within Piano DSL. It generates GLSL compute shaders from high-level Piano DSL kernel expressions.

### Pipeline

1. Piano DSL kernel expression is parsed
2. AST is analyzed for parallelizability
3. GLSL compute shader code is generated
4. Shader is compiled to SPIR-V via the compiler cache
5. Compute dispatch is executed with optimal work group sizes
6. Results are read back or consumed in-place

### GLSL Codegen

The codegen translates Piano DSL vector/matrix operations into GLSL WGSL-compatible syntax. It automatically handles:

- Work group size selection based on GPU capabilities
- Shared memory allocation
- Barrier insertion for cross-invocation synchronization
- Precision selection (TF32, FP16, INT8)

### Dispatch

```
piano compute --kernel my_kernel --grid 256,256,1
```

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**