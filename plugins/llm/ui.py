"""Claude-Code-style terminal rendering for the HELLFORGE copilot.

Pure rendering helpers (no I/O beyond print): branded banner, colored
prompts, status chips, dim section rules, thinking lines, result lines,
diff headers and text wrapping. Colors are stripped when stdout is not a
TTY — same pattern as diffview.py."""

import sys

CYAN = "\033[96m"
MAGENTA = "\033[95m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"


def is_tty():
    """Canonical TTY check: colors only reach a real terminal."""
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def color(text, ansi):
    return f"{ansi}{text}{RESET}" if is_tty() else text


def cyan(text):
    return color(text, CYAN)


def magenta(text):
    return color(text, MAGENTA)


def green(text):
    return color(text, GREEN)


def yellow(text):
    return color(text, YELLOW)


def red(text):
    return color(text, RED)


def dim(text):
    return color(text, DIM)


def bold(text):
    return color(text, BOLD)


def banner(state):
    """Branded session header:

    ── HELLFORGE COPILOT ──────────────────────────
      model: gemma3:4b   provider: ollama (local)   multi-agent: on
    ────────────────────────────────────────────────

    Model chip cyan, provider chip magenta, session id dim."""
    model = cyan(str(state.get("model") or "?"))
    provider = magenta(str(state.get("provider") or "?"))
    multi = dim(str(state.get("multi_agent", "on")))
    head = "── HELLFORGE COPILOT ─"
    bar = "─" * 60
    return f"{head}{'─' * (60 - len(head))}\n" \
           f"  model: {model}   provider: {provider}   multi-agent: {multi}\n" \
           f"{bar}"


def prompt(label="you"):
    """Colored input prompt: 'you> ' cyan bold, 'agent> ' magenta bold,
    'app> ' dim."""
    ansi = {"you": BOLD + CYAN, "agent": BOLD + MAGENTA,
            "app": DIM}.get(label, DIM)
    return color(f"{label}> ", ansi)


CHIP_COLORS = {
    "plan": MAGENTA,
    "edit": YELLOW,
    "command": CYAN,
    "test": GREEN,
    "done": GREEN,
    "error": RED,
    "skip": DIM,
}


def chip(text, kind):
    """Status chip, ' [plan] ' style — colored brackets + text."""
    return color(f" [{text}] ", CHIP_COLORS.get(kind, DIM))


def section(title):
    """Print a dim '── title ──────' rule, filled to ~60 cols."""
    head = f"── {title} ─"
    print(dim(head + "─" * max(1, 60 - len(head))))


def thinking(text):
    """Print a dim '● asking model…' style status line."""
    print(dim(f"● {text}"))


_RESULT_PREFIXES = {
    "ok": ("✓", GREEN),
    "error": ("✗", RED),
    "info": ("→", CYAN),
}


def result_line(text, kind="ok"):
    """Result line with colored prefix: ✓ green, ✗ red, → cyan."""
    symbol, ansi = _RESULT_PREFIXES.get(kind, ("→", CYAN))
    return f"{color(symbol, ansi)} {text}"


def diff_header(path, adds, dels):
    """Colored 'path  +N -M' header line (green/red counts)."""
    return f"  {yellow(path)}  {green(f'+{adds}')} {red(f'-{dels}')}"


def wrap(text, prefix="  "):
    """Indent a multi-line string with the prefix (for model replies)."""
    return "\n".join(prefix + ln for ln in (text or "").split("\n"))
