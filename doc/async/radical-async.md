**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](async/overview.md) | [lure-async](async/lure-async.md) | [fentclient-async](async/fentclient-async.md) | [radical-async](async/radical-async.md)

## Radical Async GPU Compilation

The Radical engine offloads shader compilation and batch compute workloads to the GPU asynchronously.

### Capabilities

- GLSL to SPIR-V compilation on GPU compute queues
- Parallel AST-to-GLSL codegen for large shader forests
- Tensor Core accelerated matrix operations for DSP pipeline generation
- Non-blocking dispatch with CPU-side progress polling

### Workflow

1. AST nodes are batched into GPU work groups
2. GLSL codegen runs on CPU threads (LURE/FentClient) in parallel
3. Generated GLSL is dispatched to GPU for SPIR-V compilation
4. Compiled shaders are cached to disk
5. Callback fires when all shaders are ready

This approach keeps the CPU free for other pipeline stages while the GPU handles compilation.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**