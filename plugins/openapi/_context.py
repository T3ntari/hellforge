import os

"""OPENapi GLContext — raw OpenGL context, window, extensions, debug.
This is the lowest layer. Game engines create one context and build on top."""


def _display_available():
    """True when a display is reachable (env, Wayland or X sockets) —
    avoids glfw.init() warnings on headless machines."""
    if os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
        return True
    try:
        runtime = os.environ.get("XDG_RUNTIME_DIR", "/run/user/1000")
        if os.path.isdir(runtime) and any(
                d.startswith("wayland-") for d in os.listdir(runtime)):
            return True
        if os.path.isdir("/tmp/.X11-unix") and any(
                d.startswith("X") for d in os.listdir("/tmp/.X11-unix")):
            return True
    except Exception:
        pass
    return False


import os
import sys


class GLContext:
    """Raw OpenGL context. One per application. Everything else derives from this."""

    def __init__(self, width=800, height=600, title="OPENapi", fullscreen=False, vsync=True):
        self.available = False
        self.diagnostic = ""
        self.width = width
        self.height = height
        self.title = title
        self.fullscreen = fullscreen
        self.vsync = vsync
        self.gpu_name = "Unknown"
        self.gl_version = "N/A"
        self.glsl_version = "N/A"
        self.vendor = "Unknown"
        self.renderer = "Unknown"
        self.extensions = []
        self._window = None
        self._init()

    def _init(self):
        if not _display_available():
            self.diagnostic = "no display (headless)"
            return
        try:
            import warnings
            import glfw
            glfw.set_error_callback(lambda *a: None)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ok = glfw.init()
            if not ok:
                self.diagnostic = "glfw init failed"
                return

            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
            glfw.window_hint(glfw.OPENGL_DEBUG_CONTEXT, True)

            monitor = glfw.get_primary_monitor() if fullscreen else None
            self._window = glfw.create_window(width, height, title, monitor, None)
            if not self._window:
                # Fall back to 4.3
                glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
                glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
                self._window = glfw.create_window(width, height, title, None, None)
                if not self._window:
                    glfw.terminate()
                    self.diagnostic = "glfw window creation failed"
                    return

            glfw.make_context_current(self._window)
            glfw.swap_interval(1 if vsync else 0)

            self._read_context_info()
            self.available = True
            self.diagnostic = "ready"

        except ImportError:
            self.diagnostic = "PyOpenGL/glfw not installed (pip install PyOpenGL glfw)"
        except Exception as e:
            self.diagnostic = str(e)
            self._cleanup()

    def _read_context_info(self):
        from OpenGL.GL import (
            glGetString,
            GL_RENDERER,
            GL_VENDOR,
            GL_VERSION,
            GL_SHADING_LANGUAGE_VERSION,
        )
        from OpenGL.GL import (
            glGetIntegerv,
            GL_NUM_EXTENSIONS,
            GL_EXTENSIONS,
        )
        self.renderer = glGetString(GL_RENDERER).decode()
        self.vendor = glGetString(GL_VENDOR).decode()
        self.gpu_name = self.renderer
        self.gl_version = glGetString(GL_VERSION).decode()
        self.glsl_version = glGetString(GL_SHADING_LANGUAGE_VERSION).decode()
        count = glGetIntegerv(GL_NUM_EXTENSIONS)
        self.extensions = set()
        for i in range(count):
            self.extensions.add(glGetString(GL_EXTENSIONS, i).decode())

    def swap_buffers(self):
        if self._window:
            import glfw
            glfw.swap_buffers(self._window)

    def poll_events(self):
        import glfw
        glfw.poll_events()

    def should_close(self):
        import glfw
        return glfw.window_should_close(self._window) if self._window else True

    def set_window_size(self, w, h):
        if self._window:
            import glfw
            glfw.set_window_size(self._window, w, h)
            self.width, self.height = w, h

    def toggle_fullscreen(self):
        import glfw
        if self._window:
            if self.fullscreen:
                glfw.set_window_monitor(self._window, None, 100, 100, self.width, self.height, 0)
            else:
                monitor = glfw.get_primary_monitor()
                mode = glfw.get_video_mode(monitor)
                glfw.set_window_monitor(self._window, monitor, 0, 0, mode.size.width, mode.size.height, mode.refresh_rate)
            self.fullscreen = not self.fullscreen
            glfw.swap_interval(1 if self.vsync else 0)

    def _cleanup(self):
        try:
            import glfw
            if self._window:
                glfw.destroy_window(self._window)
            glfw.terminate()
        except Exception:
            pass
        self._window = None

    def __del__(self):
        self._cleanup()
