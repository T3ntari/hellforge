**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [radical-gpu](radical-gpu.md) | [opengl-api](opengl-api.md) | [vulkan-api](vulkan-api.md) | [tensor-cores](tensor-cores.md) | [shader-compilation](shader-compilation.md)

## Radical Compute Pipeline

Radical (v1.0.0) is the GPU shader math core: it compiles E math ASTs
into GLSL compute shaders and executes them on GPU shader cores.

### Pipeline

1. The E math AST for an expression is analyzed
2. GLSL compute shader source is generated
3. The shader is compiled and cached (`shader_cache`)
4. The compute dispatch runs with the selected GPU
5. Results feed back into the expression result (fallback: LURE → Python)

### Evaluator registration

Radical registers a math evaluator at **priority 5** — above LURE (10),
below TensorSHARP (3), always with the Python evaluator (100) as the
floor. `radical info` shows the chain.

### Multi-GPU & VRAM

- `radical gpu` — show the active GPU; `radical gpu list` enumerates all
  GPUs (index, vendor, type, VRAM, API support); `radical gpu <index>`
  switches (context re-init needs a shell restart)
- `radical vram <MB>` — cap VRAM; `radical vram off` removes the cap
- `radical status` reports GPU type, OpenGL/GLSL versions, compute
  capability, shaders compiled and expressions evaluated

### Shader cache

`radical shaders` shows the compiled-shader cache (count, KB, previews).
Cache lookups are source-hash keyed; see
[Shader Compilation](shader-compilation.md).

---

**HELLFORGE OS v0.1.14.41-beta** — Radical compute