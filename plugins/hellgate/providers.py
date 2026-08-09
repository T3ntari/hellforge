"""Hellgate provider registry — ollama is ONE option, never the default.

A provider is chosen in the session ($provider / $model) and persisted in
hellgate-state/session.json. Before every tool launch the session writes
hellgate-state/provider.json, which the tool modules translate into their
own config format:

    {
      "id": "ollama",            # one of PROVIDERS[*]["id"]
      "name": "Ollama (local)",
      "model": "qwen2.5-coder:3b",
      "base_url": "http://127.0.0.1:11434/v1",   # null for official APIs
      "api_key": "sk-..." | null
    }

Default resolution: the FIRST provider in the registry whose API key is set
in the environment (or, for local providers, that is actually reachable).
Ollama sits LAST in the registry — it only becomes the default when no
other provider is configured at all.
"""

import json
import os
import urllib.request

# Registry order matters: first-available wins the default. Ollama last.
PROVIDERS = [
    {"id": "anthropic", "name": "Anthropic", "env_key": "ANTHROPIC_API_KEY",
     "model": "claude-sonnet-4-5", "base_url": None},
    {"id": "openai", "name": "OpenAI", "env_key": "OPENAI_API_KEY",
     "model": "gpt-4o-mini", "base_url": None},
    {"id": "openrouter", "name": "OpenRouter", "env_key": "OPENROUTER_API_KEY",
     "model": "qwen/qwen-2.5-coder-32b-instruct",
     "base_url": "https://openrouter.ai/api/v1"},
    {"id": "google", "name": "Google Gemini", "env_key": "GEMINI_API_KEY",
     "model": "gemini-2.0-flash", "base_url": None},
    {"id": "custom", "name": "Custom (OpenAI-compatible)", "env_key": None,
     "model": None, "base_url": None},
    {"id": "ollama", "name": "Ollama (local)", "env_key": None,
     "model": "qwen2.5-coder:3b", "base_url": "http://127.0.0.1:11434/v1"},
]

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434/v1"


def by_id(pid):
    for p in PROVIDERS:
        if p["id"] == pid:
            d = dict(p)
            d["api_key"] = os.environ.get(p["env_key"]) if p["env_key"] else None
            return d
    return None


def _ollama_up(url):
    root = url.rstrip("/")
    if root.endswith("/v1"):
        root = root[:-3]  # /api/tags lives on the ollama root, not /v1
    for cand in (f"{root}/api/tags", f"{url.rstrip('/')}/api/tags"):
        try:
            urllib.request.urlopen(cand, timeout=2)
            return True
        except Exception:
            continue
    return False


def available(provider=None):
    """available(provider) -> bool. Without arg: list of (provider, available)."""
    if provider is not None:
        p = by_id(provider)
        if p is None:
            return False
        if p["env_key"]:
            return bool(os.environ.get(p["env_key"]))
        if p["id"] == "ollama":
            return _ollama_up(os.environ.get("HELLGATE_OLLAMA_URL", p["base_url"]))
        return True  # custom
    return [(p, available(p["id"])) for p in PROVIDERS]


def resolve_default():
    """First configured provider; ollama only as last-resort fallback."""
    for p, ok in available():
        if ok:
            return dict(p)
    return dict(by_id("ollama"))


def provider_json_path(project_dir):
    return os.path.join(project_dir, "hellgate-state", "provider.json")


def write_provider_json(project_dir, provider):
    path = provider_json_path(project_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(provider, f, indent=2)
    return path


def read_provider_json(project_dir):
    """Current provider as a dict, or None when nothing was ever written."""
    try:
        with open(provider_json_path(project_dir)) as f:
            return json.load(f)
    except Exception:
        return None
