"""Thinking-tag extraction and rendering for the HELLFORGE copilot.

Parses deepseek-style <thinking>…</thinking> blocks (possibly multiple) and
OpenAI-style "reasoning_content" JSON fields out of model replies, and
renders them as a collapsed one-liner, full indented blocks, or the explored
turn-summary line. Pure text helpers — no ANSI, no I/O; ui.py applies the
dim colors TTY-aware."""

import re

_THINK_RE = re.compile(r"<thinking>(.*?)</thinking>", re.DOTALL | re.IGNORECASE)
_REASONING_RE = re.compile(r'"reasoning_content"\s*:\s*"((?:[^"\\]|\\.)*)"')


def extract_thinking(text):
    """Strip thinking out of a model reply.

    Extracts <thinking>…</thinking> blocks and OpenAI-style
    "reasoning_content" JSON fields. Returns (thinking_blocks, visible_text):
    thinking_blocks is a list of block strings (in order, stripped), and
    visible_text is the original text with all thinking removed."""
    text = text or ""
    blocks = [m.group(1).strip() for m in _THINK_RE.finditer(text)]
    visible = _THINK_RE.sub("", text)
    for m in _REASONING_RE.finditer(visible):
        blocks.append(m.group(1).strip())
    visible = _REASONING_RE.sub("", visible)
    return blocks, visible


def collapse(blocks, seconds):
    """Auto-collapsed one-liner: 'thought for 12.3s' (1 decimal).

    One block or many, the count collapses to the same line."""
    return f"thought for {seconds:.1f}s"


def render_full(blocks):
    """Thinking shown in full: '· thinking ·' prefix + indented blocks."""
    if not blocks:
        return ""
    body = "\n".join("  " + ln for block in blocks for ln in block.split("\n"))
    return "· thinking ·\n" + body


def explored_line(n_files, n_edits, n_commands):
    """Turn-summary line: 'explored 3 files · 2 edits · 1 command'.

    Only non-zero parts are included; all zero → empty string."""
    parts = []
    if n_files:
        parts.append(f"{n_files} file" + ("" if n_files == 1 else "s"))
    if n_edits:
        parts.append(f"{n_edits} edit" + ("" if n_edits == 1 else "s"))
    if n_commands:
        parts.append(f"{n_commands} command" + ("" if n_commands == 1 else "s"))
    return f"explored {' · '.join(parts)}" if parts else ""


def apply_config(state, show_full=None):
    """Resolve llm_show_thinking into a display config dict.

    state['llm_show_thinking']: any truthy value → full thinking shown
    ({'show_full': True}); the string 'auto' → collapsed one-liner plus the
    explored work line ({'explore': True}); falsy/absent → collapsed
    one-liner. show_full is the fallback used when state has no value."""
    cfg = {"show_full": bool(show_full), "explore": False}
    val = (state or {}).get("llm_show_thinking")
    if val is not None:
        if isinstance(val, str) and val.strip().lower() == "auto":
            cfg = {"show_full": False, "explore": True}
        else:
            cfg = {"show_full": bool(val), "explore": False}
    return cfg