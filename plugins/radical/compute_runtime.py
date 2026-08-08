"""Compute Runtime — GPU buffer management, shader dispatch, readback.
Manages OpenGL compute shader pipeline for math expression evaluation.
Falls back to CPU if GPU context is unavailable."""

import hashlib
import time

from .ast_to_glsl import (
    ast_to_glsl,
    _collect_vars,
)
from .shader_compiler import (
    compile_glsl,
    use_program,
    delete_program,
)


class RadicalEngine:
    """GPU compute engine for math expression evaluation."""

    def __init__(self, gpu_info, max_vram_mb=0):
        self.gpu_info = gpu_info
        self.available = False
        self.diagnostic = ""
        self._compile_count = 0
        self._eval_count = 0
        self._ctx = None
        self._max_vram_mb = max_vram_mb
        self._vram_used_mb = 0
        self._init()
        if self.available and max_vram_mb > 0:
            self.diagnostic += f" (VRAM limit {max_vram_mb}MB)"

    def _init(self):
        """Initialize GPU context for compute."""
        try:
            from OpenGL.GL import (
                glGenBuffers, glBindBuffer, glBufferData, glBufferSubData,
                glGetBufferSubData, glMapBuffer, glUnmapBuffer,
                glGenVertexArrays, glDispatchCompute, glMemoryBarrier,
                glFinish, glGetInteger,
                GL_SHADER_STORAGE_BUFFER, GL_MAP_WRITE_BIT, GL_MAP_READ_BIT,
                GL_ALL_BARRIER_BITS, GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS,
            )
            from OpenGL import GL as gl

            # We need an active OpenGL context. The gpu_detect already created one.
            # If no context exists, try to create a hidden window.
            ctx = _ensure_context()
            if ctx is None:
                self.diagnostic = "No OpenGL context available"
                return

            self._ctx = ctx
            self.available = True
            self.diagnostic = "ready"
        except ImportError as e:
            self.diagnostic = f"PyOpenGL not installed: {e}"
        except Exception as e:
            self.diagnostic = f"Engine init: {e}"

    def eval_ast(self, ast_dict, variables):
        """Evaluate a single math AST on GPU (or CPU fallback).
        Returns float result or None."""
        if not self.available:
            return self._eval_cpu(ast_dict, variables)

        try:
            var_names = sorted(variables.keys()) if variables else []
            source = ast_to_glsl(ast_dict, var_names, count=1)

            source_hash = hashlib.sha256(source.encode()).hexdigest()
            program, err = compile_glsl(source, source_hash)
            if program is None:
                return self._eval_cpu(ast_dict, variables, err)

            self._compile_count += 1
            return self._dispatch_single(program, var_names, variables)
        except Exception:
            return self._eval_cpu(ast_dict, variables)

    def eval_batch(self, ast_dicts, variables_list):
        """Evaluate multiple ASTs in a single GPU dispatch.
        ast_dicts: list of AST dicts
        variables_list: list of variable dicts (same length)
        Returns list of results."""
        if not self.available or not ast_dicts:
            return [self._eval_cpu(ad, vd) for ad, vd in zip(ast_dicts, variables_list or [{}] * len(ast_dicts))]

        try:
            # Collect all variable names
            all_vars = set()
            for ad in ast_dicts:
                _collect_vars(ad, all_vars)
            var_names = sorted(all_vars)

            # Build combined shader
            from .ast_to_glsl import ast_list_to_glsl
            source = ast_list_to_glsl(ast_dicts, var_names, count=len(ast_dicts))
            source_hash = hashlib.sha256(source.encode()).hexdigest()
            program, err = compile_glsl(source, source_hash)
            if program is None:
                return [self._eval_cpu(ad, vd) for ad, vd in zip(ast_dicts, variables_list or [{}] * len(ast_dicts))]

            self._compile_count += 1
            return self._dispatch_batch(program, var_names, variables_list, len(ast_dicts))
        except Exception:
            return [self._eval_cpu(ad, vd) for ad, vd in zip(ast_dicts, variables_list or [{}] * len(ast_dicts))]

    def _dispatch_single(self, program, var_names, variables):
        """Dispatch a single expression compute shader and read back result."""
        try:
            from OpenGL.GL import (
                glUseProgram, glGenBuffers, glBindBuffer, glBufferData,
                glBufferSubData, glGetBufferSubData, glDispatchCompute,
                glMemoryBarrier, glFinish, glBindBufferBase,
                GL_SHADER_STORAGE_BUFFER, GL_ALL_BARRIER_BITS,
            )

            glUseProgram(program)

            # Output buffer (1 float)
            out_buf = glGenBuffers(1)
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, out_buf)
            glBufferData(GL_SHADER_STORAGE_BUFFER, 4, None, GL_MAP_READ_BIT)  # 1 float = 4 bytes
            glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, out_buf)

            # Input buffers for each variable
            input_bufs = []
            for idx, name in enumerate(var_names):
                val = variables.get(name, 0.0)
                buf = glGenBuffers(1)
                glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf)
                import ctypes
                data = (ctypes.c_float * 1)(float(val))
                glBufferData(GL_SHADER_STORAGE_BUFFER, 4, data, GL_MAP_READ_BIT)
                glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1 + idx, buf)
                input_bufs.append(buf)

            # Dispatch (1 workgroup, 1 invocation)
            glDispatchCompute(1, 1, 1)
            glMemoryBarrier(GL_ALL_BARRIER_BITS)
            glFinish()

            # Read back
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, out_buf)
            import ctypes
            result = (ctypes.c_float * 1)()
            glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, 4, result)
            val = result[0]

            # Cleanup
            for buf in input_bufs:
                try:
                    from OpenGL.GL import glDeleteBuffers
                    glDeleteBuffers(1, [buf])
                except Exception:
                    pass
            try:
                from OpenGL.GL import glDeleteBuffers
                glDeleteBuffers(1, [out_buf])
            except Exception:
                pass

            self._eval_count += 1
            return float(val)

        except Exception:
            return self._eval_cpu(ast_dict=None, variables=variables)

    def _dispatch_batch(self, program, var_names, variables_list, count):
        """Dispatch batch compute shader."""
        try:
            from OpenGL.GL import (
                glUseProgram, glGenBuffers, glBindBuffer, glBufferData,
                glBufferSubData, glGetBufferSubData, glDispatchCompute,
                glMemoryBarrier, glFinish, glBindBufferBase,
                GL_SHADER_STORAGE_BUFFER, GL_ALL_BARRIER_BITS,
            )
            import ctypes

            glUseProgram(program)

            # Output buffer (count floats)
            out_buf = glGenBuffers(1)
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, out_buf)
            glBufferData(GL_SHADER_STORAGE_BUFFER, count * 4, None, GL_MAP_READ_BIT)
            glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, out_buf)

            # Input buffers
            input_bufs = []
            for idx, name in enumerate(var_names):
                data = (ctypes.c_float * count)(*[float(vl.get(name, 0.0)) for vl in variables_list])
                buf = glGenBuffers(1)
                glBindBuffer(GL_SHADER_STORAGE_BUFFER, buf)
                glBufferData(GL_SHADER_STORAGE_BUFFER, count * 4, data, GL_MAP_READ_BIT)
                glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 1 + idx, buf)
                input_bufs.append(buf)

            # Dispatch (ceil(count / 256) workgroups)
            groups = (count + 255) // 256
            glDispatchCompute(groups, 1, 1)
            glMemoryBarrier(GL_ALL_BARRIER_BITS)
            glFinish()

            # Read back
            glBindBuffer(GL_SHADER_STORAGE_BUFFER, out_buf)
            result_data = (ctypes.c_float * count)()
            glGetBufferSubData(GL_SHADER_STORAGE_BUFFER, 0, count * 4, result_data)
            results = [float(result_data[i]) for i in range(count)]

            # Cleanup
            for buf in input_bufs + [out_buf]:
                try:
                    from OpenGL.GL import glDeleteBuffers
                    glDeleteBuffers(1, [buf])
                except Exception:
                    pass

            self._eval_count += count
            return results

        except Exception:
            return [self._eval_cpu(ad, vl)
                    for ad, vl in zip([None] * count, variables_list)]

    def _eval_cpu(self, ast_dict=None, variables=None, error=""):
        """CPU fallback: evaluate using Python evaluator."""
        if error:
            self.diagnostic = error
        try:
            from ep_compiler.variables import evaluate_expression
            # We need the expression string, which we don't have here.
            # Fall back to the registered Python evaluator directly.
            from ep_compiler.variables import _evaluators
            for priority, name, eval_fn in _evaluators:
                if name == "Python":
                    result = eval_fn(ast_dict, variables or {})
                    if result is not None:
                        return float(result)
            return None
        except Exception:
            return None

    def _check_vram(self, bytes_needed):
        """Check if allocating bytes_needed would exceed the VRAM limit.
        Returns True if allocation is allowed."""
        if self._max_vram_mb <= 0:
            return True
        mb_needed = bytes_needed / (1024 * 1024)
        if self._vram_used_mb + mb_needed > self._max_vram_mb:
            return False
        self._vram_used_mb += mb_needed
        return True

    def _free_vram(self, bytes_freed):
        """Track VRAM deallocation."""
        if self._max_vram_mb > 0:
            mb_freed = bytes_freed / (1024 * 1024)
            self._vram_used_mb = max(0, self._vram_used_mb - mb_freed)

    def stats(self):
        return {
            "compile_count": self._compile_count,
            "eval_count": self._eval_count,
            "available": self.available,
            "diagnostic": self.diagnostic,
            "vram_used_mb": self._vram_used_mb,
            "max_vram_mb": self._max_vram_mb,
        }

    def shutdown(self):
        """Clean up GPU resources."""
        try:
            from .shader_cache import _cache
            for program_id in list(_cache.values()):
                try:
                    delete_program(program_id)
                except Exception:
                    pass
            _cache.clear()
            # Destroy context if we created one
            _destroy_context(self._ctx)
        except Exception:
            pass


# ── Context Management (shared across Radical) ──

_global_context = None


def _ensure_context():
    """Ensure an OpenGL context exists for compute operations.
    Returns context info or None."""
    global _global_context
    if _global_context is not None:
        return _global_context

    # Try glfw
    try:
        import glfw
        if glfw.init():
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            w = glfw.create_window(1, 1, "", None, None)
            if w:
                glfw.make_context_current(w)
                _global_context = {"type": "glfw", "window": w}
                return _global_context
    except Exception:
        pass

    # Try pygame
    try:
        import pygame
        if not pygame.get_init():
            pygame.init()
        pygame.display.set_mode((1, 1), pygame.OPENGL | pygame.HIDDEN)
        _global_context = {"type": "pygame"}
        return _global_context
    except Exception:
        pass

    return None


def _destroy_context(ctx):
    """Destroy an OpenGL context."""
    global _global_context
    if ctx is None:
        return
    try:
        if ctx.get("type") == "glfw":
            import glfw
            glfw.make_context_current(None)
            glfw.destroy_window(ctx.get("window"))
            glfw.terminate()
        elif ctx.get("type") == "pygame":
            import pygame
            pygame.quit()
    except Exception:
        pass
    _global_context = None
