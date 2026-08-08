"""Ollama (local) and OpenAI-compatible (cloud) model support."""

import json
import os
import urllib.request
import urllib.error

from .config import OLLAMA_HOST

# OpenAI-compatible config (set via environment variables)
OPENAI_BASE_URL = os.environ.get("E_OPENAI_URL", "")
OPENAI_API_KEY = os.environ.get("E_OPENAI_KEY", "")
CLOUD_MAX_TOKENS = 32768  # Auto-scaled for large models

# Browser-matching headers to bypass Cloudflare 403
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/json",
}

# ── Ollama (local) ───────────────────────────

def ollama_request(method, path, data=None, stream=False):
    url = f"{OLLAMA_HOST}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        return urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        return e
    except urllib.error.URLError:
        return None


def list_ollama_models():
    resp = ollama_request("GET", "/api/tags")
    if not resp or resp.status != 200:
        return []
    try:
        data = json.loads(resp.read())
        return [m["name"] for m in data.get("models", [])]
    except (json.JSONDecodeError, KeyError):
        return []


def ollama_generate(prompt, system="", stream=True):
    from .config import MODEL
    data = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": stream,
        "options": {"num_predict": 4096, "temperature": 0.7},
    }
    resp = ollama_request("POST", "/api/generate", data, stream=stream)
    if not resp or resp.status != 200:
        err = resp.read().decode() if resp else "Connection refused"
        return None, err
    if stream:
        return resp, None
    result = json.loads(resp.read())
    return result.get("response", ""), None


def stream_ollama(prompt, system=""):
    gen = ollama_generate(prompt, system, stream=True)
    if gen is None or (isinstance(gen, tuple) and gen[1]):
        yield ("error", gen[1] if isinstance(gen, tuple) else "Failed")
        return
    resp = gen[0] if isinstance(gen, tuple) else gen
    full = ""
    for line in resp:
        line = line.decode().strip()
        if not line:
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        token = data.get("response", "")
        full += token
        yield ("token", token)
        if data.get("done"):
            break
    yield ("done", full)


# ── OpenAI-compatible (cloud) ────────────────

def _openai_req(method, path, data=None, stream=False):
    """Make request with proper browser headers to bypass Cloudflare."""
    url = f"{OPENAI_BASE_URL}{path}"
    headers = {**BROWSER_HEADERS, "Authorization": f"Bearer {OPENAI_API_KEY}"}
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        return urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        return e
    except urllib.error.URLError as e:
        return None


def openai_list_models():
    if not OPENAI_API_KEY:
        return []
    resp = _openai_req("GET", "/models")
    if not resp or resp.status != 200:
        return ["deepseek-v4-flash"]
    try:
        data = json.loads(resp.read())
        return [m["id"] for m in data.get("data", [])]
    except (json.JSONDecodeError, KeyError):
        return ["deepseek-v4-flash"]


def openai_chat(messages, stream=True):
    from .config import MODEL
    data = {
        "model": MODEL,
        "messages": messages,
        "stream": stream,
        "max_tokens": CLOUD_MAX_TOKENS,
        "temperature": 0.7,
    }
    resp = _openai_req("POST", "/chat/completions", data, stream=stream)
    if not resp or resp.status != 200:
        err = resp.read().decode() if hasattr(resp, 'read') else str(resp)
        return None, err

    if stream:
        return resp, None
    result = json.loads(resp.read())
    return result["choices"][0]["message"]["content"], None


def stream_openai(messages):
    gen = openai_chat(messages, stream=True)
    if gen is None or (isinstance(gen, tuple) and gen[1]):
        yield ("error", gen[1] if isinstance(gen, tuple) else "Failed")
        return
    resp = gen[0] if isinstance(gen, tuple) else gen
    full = ""
    for line in resp:
        line = line.decode().strip()
        if not line:
            continue
        if line.startswith("data: "):
            line = line[6:]
        if line == "[DONE]":
            break
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "choices" not in data:
            continue
        choices = data["choices"]
        if not choices or "delta" not in choices[0]:
            continue
        delta = choices[0]["delta"]
        token = delta.get("content", "")
        if token:
            full += token
            yield ("token", token)
    yield ("done", full)


# ── Unified interface ────────────────────────

def is_cloud_model(model_name):
    return "/" not in model_name


def stream_generate(prompt, system=""):
    from .config import MODEL

    if is_cloud_model(MODEL):
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        yield from stream_openai(messages)
    else:
        yield from stream_ollama(prompt, system)
