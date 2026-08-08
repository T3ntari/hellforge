"""Diff rendering for the interactive copilot — unified colored line diffs
(+ green, - red, line numbers), file reads with line ranges, diff stats.

Colors are stripped when stdout is not a TTY."""

import difflib
import sys

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
DIM = "\033[90m"
RESET = "\033[0m"


def _tty():
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def color(text, ansi):
    return f"{ansi}{text}{RESET}" if _tty() else text


def green(text):
    return color(text, GREEN)


def red(text):
    return color(text, RED)


def yellow(text):
    return color(text, YELLOW)


def dim(text):
    return color(text, DIM)


def render_unified(old_text, new_text, context=3, max_lines=400):
    """Unified diff with both-side line numbers. Returns list of display
    lines: 'old | new | body' — equal lines plain, deletions red (-),
    insertions green (+). Truncated to max_lines with a notice."""
    old = (old_text or "").splitlines() or [""]
    new = (new_text or "").splitlines() or [""]
    sm = difflib.SequenceMatcher(None, old, new)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i1, i2):
                out.append(f"{i1 + k + 1:5} | {j1 + k + 1:5} | {old[k]}")
        elif tag == "delete":
            for k in range(i1, i2):
                out.append(red(f"{i1 + k + 1:5} |      | - {old[k]}"))
        elif tag == "insert":
            for k in range(j1, j2):
                out.append(green(f"      | {j1 + k + 1:5} | + {new[k]}"))
        elif tag == "replace":
            for k in range(i1, i2):
                out.append(red(f"{i1 + k + 1:5} |      | - {old[k]}"))
            for k in range(j1, j2):
                out.append(green(f"      | {j1 + k + 1:5} | + {new[k]}"))
    if len(out) > max_lines:
        out = out[:max_lines] + [dim(f"  ... ({len(out) - max_lines} more lines — "
                                     f"use [v]iew to see the whole file)")]
    return out


def render_read(lines, start=1, end=None):
    """Line-numbered file view: 'Read (start-end)' style. Dim numbers."""
    if not lines:
        return [dim("  (empty file)")]
    end = end or len(lines)
    end = min(end, len(lines))
    out = []
    for i in range(max(1, start) - 1, end):
        out.append(f"{dim(f'{i + 1:5}')} | {lines[i]}")
    return out


def diff_stat(old_text, new_text):
    """'Write file.py | +10 | -20 |' style compact stat."""
    old = (old_text or "").splitlines()
    new = (new_text or "").splitlines()
    sm = difflib.SequenceMatcher(None, old, new)
    adds = dels = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("insert", "replace"):
            adds += j2 - j1
        if tag in ("delete", "replace"):
            dels += i2 - i1
    return adds, dels


def print_diff(old_text, new_text, path, max_lines=400):
    """Print a full colored diff for one file with a header line."""
    adds, dels = diff_stat(old_text, new_text)
    print(f"  {yellow(path)}  {green(f'+{adds}')} {red(f'-{dels}')}")
    for line in render_unified(old_text, new_text, max_lines=max_lines):
        print(f"  {line}")
