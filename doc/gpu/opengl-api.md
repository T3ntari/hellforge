**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](gpu/overview.md) | [radical-gpu](gpu/radical-gpu.md) | [opengl-api](gpu/opengl-api.md) | [vulkan-api](gpu/vulkan-api.md) | [tensor-cores](gpu/tensor-cores.md) | [shader-compilation](gpu/shader-compilation.md)

## OPENapi — OpenGL Primitives

OPENapi provides a comprehensive set of OpenGL 4.6 primitives designed for game engine integration with Piano DSL.

### Features

- Vertex buffer objects (VBO) with streaming updates
- Uniform buffer objects (UBO) for per-frame data
- Shader storage buffer objects (SSBO) for compute
- Compute shader dispatch with barrier management
- Debug markers and GPU timer queries

### Example

```piano
openapi.buffer.vertex(positions, layout = "vec3")
openapi.shader.compute("shaders/audio_dsp.comp")
openapi.dispatch(128, 128, 1)
```

### Integration

OPENapi is designed to sit alongside existing OpenGL rendering code. It does not assume ownership of the GL context and can be used with any framework (SDL, GLFW, Qt).

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**