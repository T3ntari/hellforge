**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [radical-gpu](radical-gpu.md) | [opengl-api](opengl-api.md) | [vulkan-api](vulkan-api.md) | [tensor-cores](tensor-cores.md) | [shader-compilation](shader-compilation.md)

## OPENapi — OpenGL Primitives

OPENapi (v1.0.0) is the low-level **OpenGL** graphics API driver — the raw
building blocks that game engines are built on top of. It requires Radical
for GPU detection (`pip install PyOpenGL glfw`).

### Primitives

- **Context** — GLFW window, OpenGL version, extensions, debug callback
- **Shader** — GLSL compile/link, uniform reflection
- **Buffer** — VBO, EBO, VAO, SSBO, UBO allocation + upload
- **Texture** — 2D/3D/cubemap, sampler state, mipmaps
- **Render** — pipeline state, draw calls, framebuffer objects, swapchain
- **Window** — input callbacks, cursor modes, fullscreen toggling

### Querying the driver

```
openapi status        # GPU, OpenGL/GLSL versions, extension count, vsync
openapi extensions    # key extensions: compute shader, SSBO, DSA,
                      # KHR_debug, ray tracing, sparse/bindless textures
openapi info          # sub-API summary
```

### Integration

OPENapi does not assume ownership of the GL context and can sit alongside
existing OpenGL code (SDL, GLFW, Qt). Example engine:
`examples/opengl_engine.py`.

---

**HELLFORGE OS v0.1.14.41-beta** — OpenGL API driver