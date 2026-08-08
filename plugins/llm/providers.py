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

def chat_request(provider, base_url, api_key, model, messages, timeout=300):
    """Send a chat completion. Returns (text, error).
    provider: openai|anthropic|ollama (all use the OpenAI-compatible /chat/
    completions shape except anthropic which uses /v1/messages).
    Default timeout 300s — local models can be slow to warm up."""
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
        "temperature": _temp_for(provider, model),
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


def _temp_for(provider, model):
    """Small/local models need determinism: temperature 0.1."""
    m = (model or "").lower()
    if provider == "ollama":
        return 0.1
    if any(t in m for t in ("3b", "4b", "0.5b", "1.5b", "tiny", "mini", "small")):
        return 0.1
    return 0.2


# ── Streaming chat (SSE / NDJSON) ──────────────

def _stream_lines(resp):
    """Yield decoded lines from an HTTP response as they arrive."""
    try:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                yield line
    except Exception:
        return


def stream_chat(provider, base_url, api_key, model, messages, on_chunk,
                timeout=300):
    """Stream a chat completion. on_chunk(text) is called per delta.
    Returns (full_text, err, thinking) — thinking accumulates
    reasoning/thinking deltas (anthropic thinking_delta / ollama
    message.thinking) where the backend provides them."""
    provider = (provider or "custom").lower()
    full = []
    thinking = []

    def _emit(t):
        if t:
            full.append(t)
            try:
                on_chunk(t)
            except Exception:
                pass

    def _emit_thinking(t):
        if t:
            thinking.append(t)

    if provider == "anthropic":
        url = (base_url or PROVIDERS["claude"]["base_url"]).rstrip("/") + "/messages"
        headers = {"x-api-key": api_key or "", "anthropic-version": "2023-06-01",
                   "content-type": "application/json"}
        sys_text = "\n".join(m["content"] for m in messages if m["role"] == "system")
        conv = [m for m in messages if m["role"] != "system"]
        payload = {"model": model, "max_tokens": 4096, "stream": True,
                   "messages": conv}
        if sys_text:
            payload["system"] = sys_text
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                for line in _stream_lines(resp):
                    if not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        ev = json.loads(data)
                    except Exception:
                        continue
                    etype = ev.get("type")
                    if etype == "content_block_delta":
                        dt = ev.get("delta", {})
                        if dt.get("type") == "text_delta":
                            _emit(dt.get("text", ""))
                        elif dt.get("type") == "thinking_delta":
                            _emit_thinking(dt.get("thinking", ""))
        except Exception as e:
            return "".join(full), str(e), "".join(thinking)
        return "".join(full), None, "".join(thinking)

    # ollama native
    if provider == "ollama" and base_url and "11434" in base_url \
            and "/v1" not in (base_url or ""):
        url = base_url.rstrip("/") + "/api/chat"
        payload = {"model": model, "stream": True, "messages": messages}
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                for line in _stream_lines(resp):
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    msg = obj.get("message", {})
                    if msg.get("thinking"):
                        _emit_thinking(msg["thinking"])
                    if msg.get("content"):
                        _emit(msg["content"])
                    if obj.get("done"):
                        break
        except Exception as e:
            return "".join(full), str(e), "".join(thinking)
        return "".join(full), None, "".join(thinking)

    # openai-compatible SSE
    url = (base_url or PROVIDERS["openai"]["base_url"]).rstrip("/") + "/chat/completions"
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    payload = {"model": model, "messages": messages, "temperature": _temp_for(provider, model),
               "stream": True}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={**headers, "Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            for line in _stream_lines(resp):
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    obj = json.loads(data)
                except Exception:
                    continue
                try:
                    delta = obj["choices"][0]["delta"]
                except (KeyError, IndexError, TypeError):
                    continue
                if delta.get("reasoning_content"):
                    _emit_thinking(delta["reasoning_content"])
                if delta.get("content"):
                    _emit(delta["content"])
    except Exception as e:
        return "".join(full), str(e), "".join(thinking)
    return "".join(full), None, "".join(thinking)
