"""Auto-compact engine — context windows per provider/model, usage
metering, and chunked conversation compression for long copilot sessions.

- context_window(provider, model) → max tokens (ollama name regexes,
  openai/claude/deepseek/glm tables, custom default); set_window /
  get_window provide a module-level override map for diagnostics
- usage_tokens / should_compact / render_meter — metering over the message
  history (reuses plugins.llm.costs.estimate_tokens, lazily imported)
- compact_history(history, model_fn, ...) — the core: splits the old turns
  into chunks, summarizes each chunk in its own model_fn call (so every
  call stays small), keeps system + recent turns verbatim, falls back to
  raw turns when a chunk errors, and retries once with tighter summaries
  when the result still exceeds the target
- compression_model_recommend / recommend_line — the recommended
  compression model (huihui-ai/Huihui-MoE-1B-A0.6B, a 1B MoE that fits
  low VRAM), advertised via a YELLOW recommendation line
"""

import re

from . import ui

# ── provider/model context windows ────────────────

OVERRIDES = {}  # (provider, model) -> forced window (module override map)


def _ollama_window(model):
    """Ollama windows from the model name. A 'Nk' in the name overrides
    every family rule (deepseek-r1-64k → 65536); gemma3:27b is the one
    131072-capable variant, the rest of gemma3 is 32k."""
    m = model or ""
    k = re.search(r"(\d+)k", m)
    if k:
        return int(k.group(1)) * 1024
    if "llama3" in m:
        return 8192
    if "qwen2.5" in m:
        return 32768
    if "deepseek-r1" in m:
        return 65536
    if "gemma3" in m:
        return 131072 if ":27b" in m else 32768
    if "mistral" in m:
        return 32768
    if "phi" in m:
        return 8192
    return 8192


def _openai_window(model):
    m = model or ""
    if "gpt-4o" in m:
        return 128000
    if "gpt-4.1" in m:
        return 1047576
    if m.startswith(("o1", "o3", "o4")):
        return 200000
    if "gpt-4" in m:
        return 8192
    return 128000


def _claude_window(model):
    return 200000


def _deepseek_window(model):
    return 131072 if "v4" in (model or "") else 65536


def _glm_window(model):
    m = model or ""
    if "glm-4" in m and "glm-4.5" not in m:
        return 128000
    return 131072


def context_window(provider, model):
    """Max context tokens for (provider, model). Overrides win, then the
    provider table; custom/unknown providers default to 32768."""
    key = ((provider or "").strip().lower(), (model or "").strip().lower())
    if key in OVERRIDES:
        return OVERRIDES[key]
    provider_, model_ = key
    if provider_ == "ollama":
        return _ollama_window(model_)
    if provider_ == "openai":
        return _openai_window(model_)
    if provider_ == "claude":
        return _claude_window(model_)
    if provider_ == "deepseek":
        return _deepseek_window(model_)
    if provider_ == "glm":
        return _glm_window(model_)
    return 32768


def set_window(provider, model, tokens):
    """Force a window for (provider, model) in the module override map."""
    key = ((provider or "").strip().lower(), (model or "").strip().lower())
    OVERRIDES[key] = int(tokens)


def get_window(provider, model):
    """Effective window for (provider, model) incl. any override —
    the diagnostics entry point."""
    return context_window(provider, model)


# ── usage metering ─────────────────────────────────

def usage_tokens(history):
    """Total token estimate for a message list (lazy-imported costs)."""
    from . import costs
    return costs.estimate_tokens(history)


def should_compact(history, window, threshold=0.9):
    """True when usage_tokens/window crosses the threshold (>=)."""
    try:
        window = int(window)
    except (TypeError, ValueError):
        window = 0
    if window <= 0:
        return False
    return usage_tokens(history) >= window * threshold


def _fmt_tokens(n):
    try:
        n = int(n or 0)
    except (TypeError, ValueError):
        n = 0
    if n < 1000:
        return str(n)
    return f"{n / 1000.0:.1f}k".replace(".0k", "k")


def render_meter(history, window):
    """Grey one-liner: 'tokens: 12.4k/128k · context 10%'
    (ui.dim — plain text off-TTY)."""
    used = usage_tokens(history)
    try:
        window = int(window)
    except (TypeError, ValueError):
        window = 0
    pct = used / window * 100 if window > 0 else 0
    return ui.dim(f"tokens: {_fmt_tokens(used)}/{_fmt_tokens(window)} "
                  f"· context {pct:.0f}%")


# ── chunked compression ────────────────────────────

SUMMARY_PROMPT = (
    "Compress these conversation turns into dense notes. Keep: decisions, "
    "file paths, error messages, code identifiers, user requirements. "
    "Drop: pleasantries, repetition. Output \u2264 400 tokens."
)

SHORT_MEMORY_PROMPT = (
    "Compress these turns into a short-term memory summary of at most 25% "
    "of the original token count. Keep: decisions, file paths, error "
    "messages, code identifiers, user requirements. Drop: pleasantries, "
    "repetition. Output \u2264 400 tokens."
)

_COMPRESSED_HEADER = "Compressed context of earlier turns:"
_TIGHTER = ("\n\nBe even more terse: single-line bullets only, "
            "no more than 150 tokens.")
_FALLBACK_RAW = 2  # messages kept verbatim when a chunk's summary fails
_FILE_RE = re.compile(r"\b[\w./-]+\.(?:py|md|e|txt|json|ya?ml|toml|ini|sh|"
                      r"c|h|cpp|go|rs|js|ts)\b")


def _msg_text(message):
    content = (message or {}).get("content")
    if isinstance(content, list):  # Anthropic-style text blocks
        return " ".join(str(b.get("text", ""))
                        for b in content if isinstance(b, dict))
    return str(content or "")


def _render_turn(message):
    return f"{(message or {}).get('role', 'user')}: {_msg_text(message)}"


def summary_prompt(chunk):
    """Full summarization prompt for one chunk: template + rendered turns."""
    turns = "\n\n".join(_render_turn(m) for m in chunk)
    return f"{SUMMARY_PROMPT}\n\nCONVERSATION TURNS:\n{turns}"


def _chunk_messages(messages, size, max_chunks):
    """Split into chunks of `size` messages; when that exceeds max_chunks,
    merge to bigger chunks so at most max_chunks summarization calls run."""
    size = max(1, int(size))
    n = len(messages)
    if max_chunks and (n + size - 1) // size > max_chunks:
        size = max(1, (n + max_chunks - 1) // max_chunks)
    return [messages[i:i + size] for i in range(0, n, size)]


def _file_notes(messages):
    """Distinct file paths mentioned in the old turns, as one note line."""
    found = []
    for m in messages:
        for path in _FILE_RE.findall(_msg_text(m)):
            if path not in found:
                found.append(path)
    if not found:
        return ""
    return "Files touched: " + ", ".join(found[:20])


def _split_system(history):
    """First system message (if any) is the untouched head; the rest is
    the compressible conversation."""
    history = list(history or [])
    if history and str(history[0].get("role", "")).strip().lower() == "system":
        return [history[0]], history[1:]
    return [], history


def _compress(head, rest, model_fn, keep_recent, chunk_size, max_chunks, tight):
    """One compression pass: chunk the old turns, summarize each chunk in
    its own model_fn call, and compose
    [system] + [compressed-context system msg] + recent."""
    old, recent = rest[:-keep_recent], rest[-keep_recent:]
    chunks = _chunk_messages(old, chunk_size, max_chunks)
    pieces = []
    for i, chunk in enumerate(chunks):
        prompt = summary_prompt(chunk)
        if tight:
            prompt += _TIGHTER
        try:
            result = model_fn([{"role": "user", "content": prompt}])
        except Exception as e:  # never lose the turn silently
            result = (None, str(e))
        text, err = result if isinstance(result, tuple) else (result, None)
        if text and not err:
            pieces.append(f"### Chunk {i + 1}\n{str(text).strip()}")
        else:
            raw = "\n".join(_render_turn(m) for m in chunk[:_FALLBACK_RAW])
            pieces.append(f"### Chunk {i + 1} (summarization failed — "
                          f"raw turns kept)\n{raw}")
    notes = _file_notes(old)
    if notes:
        pieces.append(notes)
    block = _COMPRESSED_HEADER + "\n\n" + "\n\n".join(pieces) + "\n"
    new_history = list(head) + [{"role": "system", "content": block}] \
        + list(recent)
    return new_history, len(chunks), usage_tokens(new_history)


def compact_history(history, model_fn, window, threshold=0.9, target=0.75,
                    keep_recent=6, chunk_size=6, max_chunks=6):
    """Compress an over-threshold message list via chunked summarization.

    model_fn(messages) returns the reply text, or a (text, err) tuple like
    providers.chat_request. Each chunk is summarized in its own call so
    every call stays small. Returns (new_history, stats) with stats =
    {tokens_before, tokens_after, chunks, ratio, ok, compacted}. Under the
    threshold the original history is returned untouched; when the result
    still exceeds window*target a second pass runs with keep_recent=4 and
    tighter per-chunk summaries."""
    before = usage_tokens(history)
    if window <= 0 or before < window * threshold:
        stats = {"tokens_before": before, "tokens_after": before,
                 "chunks": 0, "ratio": 1.0, "ok": True, "compacted": False}
        return history, stats
    head, rest = _split_system(history)
    if len(rest) <= keep_recent:  # nothing old to compress
        stats = {"tokens_before": before, "tokens_after": before,
                 "chunks": 0, "ratio": 1.0, "ok": True, "compacted": False}
        return history, stats
    new_history, chunks, tokens_after = history, 0, before
    for tight in (False, True):
        kr = keep_recent if not tight else min(4, keep_recent)
        new_history, chunks, tokens_after = _compress(
            head, rest, model_fn, kr, chunk_size, max_chunks, tight)
        if tokens_after <= window * target or not chunks:
            break
    ratio = tokens_after / before if before else 1.0
    stats = {"tokens_before": before, "tokens_after": tokens_after,
             "chunks": chunks, "ratio": round(ratio, 4),
             "ok": tokens_after <= window * target or chunks == 0,
             "compacted": True}
    return new_history, stats


# ── compression model recommendation ───────────────

COMPRESSION_MODEL = "huihui-ai/Huihui-MoE-1B-A0.6B"


def compression_model_recommend():
    """The recommended compression model (1B MoE — fits any VRAM class)."""
    return COMPRESSION_MODEL


def recommend_line():
    """YELLOW one-liner recommending the compression model (plain off-TTY)."""
    return ui.yellow(f"recommended: {COMPRESSION_MODEL} for compression "
                     f"(low VRAM)")
