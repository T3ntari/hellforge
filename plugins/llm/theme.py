"""Anthropic-style TUI theme — Claude Code's visual identity:
warm cream text, muted violet accents, sage green success, terracotta
errors, amber warnings, charcoal borders. 24-bit ANSI with an 8-color
fallback for terminals without truecolor. Everything is TTY-aware."""

import os
import sys

# Palette (RGB)
CREAM = (247, 243, 234)       # primary text
VIOLET = (196, 163, 246)      # primary accent
CHARCOAL = (58, 54, 66)       # borders / structure
SAGE = (150, 180, 140)        # success
TERRACOTTA = (205, 120, 90)   # errors
AMBER = (224, 180, 110)       # warnings
DIM = (140, 132, 120)         # muted

# 8-color fallbacks
_FALLBACK = {
    CREAM: "97", VIOLET: "35", CHARCOAL: "90", SAGE: "32",
    TERRACOTTA: "31", AMBER: "33", DIM: "90",
}


def _tty():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def _truecolor():
    ct = os.environ.get("COLORTERM", "")
    return "truecolor" in ct or "24bit" in ct


def _ansi(rgb, code):
    if not _tty():
        return ""
    if _truecolor():
        return f"\033[{code};2;{rgb[0]};{rgb[1]};{rgb[2]}m"
    return f"\033[{_FALLBACK.get(rgb, '90')}m"


def _paint(text, rgb, code):
    ansi = _ansi(rgb, code)
    if not ansi:
        return text
    return f"{ansi}{text}\033[0m"


def cream(text):
    return _paint(text, CREAM, 38)


def violet(text):
    return _paint(text, VIOLET, 38)


def sage(text):
    return _paint(text, SAGE, 38)


def terra(text):
    return _paint(text, TERRACOTTA, 38)


def amber(text):
    return _paint(text, AMBER, 38)


def dim(text):
    return _paint(text, DIM, 38)


def box(text, width=58):
    """Render a bordered box (charcoal borders, cream content)."""
    lines = (text or "").splitlines()
    w = max(width, max((len(l) for l in lines), default=0) + 4)
    top = "┌" + "─" * (w - 2) + "┐"
    bot = "└" + "─" * (w - 2) + "┘"
    out = [_paint(top, CHARCOAL, 38)]
    for l in lines:
        out.append(_paint("│ ", CHARCOAL, 38) + l + _paint(" │", CHARCOAL, 38))
    out.append(_paint(bot, CHARCOAL, 38))
    if not _tty():
        out = ["+" + "-" * (w - 2) + "+",
               *[f"| {l}" for l in lines],
               "+" + "-" * (w - 2) + "+"]
    return "\n".join(out)


HELLFORGE_ART = r"""
  _  _    ___   _  _   _____   _____    ___    ___    ____   _____
 | || |  / _ \ | || | | ____| |  ___|  / _ \  / _ \  |  _ \ | ____|
 | || |_| | | || || |_| |_    | |_    | | | || | | | | |_) ||  _|
 |__   _| |_| ||__   _|  _|   |  _|   | |_| || |_| | |  _ < | |___
    | |  \___/    | | | |___  | |     \___/  \___/  |_| \_\|_____|
    |_|           |_| |_____| |_|
"""


def splash(version="", git_branch="", tools_line="", model=""):
    """The welcome splash: ASCII header + dim subtitle + divider + ready."""
    parts = [violet(HELLFORGE_ART.rstrip("\n"))]
    sub = []
    if version:
        sub.append(f"v{version}")
    if git_branch:
        sub.append(f"Git: {git_branch}")
    if tools_line:
        sub.append(tools_line)
    if model:
        sub.append(f"model: {model}")
    if sub:
        parts.append(dim("  " + " • ".join(sub)))
    parts.append(dim("  " + "─" * 56))
    parts.append(sage("  ✓ ready"))
    return "\n".join(parts)


def footer(keys=None):
    """The persistent shortcut bar (dim, one line)."""
    keys = keys or ["Ctrl+C: Copy", "Ctrl+V: Paste", "Ctrl+X: Cut",
                    "Tab: Autocomplete", "/exit: Leave"]
    return dim("  " + " | ".join(keys))


def spinner_line(text):
    """Print a working line WITHOUT a trailing newline (ends in \\r so the
    next done_line can overwrite it). Off-TTY prints normally."""
    if _tty():
        print("  " + dim(text) + "\r", end="", flush=True)
    else:
        print("  " + dim(text), flush=True)


def done_line(text):
    """Overwrite the spinner line with a ✓ completion line."""
    print("  " + sage("✓ ") + cream(text), flush=True)


def permission_box(question, detail=""):
    """The high-visibility approval boundary box + choice array."""
    body = question
    if detail:
        body += "\n" + dim(detail)
    return box(body) + "\n" + sage("[Y]es") + " / " + terra("[N]o") + \
        " / " + violet("[E]dit block")
