"""LLM provider registry — OpenAI-compatible (custom URL), DeepSeek, Claude,
and native Ollama detection. Zero extra dependencies (stdlib urllib only)."""

import json
import os
import urllib.request
import urllib.error

# ── Provider definitions ────────────────────────

PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3-mini"],
        "api": "openai",
    },
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v4"],
        "api": "openai",
    },
    "claude": {
        "label": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "models": ["claude-sonnet-4-5", "claude-opus-4-1", "claude-haiku-4-5"],
        "api": "anthropic",
    },
    "ollama": {
        "label": "Ollama (local)",
        "base_url": "http://127.0.0.1:11434",
        "models": [],  # discovered at runtime from the local server
        "api": "ollama",
    },
    "custom": {
        "label": "Custom (OpenAI-compatible)",
        "base_url": "",
        "models": [],
        "api": "openai",
    },
}

DEFAULT_MODEL = {
    "openai": "gpt-4o-mini",
    "deepseek": "deepseek-chat",
    "claude": "claude-sonnet-4-5",
    "ollama": None,
    "custom": None,
}


def _http_json(url, payload=None, headers=None, method=None, timeout=60):
    """Stdlib JSON HTTP helper. Returns (status, data_dict_or_none, error)."""
    req = urllib.request.Request(url, headers=headers or {}, method=method)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        req.data = body
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


# ── Ollama native support ───────────────────────

OLLAMA_HEAD = "http://127.0.0.1:11434"


def ollama_detected(timeout=2):
    """True when a local Ollama server answers on the default port."""
    status, _, err = _http_json(OLLAMA_HEAD + "/api/version", timeout=timeout)
    return status is not None and err is None


def ollama_models(timeout=5):
    """List locally installed Ollama models via the native /api/tags endpoint."""
    status, data, err = _http_json(OLLAMA_HEAD + "/api/tags", timeout=timeout)
    if status is None or not data:
        return []
    return [m.get("name") for m in data.get("models", []) if m.get("name")]


# ── Unified chat request ────────────────────────

def chat_request(provider, base_url, api_key, model, messages, timeout=120):
    """Send a chat completion. Returns (text, error).
    provider: openai|anthropic|ollama (all use the OpenAI-compatible /chat/
    completions shape except anthropic which uses /v1/messages)."""
    provider = (provider or "custom").lower()

    if provider == "anthropic":
        url = (base_url or PROVIDERS["claude"]["base_url"]).rstrip("/") + "/messages"
        headers = {
            "x-api-key": api_key or "",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        # Convert OpenAI-style messages to Anthropic's user/assistant form
        sys_text = "\n".join(m["content"] for m in messages if m["role"] == "system")
        conv = [m for m in messages if m["role"] != "system"]
        payload = {
            "model": model,
            "max_tokens": 4096,
            "messages": conv,
        }
        if sys_text:
            payload["system"] = sys_text
        status, data, err = _http_json(url, payload, headers, timeout=timeout)
        if err:
            return None, err
        if status != 200:
            msg = data.get("error", {}).get("message") if isinstance(data, dict) else None
            return None, msg or f"HTTP {status}"
        blocks = data.get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text"), None

    # OpenAI-compatible: openai / deepseek / custom / ollama(/v1)
    url = (base_url or PROVIDERS["openai"]["base_url"]).rstrip("/") + "/chat/completions"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    status, data, err = _http_json(url, {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }, headers, timeout=timeout)
    if err:
        return None, err
    if status != 200:
        msg = None
        if isinstance(data, dict):
            e = data.get("error")
            msg = e.get("message") if isinstance(e, dict) else str(e)
        return None, msg or f"HTTP {status}"
    try:
        return data["choices"][0]["message"]["content"], None
    except (KeyError, IndexError, TypeError):
        return None, "Unexpected response shape"
