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


# ── Claude-Code-style status bar + tool headers (T10) ──

MODE_BADGE_COLORS = {"plan": YELLOW, "auto": GREEN, "ask": CYAN}


def mode_badge(mode):
    """Mode badge for the prompt: (plan) yellow, (auto) green, (ask) cyan."""
    ansi = MODE_BADGE_COLORS.get(mode, DIM)
    return color(f"({mode})", ansi)


def _fmt_tokens(n):
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        n = 0
    return f"{n / 1000.0:.1f}k" if n >= 1000 else f"{n}"


def status_bar(state, stats):
    """Dim one-line session status (Claude Code style):
    'model: gemma3:4b · mode: auto · tokens: 12.4k · cost: $0.0012 · context: 8%'
    stats: {tokens, cost, context} — context as a 0..1 fraction or percent."""
    stats = stats or {}
    parts = [
        f"model: {state.get('model') or '?'}",
        f"mode: {state.get('mode') or 'auto'}",
        f"tokens: {_fmt_tokens(stats.get('tokens', 0))}",
        f"cost: ${float(stats.get('cost', 0.0) or 0.0):.4f}",
    ]
    ctx = stats.get("context")
    if isinstance(ctx, (int, float)):
        pct = ctx * 100 if ctx <= 1.0 else ctx
        parts.append(f"context: {pct:.0f}%")
    else:
        parts.append("context: ?")
    return dim(" · ".join(parts))


_TOOL_SYMBOLS = {"plan": "✻", "edit": "●", "write": "✎", "read": "▤",
                 "test": "✓", "run": "▶", "todo": "✓", "done": "✓"}


def tool_call(title, kind=""):
    """Print a Claude Code tool header: '✻ plan · eshell.py' or '● edit'.
    The caller prints the tool body on the following lines."""
    symbol = _TOOL_SYMBOLS.get(title, "●")
    head = f" {symbol} {bold(title)}"
    if kind:
        head += f" {dim('· ' + str(kind))}"
    print(head)


def result_block(text):
    """Print a ──-ruled block: dim rule, indented text, closing rule."""
    rule = dim("─" * 60)
    print(rule)
    print(wrap(text or "", prefix="  "))
    print(rule)


def error_line(text):
    """Colored red single-line error."""
    print(red(text))


def warn_line(text):
    """Colored yellow single-line warning."""
    print(yellow(text))


def elapsed(seconds):
    """Dim turn-timing tag, e.g. '(0.8s)'."""
    return dim(f"({seconds:.1f}s)")


# ── T13: thinking tags + turn summary chrome ──


def thinking_collapsed(seconds):
    """Dim auto-collapsed thinking one-liner: 'thought for 12.3s'."""
    try:
        from plugins.llm import thinking as _thinking
        line = _thinking.collapse([], seconds)
    except Exception:
        line = f"thought for {seconds:.1f}s"
    return dim(line)


def explored(files, edits, commands):
    """Dim turn-summary line:
    'explored 3 files · 2 edits · 1 command' (non-zero parts only)."""
    try:
        from plugins.llm import thinking as _thinking
        line = _thinking.explored_line(files, edits, commands)
    except Exception:
        parts = []
        if files:
            parts.append(f"{files} file" + ("" if files == 1 else "s"))
        if edits:
            parts.append(f"{edits} edit" + ("" if edits == 1 else "s"))
        if commands:
            parts.append(f"{commands} command" + ("" if commands == 1 else "s"))
        line = f"explored {' · '.join(parts)}" if parts else ""
    return dim(line)
