# OPENapi — Low-Level OpenGL Graphics API

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [commands](../commands/openapi-commands.md)

---

## Overview

**OPENapi v1.0.0** (author Tentari) is a low-level **OpenGL** graphics API
— not a game engine. It provides the raw building blocks that game engines
and rendering pipelines are built on top of. Requires Radical for GPU
detection; `pip install PyOpenGL glfw numpy`.

## Core primitives

- **Context** — GLFW window, OpenGL version, extensions, debug callback
- **Shader** — compile/link GLSL programs, uniform reflection
- **Buffer** — VBO, EBO, VAO, SSBO, UBO allocation + upload
- **Texture** — 2D, 3D, cubemap, sampler state, mipmaps
- **Render** — pipeline state, draw calls, framebuffer objects, swapchain
- **Window** — input callbacks, cursor modes, fullscreen toggling

Example engine: `examples/opengl_engine.py`.

## Commands

`openapi status|extensions|info` — see
[OPENapi commands](../commands/openapi-commands.md).
