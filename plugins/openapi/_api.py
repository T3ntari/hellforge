"""OPENapi OpenGLAPI — top-level API exposing all GL primitives.
Game engines import this and use: api.shader, api.buffer, api.texture, api.render, api.window."""

import os


class OpenGLAPI:
    """Low-level OpenGL API. All sub-APIs are accessed as attributes."""

    def __init__(self, context):
        self.context = context
        self.available = context.available
        if not self.available:
            return

        from ._shader import ShaderAPI
        from ._buffer import BufferAPI
        from ._texture import TextureAPI
        from ._render import RenderAPI
        from ._window import WindowAPI

        self.shader = ShaderAPI(context)
        self.buffer = BufferAPI(context)
        self.texture = TextureAPI(context)
        self.render = RenderAPI(context, self.buffer, self.shader)
        self.window = WindowAPI(context)

    def begin_frame(self):
        """Begin a new frame. Returns False if window should close."""
        self.context.poll_events()
        if self.context.should_close():
            return False
        from OpenGL.GL import (
            glClear,
            glClearColor,
            GL_COLOR_BUFFER_BIT,
            GL_DEPTH_BUFFER_BIT,
        )
        glClearColor(0.08, 0.08, 0.12, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        return True

    def end_frame(self):
        """End current frame, swap buffers."""
        self.context.swap_buffers()

    def shutdown(self):
        """Clean up all GPU resources."""
        self.context._cleanup()

    @property
    def gl(self):
        """Direct access to OpenGL.GL module for advanced users."""
        from OpenGL import GL as gl
        return gl
