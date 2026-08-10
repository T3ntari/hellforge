# HELLFORGE — Radical Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [radical-commands](radical-commands.md)

The **radical** plugin (v1.0.0) is the GPU Shader Math Core: it compiles E
math ASTs into GLSL compute shaders and executes them on the GPU. It is
registered as a math evaluator at **priority 5** (after TensorSHARP's 3,
before LURE's 10) and falls back Radical → LURE → Python. Requires
`pip install PyOpenGL glfw`.

## radical status
**Syntax:** `radical status`
**Description:** Primary GPU, vendor, type, VRAM, OpenGL/GLSL versions, compute support, shaders compiled, expressions evaluated, plus a list of ALL detected GPUs and the API support matrix.
**Example:** `radical status`

## radical gpu
**Syntax:** `radical gpu [list|<index>]`
**Description:** Show the current GPU; `list` enumerates GPUs with index/vendor/type/VRAM; switching requires a shell restart to re-init the context.
**Example:** `radical gpu list`

## radical vram
**Syntax:** `radical vram [<MB>|off]`
**Description:** Show or set the VRAM allocation cap (0/off = unlimited).
**Example:** `radical vram 4096`

## radical benchmark
**Syntax:** `radical benchmark`
**Description:** GPU compute benchmark.
**Example:** `radical benchmark`

## radical shaders
**Syntax:** `radical shaders`
**Description:** Shader cache stats (count, KB) with a preview of recent entries.
**Example:** `radical shaders`

## radical info
**Syntax:** `radical info`
**Description:** Plugin summary: evaluator priority 5, AST→GLSL pipeline, fallback chain, multi-GPU switching and VRAM limit usage.
**Example:** `radical info`

---

**Plugin:** radical · see [Radical plugin page](../plugins/radical.md) and [GPU docs](../gpu/radical-gpu.md)
