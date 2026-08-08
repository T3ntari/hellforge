"""HELL'S CODE — a real full-screen TUI (curses-based) for the copilot.

Game-engine architecture: a screen buffer that repaints only changed cells,
a frame loop driven by a background agent thread, raw-mode key input, a
bordered sub-window for command output, a gatekeeper modal for approvals,
terminal-resize awareness, and relative color tokens (decoupled from the
user's terminal theme).

Branding: HELL'S CODE in a fiery red theme; "- T3ntari" in grey.

Fallback: when curses is unavailable (non-TTY, Windows without
windows-curses) the caller keeps using the classic line REPL.
"""

import os
import queue
import sys
import threading
import time

try:
    import curses
    HAS_CURSES = True
except ImportError:  # pragma: no cover
    HAS_CURSES = False


# ── Pure layout helpers (unit-testable, no curses) ──

def wrap(text, width):
    """Word-wrap text to width. Returns a list of lines (never empty)."""
    text = (text or "").replace("\t", "    ")
    lines = text.split("\n")
    out = []
    for ln in lines:
        if ln == "":
            out.append("")
            continue
        while len(ln) > width:
            cut = ln.rfind(" ", 0, width + 1)
            if cut <= 0 or cut > width:
                cut = width
            out.append(ln[:cut])
            ln = ln[cut:].lstrip()
        out.append(ln)
    return out or [""]


class Feed:
    """The scrollback buffer: logical lines (with color tokens), re-wrapped
    at render time so terminal resizes reflow everything."""

    def __init__(self, max_lines=2000):
        self.max_lines = max_lines
        self.entries = []  # [(color_token, text)]  logical lines

    def append(self, text, color=None):
        for ln in (text or "").split("\n"):
            self.entries.append((color, ln))
        if len(self.entries) > self.max_lines:
            del self.entries[:len(self.entries) - self.max_lines]

    def clear(self):
        self.entries = []

    def render(self, width, height, scroll=0):
        """Wrap entries to width; return the last `height` lines
        as [(color, text)] with `scroll` lines of backscroll."""
        wrapped = []
        for color, ln in self.entries:
            for wl in wrap(ln, width):
                wrapped.append((color, wl))
        total = len(wrapped)
        start = max(0, total - height - scroll)
        end = start + height
        return wrapped[start:end], total, max(0, total - height)


# ── Relative color tokens (decoupled from the terminal theme) ──

HELLFIRE = {
    "name": "hellfire",
    "accent": (255, 77, 77),       # fiery red — primary accent
    "accent2": (255, 140, 66),     # ember orange
    "text": (255, 235, 220),       # warm off-white
    "dim": (140, 130, 125),        # grey (the "- T3ntari" line)
    "ok": (150, 200, 140),         # sage
    "err": (255, 100, 70),         # hot error
    "border": (120, 40, 40),       # dark ember border
    "warn": (240, 190, 90),        # amber
}

CLAUDE = {
    "name": "claude",
    "accent": (196, 163, 246),
    "accent2": (167, 139, 250),
    "text": (247, 243, 234),
    "dim": (140, 132, 120),
    "ok": (150, 180, 140),
    "err": (205, 120, 90),
    "border": (58, 54, 66),
    "warn": (224, 180, 110),
}


def palette(name):
    return HELLFIRE if name != "claude" else CLAUDE


# ── The event queue between agent thread and frame loop ──

EVENTS = {
    "chunk": "streamed text chunk (display only)",
    "feed": "append a full line to the feed",
    "status": "set the status line",
    "box_open": "open a bordered sub-window (title)",
    "box_line": "append a line inside the open sub-window",
    "box_close": "close the sub-window (result summary)",
    "ask": "gatekeeper: ask a question (thread blocks until answered)",
    "ask_answer": "the user's answer to a gatekeeper ask",
    "clear_input": "clear the input line",
    "set_input": "replace the input line",
    "thinking": "show the thinking indicator on/off",
    "quit": "leave the TUI",
}


class Bridge:
    """The agent thread's window into the TUI. Every method enqueues an
    event; ask() blocks the agent thread until the frame loop answers."""

    def __init__(self, events):
        self.events = events
        self._lock = threading.Lock()
        self._answers = {}

    def stream(self, text):
        self.events.put(("chunk", text))

    def feed(self, text, color=None):
        self.events.put(("feed", (color, text)))

    def status(self, text):
        self.events.put(("status", text))

    def thinking(self, on=True):
        self.events.put(("thinking", on))

    def box_open(self, title):
        self.events.put(("box_open", title))

    def box_line(self, text):
        self.events.put(("box_line", text))

    def box_close(self, summary=""):
        self.events.put(("box_close", summary))

    def ask(self, question, detail="", choices=("y", "n", "e")):
        """Gatekeeper: block until the user answers. Returns 'y'/'n'/'e'."""
        key = object()
        with self._lock:
            self._answers[key] = None
        self.events.put(("ask", (key, question, detail, choices)))
        while True:
            with self._lock:
                ans = self._answers.get(key)
            if ans is not None:
                with self._lock:
                    self._answers.pop(key, None)
                return ans
            time.sleep(0.05)

    def answer(self, key, value):
        with self._lock:
            self._answers[key] = value

    def quit(self):
        self.events.put(("quit", None))


# ── The TUI itself ──

class HellTui:
    def __init__(self, palette_name="hellfire", on_submit=None):
        """on_submit(text, bridge) runs on the agent thread per submitted
        line; it must call bridge.quit() when the session ends."""
        self.palette = palette(palette_name)
        self.on_submit = on_submit
        self.events = queue.Queue()
        self.bridge = Bridge(self.events)
        self.feed = Feed()
        self.input = ""
        self.cursor = 0
        self.status = ""
        self.thinking = False
        self.scroll = 0
        self.box = None        # (title, [lines]) when a sub-window is open
        self.agent = None
        self._red = None
        self._dim = None
        self._ink = None

    def _init_colors(self, stdscr):
        curses.start_color()
        curses.use_default_colors()
        p = self.palette

        def _pair(idx, rgb, fg=True):
            try:
                curses.init_color(idx, *[int(c * 1000 / 255) for c in rgb])
            except curses.error:
                pass
            curses.init_pair(idx, idx if fg else -1, -1)
            return curses.color_pair(idx)

        self._ink = _pair(1, p["text"])
        self._red = _pair(2, p["accent"])
        self._dim = _pair(3, p["dim"])
        self._ok = _pair(4, p["ok"])
        self._err = _pair(5, p["err"])
        self._border = _pair(6, p["border"])
        self._warn = _pair(7, p["warn"])
        self._orange = _pair(8, p["accent2"])
        self._bold = curses.A_BOLD

    def _key_for(self, token):
        return {"accent": self._red, "accent2": self._orange,
                "text": self._ink, "dim": self._dim, "ok": self._ok,
                "err": self._err, "border": self._border,
                "warn": self._warn}.get(token, self._ink)

    def _draw(self, stdscr, h, w):
        stdscr.erase()
        # header: HELL'S CODE banner
        banner = "HELL'S CODE"
        stdscr.addstr(0, 2, banner, self._red | self._bold)
        sub = "- T3ntari"
        stdscr.addstr(1, 2 + len(banner) + 2, sub, self._dim)
        stdscr.hline(2, 0, curses.ACS_HLINE, w)
        # feed area: rows 3 .. h-3 (input + footer at bottom)
        feed_h = max(1, h - 5)
        lines, total, max_scroll = self.feed.render(w - 2, feed_h, self.scroll)
        y = 3
        for color, ln in lines:
            try:
                stdscr.addstr(y, 1, ln[:w - 2], self._key_for(color))
            except curses.error:
                pass
            y += 1
        if self.thinking:
            try:
                stdscr.addstr(y, 1, "● thinking...", self._dim)
            except curses.error:
                pass
        # sub-window (bordered box) overlays the feed when open
        if self.box:
            title, box_lines = self.box
            bw = min(w - 8, 90)
            bh = min(h - 8, len(box_lines) + 4)
            bx = (w - bw) // 2
            by = max(4, (h - bh) // 2)
            try:
                stdscr.attron(self._border)
                stdscr.hline(by, bx, curses.ACS_HLINE, bw)
                stdscr.hline(by + bh - 1, bx, curses.ACS_HLINE, bw)
                stdscr.vline(by, bx, curses.ACS_VLINE, bh)
                stdscr.vline(by, bx + bw - 1, curses.ACS_VLINE, bh)
                stdscr.attroff(self._border)
                stdscr.addstr(by, bx + 2, f" {title} ", self._orange | self._bold)
                for i, ln in enumerate(box_lines[:bh - 3]):
                    stdscr.addstr(by + 1 + i, bx + 2, ln[:bw - 4], self._dim)
            except curses.error:
                pass
        # input line
        in_y = h - 2
        try:
            stdscr.addstr(in_y, 1, "> ", self._red | self._bold)
            stdscr.addstr(in_y, 3, self.input[:w - 5], self._ink)
            stdscr.move(in_y, 3 + min(self.cursor, w - 5))
        except curses.error:
            pass
        # footer
        try:
            stdscr.addstr(h - 1, 1,
                          "Ctrl+C: Copy | Ctrl+V: Paste | Ctrl+X: Cut | "
                          "PgUp/PgDn: scroll | /exit: Leave",
                          self._dim)
            if self.status:
                stdscr.addstr(h - 1, max(1, w - len(self.status) - 2),
                              self.status[:w - 2], self._dim)
        except curses.error:
            pass
        stdscr.refresh()

    def _on_key(self, stdscr, key):
        """Raw keystroke handling (instant — no OS line buffer)."""
        # gatekeeper modal: redirect input to the question
        if self._gatekeeper:
            k, question, detail, choices = self._gatekeeper
            if key in (ord("y"), ord("Y")):
                self.bridge.answer(k, "y")
                self._gatekeeper = None
            elif key in (ord("n"), ord("N")):
                self.bridge.answer(k, "n")
                self._gatekeeper = None
            elif key in (ord("e"), ord("E")) and "e" in choices:
                self.bridge.answer(k, "e")
                self._gatekeeper = None
            return
        if key == curses.KEY_RESIZE:
            return
        if key == curses.KEY_PPAGE:
            self.scroll += 10
            return
        if key == curses.KEY_NPAGE:
            self.scroll = max(0, self.scroll - 10)
            return
        if key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            if self.cursor > 0:
                self.input = self.input[:self.cursor - 1] + self.input[self.cursor:]
                self.cursor -= 1
            return
        if key == curses.KEY_DC:
            self.input = self.input[:self.cursor] + self.input[self.cursor + 1:]
            return
        if key == curses.KEY_LEFT:
            self.cursor = max(0, self.cursor - 1)
            return
        if key == curses.KEY_RIGHT:
            self.cursor = min(len(self.input), self.cursor + 1)
            return
        if key == curses.KEY_HOME:
            self.cursor = 0
            return
        if key == curses.KEY_END:
            self.cursor = len(self.input)
            return
        if key == ord("\n") or key == ord("\r") or key == curses.KEY_ENTER:
            line = self.input
            self.input = ""
            self.cursor = 0
            self.scroll = 0
            if line.strip().lower() in ("/exit", "/bye", "quit", "exit"):
                self.bridge.quit()
                return
            self.feed.append("> " + line, "accent")
            if self.on_submit:
                threading.Thread(target=self.on_submit,
                                 args=(line, self.bridge),
                                 daemon=True).start()
            return
        if key == 3:  # Ctrl+C → copy input line (empty = nothing)
            if self.input:
                self._copy_input(stdscr)
            return
        if key == 22:  # Ctrl+V → paste
            self._paste_input()
            return
        if key == 24:  # Ctrl+X → cut
            self._cut_input()
            return
        if key == 9:  # Tab → complete /$ paths and slash commands
            self._tab_complete()
            return
        if 32 <= key < 127:
            self.input = self.input[:self.cursor] + chr(key) + self.input[self.cursor:]
            self.cursor += 1
            return

    def _copy_input(self, stdscr):
        try:
            from plugins.llm import clipboard as cb
            ok, src = cb.copy(self.input)
            self.feed.append(f"copied to {src}", "dim")
        except Exception:
            pass

    def _paste_input(self):
        try:
            from plugins.llm import clipboard as cb
            text, _ = cb.paste()
            if text:
                self.input = self.input[:self.cursor] + text + self.input[self.cursor:]
                self.cursor += len(text)
        except Exception:
            pass

    def _cut_input(self):
        try:
            from plugins.llm import clipboard as cb
            if self.input:
                cb.cut(self.input)
                self.input = ""
                self.cursor = 0
        except Exception:
            pass

    def _tab_complete(self):
        line = self.input
        if line.startswith("/$") or line.startswith("/"):
            if line.startswith("/$"):
                base = line[2:]
                from pathlib import Path
                root = Path(".").resolve()
                prefix = base.rsplit("/", 1)[0] if "/" in base else ""
                partial = base.rsplit("/", 1)[-1]
                matches = sorted(p.name for p in root.rglob(f"{partial}*")
                                 if not p.name.startswith("."))[:20]
                if matches:
                    self.input = "/$" + (prefix + "/" if prefix else "") + matches[0]
                    self.cursor = len(self.input)
            elif line == "/":
                self.input = "/exit"
                self.cursor = len(self.input)

    def _drain(self, stdscr):
        """Frame loop: drain pending events and repaint."""
        try:
            while True:
                ev = self.events.get_nowait()
                kind = ev[0]
                if kind == "chunk":
                    self.feed.append(ev[1], "text")
                elif kind == "feed":
                    color, text = ev[1]
                    self.feed.append(text, color)
                elif kind == "status":
                    self.status = ev[1]
                elif kind == "thinking":
                    self.thinking = ev[1]
                elif kind == "box_open":
                    self.box = [ev[1], []]
                elif kind == "box_line":
                    if self.box:
                        self.box[1].append(ev[1])
                        if len(self.box[1]) > 200:
                            self.box[1] = self.box[1][-200:]
                elif kind == "box_close":
                    if self.box:
                        title, lines = self.box
                        self.box = None
                        self.feed.append(f"▸ {title} — done", "dim")
                elif kind == "ask":
                    key, question, detail, choices = ev[1]
                    self._gatekeeper = (key, question, detail, choices)
                    self._gk_question = question
                    self._gk_detail = detail
                elif kind == "quit":
                    return False
        except queue.Empty:
            pass
        return True

    def run(self, stdscr):
        self._init_colors(stdscr)
        stdscr.keypad(True)
        curses.curs_set(1)
        self._gatekeeper = None
        self._gk_question = ""
        self._gk_detail = ""
        while True:
            h, w = stdscr.getmaxyx()
            self._drain(stdscr)
            if self._gatekeeper:
                self._render_gatekeeper(stdscr, h, w)
                key = stdscr.getch()
                self._on_key(stdscr, key)
            else:
                self._draw(stdscr, h, w)
                stdscr.timeout(100)  # frame loop heartbeat (10 fps)
                key = stdscr.getch()
                if key == -1:
                    continue
                self._on_key(stdscr, key)
            if not self._drain(stdscr):
                break

    def _render_gatekeeper(self, stdscr, h, w):
        stdscr.erase()
        bw = min(w - 8, 70)
        bh = 8
        bx = (w - bw) // 2
        by = (h - bh) // 2
        try:
            stdscr.attron(self._border)
            stdscr.hline(by, bx, curses.ACS_HLINE, bw)
            stdscr.hline(by + bh - 1, bx, curses.ACS_HLINE, bw)
            stdscr.vline(by, bx, curses.ACS_VLINE, bh)
            stdscr.vline(by, bx + bw - 1, curses.ACS_VLINE, bh)
            stdscr.attroff(self._border)
            stdscr.addstr(by, bx + 2, " permission required ", self._err | self._bold)
            for i, ln in enumerate(wrap(self._gk_question, bw - 6)[:2]):
                stdscr.addstr(by + 2 + i, bx + 3, ln, self._ink)
            stdscr.addstr(by + 5, bx + 3, "[Y]es / [N]o / [E]dit block",
                          self._warn | self._bold)
        except curses.error:
            pass
        stdscr.refresh()


def tui_available():
    """True when we can run the full-screen TUI here."""
    if not HAS_CURSES:
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except Exception:
        return False


def run_tui(on_submit, palette_name="hellfire"):
    """Entry point: curses.wrapper around HellTui. Returns 0."""
    if not HAS_CURSES:
        return 1
    app = HellTui(palette_name=palette_name, on_submit=on_submit)

    def _main(stdscr):
        app.run(stdscr)

    try:
        curses.wrapper(_main)
    except Exception:
        return 1
    return 0
