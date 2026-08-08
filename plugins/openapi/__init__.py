"""OPENapi v1.0.0 — Low-level OpenGL Graphics API.
Not a game engine. Provides the raw OpenGL building blocks that game engines
and rendering pipelines are built on top of.

Core primitives:
- Context: GLFW window, OpenGL version, extensions, debug callback
- Shader: compile/link GLSL programs, uniform reflection
- Buffer: VBO, EBO, VAO, SSBO, UBO allocation + upload
- Texture: 2D, 3D, cubemap, sampler state, mipmaps
- Render: pipeline state, draw calls, framebuffer objects, swapchain
- Window: input callbacks, cursor modes, fullscreen toggling

Third-party modders build game engines ON TOP of this API.
Example engine in examples/opengl_engine.py

Install: pip install PyOpenGL glfw numpy"""

VERSION = "1.0.0"
author = "Tentari"
description = "Low-level OpenGL Graphics API — context, shaders, buffers, textures, rendering pipeline"

_api = None


def register(api):
    api.add_boot_step(f"OPENapi v{VERSION}", "loading")
    global _api

    # Require Radical for GPU detection + context
    api.require("Radical")

    try:
        from ._context import GLContext
        ctx = GLContext()
        if ctx.available:
            from ._api import OpenGLAPI
            _api = OpenGLAPI(ctx)
            api.set_config("openapi_available", True)
            api.add_command("openapi", _cmd, "OPENapi: openapi status|info|extensions")
            api.add_boot_step(f"OPENapi: OpenGL {ctx.gl_version} active ({ctx.gpu_name})", "done")
        else:
            api.set_config("openapi_available", False)
            api.add_boot_step(f"OPENapi: unavailable ({ctx.diagnostic})", "skip")
            api.add_command("openapi", _cmd, "OPENapi: openapi status")
    except Exception as e:
        api.set_config("openapi_available", False)
        api.add_boot_step(f"OPENapi: init failed ({e})", "skip")
        api.add_command("openapi", _cmd, "OPENapi: openapi status")


def get_api():
    """Get the OpenGL API instance. Returns OpenGLAPI or None."""
    return _api


def _cmd(args):
    if not args or args[0] == "status":
        if _api and _api.available:
            ctx = _api.context
            print(f"  OPENapi v{VERSION} — OpenGL Graphics API")
            print(f"  GPU: {ctx.gpu_name}")
            print(f"  OpenGL: {ctx.gl_version}")
            print(f"  GLSL: {ctx.glsl_version}")
            print(f"  Extensions: {len(ctx.extensions)}")
            print(f"  Window: {ctx.width}x{ctx.height}")
            print(f"  VSync: {ctx.vsync}")
            print(f"  Game engines can be built on this API")
        else:
            print(f"  OPENapi v{VERSION}")
            print(f"  Status: inactive")
            print(f"  Install: pip install PyOpenGL glfw")

    elif args[0] == "extensions":
        if _api and _api.available:
            exts = _api.context.extensions
            print(f"  OpenGL Extensions ({len(exts)}):")
            wanted = ["GL_ARB_compute_shader", "GL_ARB_shader_storage_buffer_object",
                      "GL_ARB_direct_state_access", "GL_KHR_debug",
                      "GL_NV_ray_tracing", "GL_AMD_ray_tracing",
                      "GL_ARB_sparse_texture", "GL_ARB_bindless_texture"]
            for w in wanted:
                print(f"    {w}: {'yes' if w in exts else 'no'}")
        else:
            print(f"  No OpenGL context")

    elif args[0] == "info":
        print(f"  OPENapi v{VERSION} — Low-level OpenGL Graphics API")
        print(f"  Provides raw OpenGL primitives for building game engines:")
        print(f"    - GLContext: window, extensions, debug")
        print(f"    - ShaderAPI: GLSL compile/link, uniforms")
        print(f"    - BufferAPI: VBO, VAO, SSBO, UBO")
        print(f"    - TextureAPI: 2D/3D/cubemap, samplers, mipmaps")
        print(f"    - RenderAPI: pipeline state, draw calls, FBO, swapchain")
        print(f"    - WindowAPI: input callbacks, cursor, fullscreen")
        if _api and _api.available:
            print(f"  API status: active — build your engine on top!")

    else:
        print(f"  Usage: openapi status|extensions|info")
