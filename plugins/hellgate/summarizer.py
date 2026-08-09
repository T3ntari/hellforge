"""hellgate.summarizer — low-context summarizer.

When an agent session's context runs low (~75%), a small local model
(Qwen2.5-Coder-3B via ollama) summarizes the HELLFORGE docs into a compact
key-points digest so the agent keeps working without blowing the context
budget. Also provides token / context-fraction helpers.

stdlib + httpx only (httpx imported lazily).
"""

import os
import tempfile

DEFAULT_MODEL = "hf.co/bartowski/Qwen2.5-Coder-3B-Instruct-Abliterated-GGUF:latest"
OLLAMA_URL = os.environ.get("HELLGATE_OLLAMA_URL", "http://127.0.0.1:11434/v1")
CONTEXT_BUDGET = 128_000
MAX_DOC_CHARS = 18_000
TIMEOUT_SEC = 70
DIGEST_PROMPT = (
    "Summarize these HELLFORGE E Language docs into the most important "
    "points, markdown bullets, keep all statement names and commands, "
    "~200-300 words."
)

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT = os.path.dirname(os.path.dirname(_HERE))
KNOWLEDGE_DIR = os.path.join(_HERE, "knowledge")
AGENT_DOC_DIR = os.path.join(_PROJECT, "docs", "agent")
KNOWLEDGE_FILES = ("full.md", "samples-index.md")
FALLBACK_DOC = "quickstart.md"
DIGEST_PATH = os.path.join(KNOWLEDGE_DIR, "core-llm.md")


def tokens(text):
    """Rough token estimate, ~4 chars per token, deterministic."""
    return max(1, len(text or "") // 4)


def context_fraction(history, budget=CONTEXT_BUDGET):
    """Estimate the used fraction of a context budget from a message list.

    history: list of dicts with "role"/"content". Guarded against a
    zero/negative budget and missing content keys.
    """
    if budget <= 0:
        return 0.0
    total = 0
    for msg in history or []:
        if not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if content:
            total += tokens(content)
    return min(1.0, total / budget)


def needs_digest(history, threshold=0.75):
    """True when the estimated context usage is at or above threshold."""
    if threshold < 0:
        threshold = 0.0
    if threshold >= 1.0:
        return False
    return context_fraction(history) >= threshold


def _read_docs():
    """Concatenate the HELLFORGE docs, truncated to ~18000 chars.

    Missing files are skipped. Order: knowledge/full.md,
    knowledge/samples-index.md, then docs/agent/*.md sorted by name.
    """
    parts = []
    seen = set()
    for name in KNOWLEDGE_FILES:
        path = os.path.join(KNOWLEDGE_DIR, name)
        if os.path.isfile(path):
            seen.add(path)
            parts.append("===== %s =====\n" % name)
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                parts.append(fh.read())
    try:
        names = sorted(os.listdir(AGENT_DOC_DIR))
    except OSError:
        names = []
    for name in names:
        if not name.endswith(".md"):
            continue
        path = os.path.join(AGENT_DOC_DIR, name)
        if path in seen or not os.path.isfile(path):
            continue
        parts.append("===== docs/agent/%s =====\n" % name)
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            parts.append(fh.read())
    text = "\n".join(parts)
    return text[:MAX_DOC_CHARS]


def make_digest(api=None, model=DEFAULT_MODEL, url=None, max_tokens=900):
    """Summarize the HELLFORGE docs with the small local model.

    Returns the model's answer text. On any failure or timeout (10s),
    falls back to the first chars of docs/agent/quickstart.md as a minimal
    digest. Never raises.
    """
    base = url or OLLAMA_URL
    docs = _read_docs()
    messages = [
        {"role": "system", "content": "You are a terse summarizer."},
        {"role": "user", "content": docs + "\n\n" + DIGEST_PROMPT},
    ]
    try:
        if api is not None and callable(getattr(api, "chat_request", None)):
            text, err = api.chat_request(
                "ollama", base, None, model, messages, timeout=TIMEOUT_SEC)
            if not err and text:
                return text.strip()
        else:
            data = _http_post_json(
                base.rstrip("/") + "/chat/completions",
                {
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.1,
                },
                timeout=TIMEOUT_SEC,
            )
            text = data["choices"][0]["message"]["content"]
            if text:
                return text.strip()
    except Exception:
        pass
    return _fallback_digest()


def _http_post_json(url, payload, timeout):
    """POST JSON, return parsed response dict.

    Prefers httpx (imported lazily); falls back to stdlib urllib when
    httpx is unavailable in the current interpreter.
    """
    import json
    body = json.dumps(payload).encode("utf-8")
    try:
        import httpx
    except ImportError:
        httpx = None
    if httpx is not None:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, content=body, headers={
                "Content-Type": "application/json"})
            resp.raise_for_status()
            return resp.json()
    import urllib.request
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _fallback_digest():
    """Minimal digest: first chars of docs/agent/quickstart.md."""
    path = os.path.join(AGENT_DOC_DIR, FALLBACK_DOC)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read().strip()[:MAX_DOC_CHARS]
    except Exception:
        return "HELLFORGE digest unavailable (docs missing, ollama offline)."


def build_digest_file(path=None):
    """Write the LLM digest to knowledge/core-llm.md via temp + atomic rename.

    Never overwrites the hand-written knowledge/core.md. Returns the
    written path, or "" on failure.
    """
    target = path or DIGEST_PATH
    try:
        digest = make_digest()
        if not digest:
            return ""
        target_dir = os.path.dirname(target) or "."
        fd, tmp = tempfile.mkstemp(
            prefix=".core-llm-", suffix=".md.tmp", dir=target_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(digest)
                if not digest.endswith("\n"):
                    fh.write("\n")
            os.replace(tmp, target)
        except Exception:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
        return target
    except Exception:
        return ""
