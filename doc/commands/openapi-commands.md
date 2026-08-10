# HELLFORGE — OPENapi Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [openapi-commands](openapi-commands.md)

The **openapi** plugin (v1.0.0) is a low-level **OpenGL graphics API** —
context, shaders, buffers, textures, rendering pipeline — not an AI
endpoint client. It depends on Radical for GPU detection.

## openapi status
**Syntax:** `openapi status`
**Description:** Show the OpenGL context: GPU name, OpenGL/GLSL versions, extension count, window size, VSync — or "inactive" (`pip install PyOpenGL glfw`).
**Example:** `openapi status`

## openapi extensions
**Syntax:** `openapi extensions`
**Description:** Report whether key OpenGL extensions are present (compute shader, SSBO, DSA, KHR_debug, ray tracing, sparse/bindless textures).
**Example:** `openapi extensions`

## openapi info
**Syntax:** `openapi info`
**Description:** Describe the sub-APIs: GLContext (window, extensions, debug), ShaderAPI (GLSL compile/link, uniforms), buffer/texture/render/window primitives.
**Example:** `openapi info`

---

**Plugin:** openapi · see [OPENapi plugin page](../plugins/openapi.md) and [GPU docs](../gpu/opengl-api.md)
