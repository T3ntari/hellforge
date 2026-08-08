# **HELLFORGE v1.0.0.0 ALPHA — openapi: OpenGL Graphics API**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [fentclient](fentclient.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**openapi** wraps modern OpenGL (4.6 core profile) into six sub-APIs accessible from Piano DSL. Each sub-API maps to a dedicated namespace.

## Sub-APIs

### Context (`openapi.context`)

Manages the OpenGL context lifecycle: creation, destruction, thread binding, and debug message callbacks. Supports multiple contexts for offscreen rendering.

### Shader (`openapi.shader`)

Shader compilation, program linking, uniform/SSBO binding, and SPIR-V cross-compilation from radical-generated GLSL. Reflection queries for uniforms and buffer blocks.

### Buffer (`openapi.buffer`)

GPU buffer allocation (immutable, mapped, persistent), upload/download, bindless buffers via `ARB_bindless_texture`, and buffer storage barriers.

### Texture (`openapi.texture`)

Texture creation (2D, 3D, cube, array, multisample), mipmap generation, image load/store, and bindless texture handles. Supports all sized internal formats.

### Render (`openapi.render`)

Framebuffer objects, render passes, draw calls (indirect, instanced, indexed), query objects, and transform feedback. Compatible with radical-generated geometry shaders.

### Window (`openapi.window`)

Window creation via GLFW, input polling (keyboard, mouse, gamepad), vsync control, and swap chain management. Headless mode available for server-side rendering.

---

**API Reference:** `#include <openapi/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — openapi: OpenGL Graphics API**
