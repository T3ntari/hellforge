"""OPENapi RenderAPI — pipeline state, draw calls, framebuffer objects, swapchain."""


class RenderAPI:
    """Rendering pipeline: state management, draw calls, framebuffers."""

    def __init__(self, context, buffer_api, shader_api):
        self.ctx = context
        self.buffer = buffer_api
        self.shader = shader_api

    def draw_arrays(self, mode, first, count):
        """Draw vertices: mode=GL_TRIANGLES, GL_LINES, GL_POINTS, etc."""
        from OpenGL.GL import glDrawArrays
        glDrawArrays(mode, first, count)

    def draw_elements(self, mode, count, indices_buffer=None):
        """Draw indexed geometry."""
        from OpenGL.GL import (
            glDrawElements,
            GL_UNSIGNED_INT,
        )
        glDrawElements(mode, count, GL_UNSIGNED_INT, None)

    def draw_instanced(self, mode, first, count, instance_count):
        """Draw instanced geometry."""
        from OpenGL.GL import glDrawArraysInstanced
        glDrawArraysInstanced(mode, first, count, instance_count)

    def set_viewport(self, x, y, w, h):
        from OpenGL.GL import glViewport
        glViewport(x, y, w, h)

    def set_depth_test(self, enabled=True):
        from OpenGL.GL import (
            glEnable,
            glDisable,
            GL_DEPTH_TEST,
        )
        if enabled:
            glEnable(GL_DEPTH_TEST)
        else:
            glDisable(GL_DEPTH_TEST)

    def set_blend(self, enabled=True):
        from OpenGL.GL import (
            glEnable,
            glDisable,
            glBlendFunc,
            GL_BLEND,
            GL_SRC_ALPHA,
            GL_ONE_MINUS_SRC_ALPHA,
        )
        if enabled:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        else:
            glDisable(GL_BLEND)

    def set_cull_face(self, enabled=True):
        from OpenGL.GL import (
            glEnable,
            glDisable,
            GL_CULL_FACE,
        )
        if enabled:
            glEnable(GL_CULL_FACE)
        else:
            glDisable(GL_CULL_FACE)

    def set_wireframe(self, enabled=False):
        from OpenGL.GL import (
            glPolygonMode,
            GL_FRONT_AND_BACK,
            GL_LINE,
            GL_FILL,
        )
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE if enabled else GL_FILL)

    def clear(self, color=(0.08, 0.08, 0.12, 1.0)):
        from OpenGL.GL import (
            glClear,
            glClearColor,
            GL_COLOR_BUFFER_BIT,
            GL_DEPTH_BUFFER_BIT,
        )
        glClearColor(*color)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def create_fbo(self, width, height):
        """Create a framebuffer object with color+depth attachments. Returns (fbo, color_tex, depth_tex)."""
        from OpenGL.GL import (
            glGenFramebuffers, glBindFramebuffer, glFramebufferTexture2D,
            glGenTextures, glBindTexture, glTexImage2D, glTexParameteri,
            glCheckFramebufferStatus, GL_FRAMEBUFFER, GL_FRAMEBUFFER_COMPLETE,
            GL_COLOR_ATTACHMENT0, GL_DEPTH_ATTACHMENT,
            GL_TEXTURE_2D, GL_RGBA8, GL_RGBA, GL_UNSIGNED_BYTE,
            GL_LINEAR, GL_DEPTH_COMPONENT24, GL_DEPTH_COMPONENT,
            GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
        )
        # Color attachment
        color_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, color_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Depth attachment
        depth_tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, depth_tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT24, width, height, 0, GL_DEPTH_COMPONENT, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Framebuffer
        fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, color_tex, 0)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, depth_tex, 0)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            raise RuntimeError("FBO incomplete")
        return fbo, color_tex, depth_tex

    def bind_fbo(self, fbo):
        from OpenGL.GL import (
            glBindFramebuffer,
            GL_FRAMEBUFFER,
        )
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)

    def bind_default_fbo(self):
        from OpenGL.GL import (
            glBindFramebuffer,
            GL_FRAMEBUFFER,
        )
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def delete_fbo(self, fbo):
        from OpenGL.GL import glDeleteFramebuffers
        glDeleteFramebuffers(1, [fbo])
