"""Centralized comment stripper — handles // single-line and /* */ block comments."""
import re

BLOCK_OPEN_RE = re.compile(r"/\*")
BLOCK_CLOSE_RE = re.compile(r"\*/")


def _inside_braces(text, pos):
    """Check if position is inside { } braces (for // not stripping inside {$expr})."""
    depth = 0
    for i in range(pos):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
    return depth > 0


def strip_comments(text):
    """Remove // single-line and /* */ block comments from text.
    Does NOT strip // inside {...} blocks (needed for // floor division operator).
    Handles nested and multi-line block comments properly.
    Returns clean text suitable for parsing.
    """
    # Strip single-line comments (skip // inside braces)
    lines = text.split("\n")
    clean = []
    for line in lines:
        idx = 0
        buf = []
        while True:
            ci = line.find("//", idx)
            if ci < 0:
                buf.append(line[idx:])
                clean.append("".join(buf))
                break
            if _inside_braces(line, ci):
                buf.append(line[idx:ci + 2])
                idx = ci + 2
            else:
                buf.append(line[:ci])
                clean.append("".join(buf))
                break
    text = "\n".join(clean)

    # Strip block comments (handles multi-line)
    result = []
    i = 0
    while i < len(text):
        m = BLOCK_OPEN_RE.search(text, i)
        if not m:
            result.append(text[i:])
            break
        result.append(text[i:m.start()])
        close = BLOCK_CLOSE_RE.search(text, m.end())
        if close:
            i = close.end()
        else:
            i = len(text)
    return "".join(result)


def strip_line(line):
    """Strip trailing // comment from a single line.
    Does NOT strip // inside {...} blocks (needed for // floor division operator)."""
    idx = 0
    while True:
        ci = line.find("//", idx)
        if ci < 0:
            return line.rstrip()
        if _inside_braces(line, ci):
            idx = ci + 2
        else:
            before = line[:ci]
            if before.count('"') % 2 == 0 and before.count("'") % 2 == 0:
                return before.rstrip()
            idx = ci + 2


def has_block_comment(text):
    """Check if text contains /* */ block comments."""
    return bool(BLOCK_OPEN_RE.search(text))
