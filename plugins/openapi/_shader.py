"""OPENapi ShaderAPI — GLSL shader compilation, program linking, uniform management."""

import ctypes


class ShaderAPI:
    """OpenGL shader compilation and program linking."""

    def __init__(self, context):
        self.ctx = context
        self._programs = {}

    def compile(self, vertex_src, fragment_src, name="default"):
        """Compile vertex + fragment shader into a program. Returns program_id."""
        try:
            from OpenGL.GL import (
                glCreateProgram, glCreateShader, glShaderSource, glCompileShader,
                glAttachShader, glLinkProgram, glUseProgram,
                glGetShaderiv, glGetProgramiv, glGetShaderInfoLog, glGetProgramInfoLog,
                glDeleteShader, glDeleteProgram,
                GL_VERTEX_SHADER, GL_FRAGMENT_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS,
            )

            vshader = glCreateShader(GL_VERTEX_SHADER)
            glShaderSource(vshader, vertex_src)
            glCompileShader(vshader)
            if not glGetShaderiv(vshader, GL_COMPILE_STATUS):
                log = glGetShaderInfoLog(vshader)
                glDeleteShader(vshader)
                raise RuntimeError(f"Vertex shader error:\n{log}")

            fshader = glCreateShader(GL_FRAGMENT_SHADER)
            glShaderSource(fshader, fragment_src)
            glCompileShader(fshader)
            if not glGetShaderiv(fshader, GL_COMPILE_STATUS):
                log = glGetShaderInfoLog(fshader)
                glDeleteShader(vshader)
                glDeleteShader(fshader)
                raise RuntimeError(f"Fragment shader error:\n{log}")

            program = glCreateProgram()
            glAttachShader(program, vshader)
            glAttachShader(program, fshader)
            glLinkProgram(program)
            if not glGetProgramiv(program, GL_LINK_STATUS):
                log = glGetProgramInfoLog(program)
                glDeleteShader(vshader)
                glDeleteShader(fshader)
                glDeleteProgram(program)
                raise RuntimeError(f"Program link error:\n{log}")

            glDeleteShader(vshader)
            glDeleteShader(fshader)
            self._programs[name] = program
            return program

        except Exception as e:
            raise RuntimeError(f"Shader compile failed: {e}")

    def compile_compute(self, compute_src, name="compute"):
        """Compile a compute shader. Returns program_id."""
        from OpenGL.GL import (
            glCreateProgram, glCreateShader, glShaderSource, glCompileShader,
            glAttachShader, glLinkProgram, glGetShaderiv, glGetShaderInfoLog,
            glGetProgramiv, glGetProgramInfoLog, glDeleteShader, glDeleteProgram,
            GL_COMPUTE_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS,
        )

        shader = glCreateShader(GL_COMPUTE_SHADER)
        glShaderSource(shader, compute_src)
        glCompileShader(shader)
        if not glGetShaderiv(shader, GL_COMPILE_STATUS):
            log = glGetShaderInfoLog(shader)
            glDeleteShader(shader)
            raise RuntimeError(f"Compute shader error:\n{log}")

        program = glCreateProgram()
        glAttachShader(program, shader)
        glLinkProgram(program)
        if not glGetProgramiv(program, GL_LINK_STATUS):
            log = glGetProgramInfoLog(program)
            glDeleteShader(shader)
            glDeleteProgram(program)
            raise RuntimeError(f"Program link error:\n{log}")

        glDeleteShader(shader)
        self._programs[name] = program
        return program

    def use(self, program_id):
        """Bind a program for rendering."""
        from OpenGL.GL import glUseProgram
        glUseProgram(program_id)

    def uniform(self, program_id, name, value):
        """Set a uniform value. Supports float, int, vec2, vec3, vec4, mat4."""
        from OpenGL.GL import (
            glGetUniformLocation, glUniform1f, glUniform1i,
            glUniform2f, glUniform3f, glUniform4f,
            glUniformMatrix4fv, GL_FALSE,
        )
        loc = glGetUniformLocation(program_id, name)
        if loc < 0:
            return

        if isinstance(value, (float, int)):
            if isinstance(value, int):
                glUniform1i(loc, value)
            else:
                glUniform1f(loc, value)
        elif hasattr(value, '__len__'):
            if len(value) == 2:
                glUniform2f(loc, *value)
            elif len(value) == 3:
                glUniform3f(loc, *value)
            elif len(value) == 4:
                glUniform4f(loc, *value)
            elif len(value) == 16:
                import numpy as np
                arr = np.array(value, dtype=np.float32)
                glUniformMatrix4fv(loc, 1, GL_FALSE, arr)

    def delete(self, program_id):
        from OpenGL.GL import glDeleteProgram
        glDeleteProgram(program_id)

    def get_program(self, name):
        return self._programs.get(name)
