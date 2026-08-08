"""Clipboard access for the copilot REPL — Ctrl+C copy, Ctrl+V paste,
Ctrl+X cut. Uses whatever clipboard tool the session has: wl-clipboard
(Wayland), xclip, xsel, or pbcopy/pbpaste (macOS). Honest fallback: a
session scratch file + the copied text echoed on screen.

All functions degrade gracefully — never raise on missing tools."""

import os
import shutil
import subprocess
import tempfile

_SCRATCH = os.path.join(tempfile.gettempdir(), "hellforge_clipboard.txt")


def _run(cmd, inp=None):
    try:
        r = subprocess.run(cmd, input=inp, capture_output=True, timeout=5)
        return r.returncode == 0, r.stdout
    except Exception:
        return False, b""


def _tools():
    """Ordered candidate tools: (set_cmd, get_cmd)."""
    cands = []
    for name, setc, getc in (
        ("wl-copy", ["wl-copy"], ["wl-paste", "--no-newline"]),
        ("xclip", ["xclip", "-selection", "clipboard"], ["xclip", "-selection", "clipboard", "-o"]),
        ("xsel", ["xsel", "--clipboard", "--input"], ["xsel", "--clipboard", "--output"]),
        ("pbcopy", ["pbcopy"], ["pbpaste"]),
    ):
        if shutil.which(name):
            cands.append((setc, getc))
    return cands


def available():
    """True when a real clipboard tool exists on this session."""
    return bool(_tools())


def copy(text, scratch_only=False):
    """Copy text to the clipboard. Returns (ok, detail).
    scratch_only=True forces the session scratch file (deterministic)."""
    text = text or ""
    if not scratch_only:
        for setc, _ in _tools():
            ok, _ = _run(setc, inp=text.encode("utf-8"))
            if ok:
                return True, "clipboard"
    # fallback: scratch file
    try:
        with open(_SCRATCH, "w", encoding="utf-8") as f:
            f.write(text)
        return True, "scratch"
    except Exception:
        return False, "no clipboard tool"


def paste(scratch_only=False):
    """Read clipboard text. Returns (text, source) — source is 'clipboard',
    'scratch', or 'none'. scratch_only=True reads the session scratch file."""
    if not scratch_only:
        for _, getc in _tools():
            ok, out = _run(getc)
            if ok:
                return out.decode("utf-8", errors="replace"), "clipboard"
    if os.path.exists(_SCRATCH):
        try:
            with open(_SCRATCH, "r", encoding="utf-8") as f:
                return f.read(), "scratch"
        except Exception:
            pass
    return "", "none"


def cut(text):
    """Copy + return empty (the REPL clears the line)."""
    ok, src = copy(text)
    return ok, src


def status_line():
    if available():
        return f"clipboard: {_tools()[0][0][0]}"
    return "clipboard: scratch file fallback"
