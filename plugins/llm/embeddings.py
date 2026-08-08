"""Semantic-search embeddings for the copilot — local Ollama /api/embed
client with zero extra dependencies (stdlib urllib only).

Ollama's natively supported embedding models are the fallback list here;
they are ordered flagship → low dimension so the default (nomic-embed-text,
768-dim) can be swapped down to all-minilm (384-dim) for leaner indexes:

  embedding_models()        — recommended fallback list (4 models)
  ollama_embed()            — one-shot embed via POST /api/embed
  embed_available()         — endpoint + default model health probe
  cosine()                  — vector similarity (pure math, numpy optional)
  recommend_embed_line()    — YELLOW install hint for the REPL
  recommend_compression_line() — YELLOW hint for the context-compression model
"""

import json
import urllib.request
import urllib.error

from .ui import yellow

# ── recommended model list ──

EMBEDDING_MODELS = ["nomic-embed-text", "all-minilm",
                    "mxbai-embed-large", "bge-m3"]


def embedding_models():
    """Fallback list of the recommended Ollama embedding models.

    Ordered flagship → low dimension (nomic-embed-text 768-dim vectors down
    to all-minilm's 384-dim): pick the first your hardware indexes fine."""
    return list(EMBEDDING_MODELS)


# ── /api/embed client ──

OLLAMA_BASE = "http://127.0.0.1:11434"


def _post_json(url, payload, timeout):
    """POST JSON, return (status, data_dict_or_none, error_string_or_None)."""
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            try:
                return resp.status, json.loads(raw), None
            except Exception:
                return resp.status, None, None
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8", errors="replace"))
        except Exception:
            detail = None
        return e.code, detail, None
    except Exception as e:
        return None, None, str(e)


def ollama_embed(text, model="nomic-embed-text", base=OLLAMA_BASE, timeout=10):
    """Embed `text` via the local Ollama /api/embed endpoint.

    Returns (vector, None) on success — a list of floats — and
    (None, err_string) when the server is unreachable or replies with an
    error, matching the (result, err) convention of providers.chat_request."""
    status, data, err = _post_json(
        base.rstrip("/") + "/api/embed", {"model": model, "input": text},
        timeout)
    if err:
        return None, err
    if status != 200 or not isinstance(data, dict):
        return None, f"HTTP {status}"
    embeddings = data.get("embeddings") or []
    if not embeddings:
        return None, "no embeddings in response"
    return list(embeddings[0]), None


def embed_available(base=OLLAMA_BASE, timeout=3):
    """True when the Ollama server answers /api/embed with an embedding
    (default model pulled). Connection errors and model-missing 404s are
    both 'not available'."""
    _, data, err = _post_json(
        base.rstrip("/") + "/api/embed",
        {"model": EMBEDDING_MODELS[0], "input": ""}, timeout)
    return err is None and isinstance(data, dict) and bool(data.get("embeddings"))


# ── similarity ──

def cosine(a, b):
    """Cosine similarity of two vectors — pure math by default, numpy used
    when it happens to be installed. Zero vectors score 0.0."""
    try:
        import numpy as np
        va = np.asarray(a, dtype=float)
        vb = np.asarray(b, dtype=float)
        na = np.linalg.norm(va)
        nb = np.linalg.norm(vb)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(va, vb) / (na * nb))
    except ImportError:
        pass
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(y * y for y in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ── YELLOW recommendation lines (REPL hints) ──

def recommend_embed_line():
    """YELLOW one-liner recommending the default embedding model + list."""
    return yellow(
        "embedding: install 'ollama pull nomic-embed-text' for semantic "
        "search (fallback list: " + ", ".join(EMBEDDING_MODELS) + ")")


def recommend_compression_line():
    """YELLOW one-liner recommending the context-compression model
    (for >6GB VRAM users who can afford a 1.5B MoE)."""
    return yellow(
        "compression: 'ollama pull huihui-ai/Huihui-MoE-1B-A0.6B' for "
        "context compression (>6GB VRAM)")
