"""HELLFORGE Copilot — LLM plugin (OpenAI-compatible, DeepSeek, Claude,
Ollama native). Agentic edits with confirmation, plugin generation, chat.

Commands (eshell + run.py):
  ai status                     — provider/model/connection
  ai provider <name>            — openai | deepseek | claude | ollama | custom
  ai model [name]               — list known models / set model
  ai url <base_url>             — custom base URL (OpenAI-compatible)
  ai key <api_key>              — set API key (stored in local config)
  ai connect                    — mark connected (auto after provider/model)
  ai disconnect                 — disconnect without forgetting config
  ai ask "<question>"           — single-shot answer
  ai chat                       — interactive REPL chat (Ctrl-C / 'quit' to exit)
  ai fix "<issue description>"  — agentic mode: model proposes edits, you confirm
  ai plugin "<description>"     — generate a plugin skeleton in plugins/<name>/
"""

import json
import os
import sys

VERSION = "1.0.0"
author = "HELLFORGE"
description = "LLM copilot — OpenAI/DeepSeek/Claude/Ollama, agentic edits, plugin generation"

from . import providers
from . import agent as llm_agent

CONF = {}


def _cfg(api, key, default=None):
    return api.get_config(key, default)


def _get_state(api):
    return {
        "provider": _cfg(api, "llm_provider", "openai"),
        "model": _cfg(api, "llm_model"),
        "base_url": _cfg(api, "llm_base_url"),
        "api_key": api.get_auth_token("llm"),
        "connected": _cfg(api, "llm_connected", False),
    }


def _save_state(api, state):
    api.set_config("llm_provider", state["provider"])
    if state.get("model"):
        api.set_config("llm_model", state["model"])
    if state.get("base_url"):
        api.set_config("llm_base_url", state["base_url"])
    api.set_config("llm_connected", bool(state["connected"]))
    if state.get("api_key"):
        api.set_auth_token("llm", state["api_key"])


def _endpoint(state):
    """Resolve (provider, base_url, model) for a chat request."""
    provider = state["provider"]
    base = state.get("base_url") or providers.PROVIDERS.get(provider, {}).get("base_url", "")
    model = state.get("model")
    return provider, base, model


def _request(state, messages):
    provider, base, model = _endpoint(state)
    if provider == "ollama":
        base = providers.OLLAMA_HEAD + "/v1"
        if not model:
            model = "llama3.2"
    if not model:
        return None, "no model selected — run 'ai model <name>'"
    return providers.chat_request(provider, base, state.get("api_key"), model, messages)


# ── eshell command ─────────────────────────────

def _cmd(args, api):
    state = _get_state(api)
    if not args:
        _status(state)
        return
    sub = args[0].lower()
    rest = args[1:]

    if sub == "status":
        _status(state)

    elif sub in ("provider", "set-provider"):
        if not rest:
            print("  Providers: " + ", ".join(providers.PROVIDERS))
            return
        name = rest[0].lower()
        if name not in providers.PROVIDERS:
            print(f"  Unknown provider: {name} (choose from "
                  f"{', '.join(providers.PROVIDERS)})")
            return
        state["provider"] = name
        state["base_url"] = providers.PROVIDERS[name]["base_url"]
        state["model"] = providers.DEFAULT_MODEL.get(name)
        _save_state(api, state)
        print(f"  Provider set: {providers.PROVIDERS[name]['label']}")
        if name == "ollama":
            _ollama_wizard(api, state)
        elif name == "custom" and len(rest) > 1:
            state["base_url"] = rest[1]
            _save_state(api, state)
            print(f"  Base URL: {rest[1]}")
        else:
            print("  Next: 'ai model <name>' (or 'ai key <key>' if required)")

    elif sub == "model":
        if not rest:
            models = _known_models(state)
            if not models:
                print("  No models configured — 'ai model <name>' to set one.")
            else:
                cur = state.get("model") or "(none)"
                print(f"  Current: {cur}")
                print("  Available: " + ", ".join(models))
            return
        state["model"] = rest[0]
        _save_state(api, state)
        print(f"  Model set: {rest[0]}")

    elif sub == "url":
        if not rest:
            print(f"  Base URL: {state.get('base_url') or '(default)'}")
            return
        state["base_url"] = rest[0]
        _save_state(api, state)
        print(f"  Base URL: {rest[0]}")

    elif sub == "key":
        if not rest:
            k = state.get("api_key") or ""
            print(f"  API key: {'*' * len(k) if k else '(not set)'}")
            return
        state["api_key"] = rest[0]
        _save_state(api, state)
        print("  API key saved (stored locally, not committed)")

    elif sub == "connect":
        state["connected"] = True
        _save_state(api, state)
        print(f"  Connected: {state['provider']} / {state.get('model') or '?'}")

    elif sub == "disconnect":
        state["connected"] = False
        _save_state(api, state)
        print(f"  Disconnected: {state['provider']} (config kept — 'ai connect' to resume)")

    elif sub == "ask":
        question = " ".join(rest)
        if not question:
            print("  Usage: ai ask \"<question>\"")
            return
        messages = [{"role": "user", "content": question}]
        _run_request(state, messages)

    elif sub == "chat":
        _chat_repl(state)

    elif sub == "read":
        if not rest:
            print("  Usage: ai read <file> [start [end]]")
            return
        rel = rest[0]
        start = int(rest[1]) if len(rest) > 1 else 1
        end = int(rest[2]) if len(rest) > 2 else None
        try:
            from . import agent as ag
            from . import diffview as dv
            target = ag.safe_path(api.project_dir, rel)
        except ValueError as e:
            print(f"  {e}")
            return
        if not target.exists():
            print(f"  Not found: {rel}")
            return
        lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
        end = min(end or len(lines), len(lines))
        print(f"  {dv.yellow(rel)}  {dv.dim(f'Read ({start}-{end}) [{len(lines)} lines]')}")
        for line in dv.render_read(lines, start, end):
            print(f"  {line}")

    elif sub in ("fix", "edit", "agent"):
        issue = " ".join([a for a in rest if a != "--yes"])
        auto_apply = "--yes" in rest
        if not issue:
            print("  Usage: ai fix \"<issue description>\" [--yes]")
            return
        _agentic(api, state, issue, plugin=False, confirm_write=not auto_apply)

    elif sub == "plugin":
        desc = " ".join(rest)
        if not desc:
            print("  Usage: ai plugin \"<what the plugin should do>\"")
            return
        _agentic(api, state, desc, plugin=True)

    else:
        print(f"  Unknown subcommand: {sub}")
        print("  status | provider | model | url | key | connect | disconnect | "
              "ask | chat | fix | plugin")


def _status(state):
    provider = state["provider"]
    label = providers.PROVIDERS.get(provider, {}).get("label", provider)
    conn = "connected" if state["connected"] else "disconnected"
    key = "set" if state.get("api_key") else "not set"
    model = state.get("model") or "(none)"
    base = state.get("base_url") or "(default)"
    print(f"  Provider:  {label} ({provider}) [{conn}]")
    print(f"  Model:     {model}")
    print(f"  Base URL:  {base}")
    print(f"  API key:   {key}")
    if provider == "ollama":
        found = providers.ollama_detected()
        print(f"  Ollama server: {'detected' if found else 'not detected (127.0.0.1:11434)'}")
    print("  Commands: ai provider|model|url|key|connect|disconnect|ask|chat|fix|plugin")


def _known_models(state):
    provider = state["provider"]
    if provider == "ollama":
        return providers.ollama_models()
    models = list(providers.PROVIDERS.get(provider, {}).get("models", []))
    if state.get("model") and state["model"] not in models:
        models.append(state["model"])
    return models


def _ollama_wizard(api, state):
    """Native Ollama flow: detect server, list local models, ask which to use,
    auto-save the selection."""
    if not providers.ollama_detected():
        print("  Ollama server not detected on 127.0.0.1:11434")
        print("  Install/start Ollama, then 'ai provider ollama' again.")
        state["connected"] = False
        _save_state(api, state)
        return
    models = providers.ollama_models()
    if not models:
        print("  Ollama is running but has no models installed.")
        print("  Run 'ollama pull llama3.2' (or any model) first.")
        state["connected"] = False
        _save_state(api, state)
        return
    print(f"  Ollama detected — {len(models)} local model(s):")
    for i, m in enumerate(models, 1):
        print(f"    [{i}] {m}")
    try:
        if sys.stdin.isatty():
            pick = input("  Select model number: ").strip()
        else:
            pick = "1"
    except EOFError:
        pick = "1"
    try:
        state["model"] = models[int(pick) - 1]
    except (ValueError, IndexError):
        state["model"] = models[0]
    state["base_url"] = providers.OLLAMA_HEAD + "/v1"
    state["connected"] = True
    _save_state(api, state)
    print(f"  Connected: ollama / {state['model']} (saved — 'ai disconnect' to stop)")


def _run_request(state, messages):
    text, err = _request(state, messages)
    if err:
        print(f"  [ai error] {err}")
        return None
    print("  " + text.replace("\n", "\n  "))
    return text


def _chat_repl(state):
    print("  AI chat (Ctrl-C or 'quit' to exit)")
    history = []
    try:
        while True:
            try:
                if sys.stdin.isatty():
                    line = input("  you> ")
                else:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    line = line.strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line or line.strip().lower() in ("quit", "exit"):
                break
            history.append({"role": "user", "content": line})
            text, err = _request(state, history)
            if err:
                print(f"  [ai error] {err}")
                break
            print("  ai> " + text.replace("\n", "\n      "))
            history.append({"role": "assistant", "content": text})
    except KeyboardInterrupt:
        pass


def _agentic(api, state, request, plugin=False, confirm_write=True):
    """Agentic mode: ask the model for a JSON plan, review the colored diff
    per file (y/n/v/a/q), apply. Deletes always confirmed individually."""
    project_dir = api.project_dir
    context = _build_context(project_dir, request)
    if plugin:
        prompt = (
            f"Create a HELLFORGE plugin that: {request}\n\n"
            "The plugin lives in plugins/<name>/__init__.py and registers via "
            "def register(api): api.add_command('name', handler, help) or "
            "api.on('post_compile', fn) etc. Respond with the JSON plan format "
            "(action write)."
        )
    else:
        prompt = (
            f"The user reports this issue / wants this change: {request}\n\n"
            f"Project context:\n{context}\n\n"
            "Inspect the project and propose the minimal set of changes. "
            "Respond with the JSON plan format (read/write/edit/delete)."
        )
    messages = [
        {"role": "system", "content": llm_agent.SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    print(f"  Asking {state['provider']}/{state.get('model') or '?'} for a plan...")
    text, err = _request(state, messages)
    if err:
        print(f"  [ai error] {err}")
        return
    plan = llm_agent.parse_plan(text)
    if plan is None:
        print("  The model did not return a valid change plan. Raw reply:")
        print("  " + (text or "").replace("\n", "\n  "))
        return
    print(f"  Plan: {plan.get('summary', 'no summary')}")
    for f in plan.get("files", []):
        print(f"    {f.get('action', '?'):6s} {f.get('path', '?')}")
    from . import diffview as dv
    applied, skipped, msgs = llm_agent.interactive_apply(
        plan, project_dir, confirm_write=confirm_write)
    for m in msgs:
        print(m)
    for rel, why in skipped:
        print(f"  {dv.dim('skipped')} {rel}: {why}")
    print(f"  Applied {applied} change(s).")


def _build_context(project_dir, request, max_files=3, max_lines=200, budget=60000):
    """Compact project context for agentic prompts: a top-level tree plus the
    contents of files the request explicitly names (up to budget bytes)."""
    import re
    from pathlib import Path
    root = Path(project_dir)
    parts = []
    try:
        entries = sorted(
            p.name + ("/" if p.is_dir() else "") for p in root.iterdir()
            if not p.name.startswith(".") and p.name not in (".venv", "node_modules")
        )
        parts.append("Project root: " + ", ".join(entries[:60]))
    except Exception:
        pass
    named = re.findall(r"[\w./\\-]+\.\w+", request)
    used = 0
    for rel in named[:max_files]:
        rel = rel.replace("\\", "/").lstrip("./")
        try:
            target = (root / rel).resolve()
            if not str(target).startswith(str(root)) or not target.is_file():
                continue
            text = target.read_text(encoding="utf-8", errors="replace")
            if len(text) > budget:
                text = text[:budget] + "\n... (truncated)"
            lines = text.splitlines()[:max_lines]
            parts.append(f"--- {rel} ({target.stat().st_size} bytes) ---\n"
                         + "\n".join(lines))
            used += len(text)
            if used > budget:
                break
        except Exception:
            continue
    return "\n".join(parts) or "(empty)"


def register(api):
    api.add_boot_step("LLM Copilot loading", "loading")
    api.add_command("ai", lambda a: _cmd(a, api),
                    "AI copilot: ai status|provider|model|url|key|ask|chat|fix|plugin")
    api.add_command("llm", lambda a: _cmd(a, api), "AI copilot: alias for ai")
    api.add_help_section("AI Copilot (LLM plugin)", [
        "  ai status                    Show provider/model/connection",
        "  ai provider <openai|deepseek|claude|ollama|custom>  Select provider",
        "  ai model [<name>]            List known models / set model",
        "  ai url <base_url>            Custom OpenAI-compatible endpoint",
        "  ai key <key>                 Set API key (stored locally)",
        "  ai ask \"<question>\"          Single-shot question",
        "  ai chat                      Interactive chat",
        "  ai fix \"<issue>\"             Agentic edits (confirmed before apply)",
        "  ai plugin \"<description>\"    Generate a plugin skeleton",
        "  Ollama: 'ai provider ollama' auto-detects the local server and asks",
        "          which model to use; selection is saved; 'ai disconnect' stops.",
    ])
    api.add_boot_step("LLM Copilot ready", "done")
