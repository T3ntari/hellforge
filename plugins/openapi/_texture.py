"""OPENapi TextureAPI — 2D/3D/cubemap textures, sampler state, mipmaps."""

import numpy as np


class TextureAPI:
    """Texture creation, binding, sampler management."""

    def __init__(self, context):
        self.ctx = context
        self._samplers = {}

    def create_2d(self, width, height, data=None, internal_format=None, min_filter=None, mag_filter=None, wrap=None):
        """Create a 2D texture. Returns texture_id."""
        from OpenGL.GL import (
            glGenTextures, glBindTexture, glTexImage2D, glTexParameteri,
            GL_TEXTURE_2D, GL_RGBA, GL_RGBA8, GL_UNSIGNED_BYTE,
            GL_LINEAR, GL_NEAREST, GL_REPEAT, GL_CLAMP_TO_EDGE,
            GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
            GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T,
        )
        if internal_format is None:
            from OpenGL.GL import GL_RGBA8
            internal_format = GL_RGBA8
        min_filter = min_filter or GL_LINEAR
        mag_filter = mag_filter or GL_LINEAR
        wrap = wrap or GL_REPEAT

        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tid)

        if data is not None:
            arr = np.array(data, dtype=np.uint8)
            glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, arr.ctypes.data)
        else:
            glTexImage2D(GL_TEXTURE_2D, 0, internal_format, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filter)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap)
        return tid

    def create_cubemap(self, face_data, width, height):
        """Create a cubemap from 6 face images."""
        from OpenGL.GL import (
            glGenTextures, glBindTexture, glTexImage2D, glTexParameteri,
            GL_TEXTURE_CUBE_MAP, GL_TEXTURE_CUBE_MAP_POSITIVE_X,
            GL_RGBA, GL_RGBA8, GL_UNSIGNED_BYTE,
            GL_LINEAR, GL_LINEAR_MIPMAP_LINEAR,
            GL_CLAMP_TO_EDGE, GL_TEXTURE_MIN_FILTER, GL_TEXTURE_MAG_FILTER,
            GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_WRAP_R,
            GL_TEXTURE_CUBE_MAP_SEAMLESS,
        )
        tid = glGenTextures(1)
        glBindTexture(GL_TEXTURE_CUBE_MAP, tid)
        for i, data in enumerate(face_data[:6]):
            arr = np.array(data, dtype=np.uint8)
            glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X + i, 0, GL_RGBA8, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, arr.ctypes.data)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_CUBE_MAP, GL_TEXTURE_WRAP_R, GL_CLAMP_TO_EDGE)
        return tid

    def bind(self, texture_id, unit=0):
        from OpenGL.GL import (
            glActiveTexture,
            glBindTexture,
            GL_TEXTURE0,
            GL_TEXTURE_2D,
        )
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, texture_id)

    def generate_mipmaps(self, texture_id):
        from OpenGL.GL import (
            glGenerateMipmap,
            GL_TEXTURE_2D,
        )
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glGenerateMipmap(GL_TEXTURE_2D)

    def delete(self, texture_id):
        from OpenGL.GL import glDeleteTextures
        glDeleteTextures(1, [texture_id])
