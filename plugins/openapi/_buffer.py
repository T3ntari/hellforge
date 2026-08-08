"""OPENapi BufferAPI — VBO, VAO, EBO, SSBO, UBO management."""


class BufferAPI:
    """Vertex buffers, index buffers, storage buffers, uniform buffers."""

    def __init__(self, context):
        self.ctx = context
        self._vaos = {}

    def create_vao(self, name="vao"):
        """Create a Vertex Array Object."""
        from OpenGL.GL import glGenVertexArrays
        vao = glGenVertexArrays(1)
        self._vaos[name] = vao
        return vao

    def bind_vao(self, vao):
        from OpenGL.GL import glBindVertexArray
        glBindVertexArray(vao)

    def create_vbo(self, data, usage=None):
        """Create a Vertex Buffer Object from float data.
        usage: GL_STATIC_DRAW, GL_DYNAMIC_DRAW, GL_STREAM_DRAW
        Returns (vbo_id, size_bytes)."""
        from OpenGL.GL import (
            glGenBuffers, glBindBuffer, glBufferData,
            GL_ARRAY_BUFFER, GL_STATIC_DRAW, GL_DYNAMIC_DRAW, GL_STREAM_DRAW,
        )
        import numpy as np
        arr = np.array(data, dtype=np.float32)
        usage_map = {"static": GL_STATIC_DRAW, "dynamic": GL_DYNAMIC_DRAW, "stream": GL_STREAM_DRAW}
        gl_usage = usage_map.get(usage, GL_STATIC_DRAW) if usage else GL_STATIC_DRAW
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, arr.nbytes, arr.ctypes.data, gl_usage)
        return vbo, arr.nbytes

    def create_ebo(self, indices):
        """Create an Element Buffer Object from index data."""
        from OpenGL.GL import (
            glGenBuffers, glBindBuffer, glBufferData,
            GL_ELEMENT_ARRAY_BUFFER, GL_STATIC_DRAW,
        )
        import numpy as np
        arr = np.array(indices, dtype=np.uint32)
        ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, arr.nbytes, arr.ctypes.data, GL_STATIC_DRAW)
        return ebo, arr.nbytes

    def create_ssbo(self, data):
        """Create a Shader Storage Buffer Object."""
        from OpenGL.GL import (
            glGenBuffers, glBindBuffer, glBufferData, glBindBufferBase,
            GL_SHADER_STORAGE_BUFFER, GL_STATIC_DRAW, GL_MAP_READ_BIT,
        )
        import numpy as np
        arr = np.array(data, dtype=np.float32)
        ssbo = glGenBuffers(1)
        glBindBuffer(GL_SHADER_STORAGE_BUFFER, ssbo)
        glBufferData(GL_SHADER_STORAGE_BUFFER, arr.nbytes, arr.ctypes.data, GL_STATIC_DRAW)
        return ssbo, arr.nbytes

    def bind_ssbo(self, ssbo, binding):
        from OpenGL.GL import (
            glBindBufferBase,
            GL_SHADER_STORAGE_BUFFER,
        )
        glBindBufferBase(GL_SHADER_STORAGE_BUFFER, binding, ssbo)

    def update_vbo(self, vbo, data, offset=0):
        """Update VBO data (for dynamic geometry)."""
        from OpenGL.GL import (
            glBindBuffer,
            glBufferSubData,
            GL_ARRAY_BUFFER,
        )
        import numpy as np
        arr = np.array(data, dtype=np.float32)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferSubData(GL_ARRAY_BUFFER, offset, arr.nbytes, arr.ctypes.data)

    def vertex_attrib(self, location, size, stride=0, offset=0):
        """Set vertex attribute pointer at current VAO/VBO."""
        from OpenGL.GL import (
            glVertexAttribPointer, glEnableVertexAttribArray,
            GL_FLOAT, GL_FALSE,
        )
        glEnableVertexAttribArray(location)
        glVertexAttribPointer(location, size, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(offset))

    def delete(self, *buffers):
        from OpenGL.GL import glDeleteBuffers
        for b in buffers:
            glDeleteBuffers(1, [b])


import ctypes
