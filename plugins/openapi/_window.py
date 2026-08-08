"""OPENapi WindowAPI — input callbacks, cursor modes, fullscreen, window management."""


class WindowAPI:
    """Window and input management. Subscribe to callbacks for game engine input."""

    def __init__(self, context):
        self.ctx = context
        self.window = context._window
        self.keys = {}
        self.mouse_buttons = {}
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.mouse_dx = 0.0
        self.mouse_dy = 0.0
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        self.char_callbacks = []
        self.resize_callbacks = []
        self._init_callbacks()

    def _init_callbacks(self):
        if not self.window:
            return
        try:
            import glfw
            glfw.set_key_callback(self.window, self._key_cb)
            glfw.set_mouse_button_callback(self.window, self._mouse_cb)
            glfw.set_cursor_pos_callback(self.window, self._cursor_cb)
            glfw.set_scroll_callback(self.window, self._scroll_cb)
            glfw.set_char_callback(self.window, self._char_cb)
            glfw.set_window_size_callback(self.window, self._resize_cb)
        except Exception:
            pass

    def _key_cb(self, window, key, scancode, action, mods):
        import glfw
        self.keys[key] = action in (glfw.PRESS, glfw.REPEAT)

    def _mouse_cb(self, window, button, action, mods):
        import glfw
        self.mouse_buttons[button] = action == glfw.PRESS

    def _cursor_cb(self, window, x, y):
        self.mouse_dx = x - self.mouse_x
        self.mouse_dy = y - self.mouse_y
        self.mouse_x = x
        self.mouse_y = y

    def _scroll_cb(self, window, x, y):
        self.scroll_x = x
        self.scroll_y = y

    def _char_cb(self, window, char):
        for cb in self.char_callbacks:
            cb(char)

    def _resize_cb(self, window, w, h):
        self.ctx.width, self.ctx.height = w, h
        for cb in self.resize_callbacks:
            cb(w, h)

    def is_key_pressed(self, key):
        return self.keys.get(key, False)

    def is_mouse_pressed(self, button):
        return self.mouse_buttons.get(button, False)

    def poll_delta(self):
        """Return (mouse_dx, mouse_dy, scroll_x, scroll_y) since last poll, then reset."""
        dx, dy = self.mouse_dx, self.mouse_dy
        sx, sy = self.scroll_x, self.scroll_y
        self.mouse_dx = self.mouse_dy = 0.0
        self.scroll_x = self.scroll_y = 0.0
        return dx, dy, sx, sy

    def set_cursor_mode(self, mode):
        import glfw
        if mode == "hidden":
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_HIDDEN)
        elif mode == "disabled":
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)
        else:
            glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)

    def set_title(self, title):
        import glfw
        glfw.set_window_title(self.window, title)

    def get_time(self):
        import glfw
        return glfw.get_time()

    def on_char(self, callback):
        self.char_callbacks.append(callback)

    def on_resize(self, callback):
        self.resize_callbacks.append(callback)
