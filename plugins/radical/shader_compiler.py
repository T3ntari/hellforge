"""Shader Compiler — compile GLSL source to executable shader program.
Uses PyOpenGL runtime compilation. Caches compiled programs by source hash.
Falls back gracefully if OpenGL context or compilation fails."""

import hashlib
from .shader_cache import (
    get_cached_shader,
    cache_shader,
    get_cache_stats,
)


def compile_glsl(source, source_hash=None):
    """Compile GLSL compute shader source into a shader program.
    source: GLSL source string
    source_hash: optional pre-computed hash for cache lookup
    Returns (program_id, error) or (None, error_msg) on failure.
    """
    if source_hash is None:
        source_hash = hashlib.sha256(source.encode()).hexdigest()

    # Check cache first
    cached = get_cached_shader(source_hash)
    if cached is not None:
        return cached, None

    try:
        from OpenGL.GL import (
            glCreateProgram, glCreateShader, glShaderSource,
            glCompileShader, glAttachShader, glLinkProgram,
            glGetShaderiv, glGetProgramiv, glGetShaderInfoLog,
            glGetProgramInfoLog, glUseProgram, glDeleteShader,
            GL_COMPUTE_SHADER, GL_COMPILE_STATUS, GL_LINK_STATUS,
        )

        # Compile shader
        shader = glCreateShader(GL_COMPUTE_SHADER)
        glShaderSource(shader, source)
        glCompileShader(shader)

        # Check compile status
        status = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if not status:
            log = glGetShaderInfoLog(shader)
            glDeleteShader(shader)
            return None, f"Shader compile error: {log}"

        # Link program
        program = glCreateProgram()
        glAttachShader(program, shader)
        glLinkProgram(program)

        # Check link status
        status = glGetProgramiv(program, GL_LINK_STATUS)
        if not status:
            log = glGetProgramInfoLog(program)
            glDeleteShader(shader)
            return None, f"Program link error: {log}"

        glDeleteShader(shader)

        # Cache the result
        cache_shader(source_hash, program)
        return program, None

    except ImportError:
        return None, "PyOpenGL not installed"
    except Exception as e:
        return None, f"GLSL compile error: {e}"


def use_program(program_id):
    """Bind a compiled shader program for use."""
    try:
        from OpenGL.GL import glUseProgram
        glUseProgram(program_id)
    except Exception:
        pass


def delete_program(program_id):
    """Delete a compiled shader program."""
    try:
        from OpenGL.GL import glDeleteProgram
        glDeleteProgram(program_id)
    except Exception:
        pass
