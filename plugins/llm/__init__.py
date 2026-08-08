"""HELLFORGE Copilot — LLM plugin (OpenAI-compatible, DeepSeek, Claude,
Ollama native). Agentic edits with confirmation, plugin generation, chat.

Commands (eshell + run.py):
  ai status                     — provider/model/connection
  ai setup                      — first-time wizard (auto-runs when no config)
  ai provider <name>            — openai | deepseek | claude | ollama | custom
  ai model [name]               — list known models / set model
  ai url <base_url>             — custom base URL (OpenAI-compatible)
  ai key <api_key>              — set API key (stored in local config)
  ai connect                    — mark connected (auto after provider/model)
  ai disconnect                 — disconnect without forgetting config
  ai ask "<question>"           — single-shot answer
  ai chat                       — interactive REPL chat (Ctrl-C / 'quit' to exit)
  ai fix "<issue>"              — multi-step agentic loop: plan → review →
                                  apply → verify → repeat until done
  ai plugin "<description>"     — generate a plugin skeleton in plugins/<name>/
  ai read <file> [start [end]]  — line-numbered file view
  ai agents on|off              — multi-agent orchestration (persisted)
  ai agent-model [name|ollama|provider]
                                — daughter agent model selection
  ai index [build|status]       — project index (files/symbols/directives)
  ai index-model [name]         — indexing model (selectable from Ollama)
  ai index off                  — disable indexing (not recommended)
"""

import json
import os
import sys
import time

VERSION = "1.0.0"
author = "HELLFORGE"
description = ("LLM copilot — OpenAI/DeepSeek/Claude/Ollama, multi-step agent, "
               "indexing, safe command execution")

from . import providers
from . import agent as llm_agent
from . import indexer

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
        "setup_done": _cfg(api, "llm_setup_done", False),
        "agents_enabled": _cfg(api, "llm_agents_enabled", False),
        "agent_model": _cfg(api, "llm_agent_model"),
        "index_enabled": _cfg(api, "llm_index_enabled", True),
        "index_model": _cfg(api, "llm_index_model"),
        "index_rebuilt": _cfg(api, "llm_index_rebuilt", 0),
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
    api.set_config("llm_setup_done", bool(state.get("setup_done")))
    api.set_config("llm_agents_enabled", bool(state.get("agents_enabled")))
    if state.get("agent_model"):
        api.set_config("llm_agent_model", state["agent_model"])
    api.set_config("llm_index_enabled", bool(state.get("index_enabled")))
    if state.get("index_model"):
        api.set_config("llm_index_model", state["index_model"])
    api.set_config("llm_index_rebuilt", int(state.get("index_rebuilt", 0)))


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

    # First-run setup wizard: no saved config → walk the user through it.
    if sub != "setup" and not state["setup_done"]:
        print("  No AI config found on this machine — running setup wizard.")
        _setup_wizard(api, state)
        if not state["setup_done"]:
            return

    if sub == "setup":
        _setup_wizard(api, state)
        return

    if sub == "status":
        _status(state)

    elif sub == "agents":
        if not rest:
            on = "enabled (persisted)" if state["agents_enabled"] else "disabled"
            print(f"  Multi-agent orchestration: {on}")
            print("  Usage: ai agents on|off")
            return
        if rest[0].lower() in ("on", "enable", "yes"):
            state["agents_enabled"] = True
            _save_state(api, state)
            print("  Multi-agent orchestration ENABLED (saved forever until disabled).")
            if not state.get("agent_model"):
                _agent_model_wizard(api, state)
        elif rest[0].lower() in ("off", "disable", "no"):
            state["agents_enabled"] = False
            _save_state(api, state)
            print("  Multi-agent orchestration DISABLED (saved).")
        else:
            print("  Usage: ai agents on|off")

    elif sub in ("agent-model", "agentmodel"):
        _agent_model_cmd(api, state, rest)

    elif sub == "index":
        _index_cmd(api, state, rest)

    elif sub == "index-model":
        if not rest:
            m = state.get("index_model")
            print(f"  Indexing model: {m or '(none — local symbol index only)'}")
            print("  Usage: ai index-model <name> | ollama | provider | off")
            return
        _set_index_model(api, state, rest[0])

    elif sub == "provider":
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
        _chat_repl(state, api)

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


def _setup_wizard(api, state):
    """First-run wizard: provider → model → indexing → multi-agent.
    Runs automatically when no config exists (fresh machine / no cache)."""
    print("  ── AI Copilot setup ──")
    try:
        if not sys.stdin.isatty():
            print("  Non-interactive: skipping wizard (run 'ai setup' on a terminal).")
            return
        ans = input("  Configure AI now? [Y/n] ").strip().lower()
        if ans == "n":
            print("  Skipped. Run 'ai setup' any time.")
            return
        # 1. Provider
        print("  Providers: " + ", ".join(providers.PROVIDERS))
        p = input("  Select provider: ").strip().lower()
        if p not in providers.PROVIDERS:
            p = "openai"
        state["provider"] = p
        state["base_url"] = providers.PROVIDERS[p]["base_url"]
        state["model"] = providers.DEFAULT_MODEL.get(p)
        # 2. Model
        if p == "ollama":
            _ollama_wizard(api, state)
        else:
            models = providers.PROVIDERS[p]["models"]
            print("  Models: " + ", ".join(models))
            m = input("  Select model (Enter = first): ").strip()
            state["model"] = m if m in models else (models[0] if models else None)
            key = input("  API key (Enter = none): ").strip()
            if key:
                state["api_key"] = key
        state["connected"] = True
        # 3. Indexing
        ans = input("  Enable project indexing? [Y/n] ").strip().lower()
        state["index_enabled"] = ans != "n"
        if state["index_enabled"]:
            _set_index_model(api, state, "ollama", quiet=True)
        # 4. Multi-agent orchestration
        ans = input("  Enable multi-agent orchestration? [y/N] ").strip().lower()
        state["agents_enabled"] = ans == "y"
        if state["agents_enabled"]:
            _agent_model_wizard(api, state)
        state["setup_done"] = True
        _save_state(api, state)
        print("  ── Setup complete (saved forever on this machine) ──")
        print("  Run 'ai fix \"<issue>\"' to start. 'ai setup' to redo.")
    except (EOFError, KeyboardInterrupt):
        print("\n  Setup cancelled.")


def _agent_model_cmd(api, state, rest):
    """Daughter agent model: a name, 'provider' (same as main), or 'ollama'
    (pick directly from the local Ollama models)."""
    if not rest:
        m = state.get("agent_model") or "provider (same as main)"
        on = "enabled" if state["agents_enabled"] else "disabled"
        print(f"  Daughter agent model: {m}")
        print(f"  Multi-agent orchestration: {on} (ai agents on|off)")
        print("  Usage: ai agent-model <name> | provider | ollama")
        return
    choice = rest[0].lower()
    if choice == "provider":
        state["agent_model"] = None
        _save_state(api, state)
        print("  Daughter agent = provider model (same as main).")
    elif choice == "ollama":
        _agent_model_wizard(api, state)
    else:
        state["agent_model"] = rest[0]
        _save_state(api, state)
        print(f"  Daughter agent model: {rest[0]}")
    if not state["agents_enabled"]:
        print("  Note: enable orchestration with 'ai agents on'.")


def _agent_model_wizard(api, state):
    """Pick the daughter agent model — from the provider (all saved models)
    or directly from local Ollama."""
    try:
        if not sys.stdin.isatty():
            state["agent_model"] = state.get("model")
            _save_state(api, state)
            return
        print("  Daughter agent model sources:")
        print("    [p] provider model (same as main)")
        print("    [o] Ollama (pick from locally installed models)")
        ans = input("  Choose [p/o]: ").strip().lower()
        if ans == "o" and providers.ollama_detected():
            models = providers.ollama_models()
            if not models:
                print("  Ollama has no models — using provider model.")
                state["agent_model"] = state.get("model")
            else:
                for i, m in enumerate(models, 1):
                    print(f"    [{i}] {m}")
                pick = input("  Select daughter model number: ").strip()
                try:
                    state["agent_model"] = models[int(pick) - 1]
                except (ValueError, IndexError):
                    state["agent_model"] = models[0]
                print(f"  Daughter agent: ollama / {state['agent_model']}")
        else:
            state["agent_model"] = None  # provider model
            print("  Daughter agent: provider model (same as main).")
        _save_state(api, state)
    except (EOFError, KeyboardInterrupt):
        pass


def _index_cmd(api, state, rest):
    """ai index build|status|off — project indexing control."""
    sub = rest[0].lower() if rest else "status"
    if sub == "off":
        state["index_enabled"] = False
        _save_state(api, state)
        print("  Indexing DISABLED (not recommended — model context gets weaker).")
        print("  Re-enable: 'ai index on'")
        return
    if sub == "on":
        state["index_enabled"] = True
        _save_state(api, state)
        print("  Indexing ENABLED.")
        sub = "build"
    if sub in ("build", "rebuild"):
        idx = indexer.build_index(api.project_dir)
        state["index_rebuilt"] = int(idx.get("built", 0))
        _save_state(api, state)
        print(f"  Index rebuilt: {idx['file_count']} files, "
              f"{idx['line_count']} lines "
              f"({sum(len(f.get('symbols', [])) for f in idx['files'].values())} symbols)")
        if state.get("index_model"):
            _index_summarize(api, state, idx)
        return
    # status
    idx = indexer.load_index(api.project_dir)
    on = "enabled" if state["index_enabled"] else "disabled"
    model = state.get("index_model") or "local symbol index (no model)"
    if idx:
        print(f"  Indexing: {on} | model: {model}")
        print(f"  Index: {idx.get('file_count', 0)} files, "
              f"{idx.get('line_count', 0)} lines "
              f"(built {time.strftime('%H:%M:%S', time.localtime(idx.get('built', 0)))})")
        print("  Rebuild: 'ai index build'")
    else:
        print(f"  Indexing: {on} | model: {model}")
        print("  No index yet — run 'ai index build'")


def _set_index_model(api, state, choice, quiet=False):
    """Indexing model: a name, 'ollama' (pick locally), 'provider' (main),
    or 'off' (local symbol index only)."""
    choice = choice.lower()
    if choice == "off":
        state["index_model"] = None
        _save_state(api, state)
        if not quiet:
            print("  Indexing model off — local symbol index only (works, weaker).")
        return
    if choice == "ollama":
        if not providers.ollama_detected():
            if not quiet:
                print("  Ollama not detected — add a model name instead: "
                      "'ai index-model <name>'")
            state["index_model"] = None
            _save_state(api, state)
            return
        models = providers.ollama_models()
        if not models:
            if not quiet:
                print("  Ollama has no models installed. 'ai index-model <name>' to add one.")
            state["index_model"] = None
            _save_state(api, state)
            return
        if not quiet:
            for i, m in enumerate(models, 1):
                print(f"    [{i}] {m}")
        try:
            if sys.stdin.isatty() and not quiet:
                pick = input("  Select indexing model number: ").strip()
            else:
                pick = "1"
            state["index_model"] = models[int(pick) - 1]
        except (ValueError, IndexError):
            state["index_model"] = models[0]
        _save_state(api, state)
        if not quiet:
            print(f"  Indexing model: {state['index_model']} (disable: 'ai index-model off')")
        return
    if choice == "provider":
        state["index_model"] = None  # main model is used
        _save_state(api, state)
        if not quiet:
            print("  Indexing model: provider (same as main).")
        return
    state["index_model"] = choice
    _save_state(api, state)
    if not quiet:
        print(f"  Indexing model: {choice}")


def _index_summarize(api, state, idx):
    """Optional model pass over the index (top files). Never required —
    the deterministic symbol index is always available."""
    try:
        files = sorted(idx.get("files", {}))[:15]
        if not files:
            return
        prompt = ("Summarize this project index in 3-5 lines for a coding "
                  "agent:\n" + indexer.index_to_text(idx, max_files=15))
        text, err = _request(state, [{"role": "user", "content": prompt}])
        if text:
            print("  Index summary:")
            print("  " + text.replace("\n", "\n  "))
    except Exception:
        pass


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


def _chat_repl(state, api=None):
    """Interactive chat — project-aware: the model sees the project index
    (when indexing is on) so it never fabricates project structure. It CANNOT
    edit files — point edits at 'ai fix'."""
    print("  AI chat (Ctrl-C or 'quit' to exit)")
    history = []
    system = ("You are HELLFORGE Copilot chatting inside a project. "
              "You can reference the files listed in the project index, but "
              "you CANNOT read or edit files from chat — for changes the "
              "user runs 'ai fix'.")
    if api is not None:
        idx = indexer.load_index(api.project_dir)
        if idx:
            system += "\n\nProject index:\n" + indexer.index_to_text(idx, max_files=25)
    history.append({"role": "system", "content": system})
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


def _agentic(api, state, request, plugin=False, confirm_write=True, max_steps=5):
    """Multi-step agentic loop: plan → review → apply → (commands) →
    verify → repeat until the model says done. Deletes always confirmed."""
    project_dir = api.project_dir
    from . import diffview as dv

    if not state["setup_done"]:
        print("  Run 'ai setup' first (or the wizard will appear on next command).")
        _setup_wizard(api, state)
        if not state["setup_done"]:
            return

    idx = None
    if state.get("index_enabled", True):
        idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
        state["index_rebuilt"] = int(idx.get("built", 0))

    steps = 0
    while steps < max_steps:
        steps += 1
        print(f"\n  ── step {steps}/{max_steps} ──")
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
                f"Project context:\n{_build_context(project_dir, request)}\n\n"
                f"{indexer.index_to_text(idx, max_files=30)}\n\n"
                "You may use 'read' to inspect files, 'commands' to run checks "
                "(e.g. python tests/...), and write/edit to change files. "
                "When the change is complete (or on the final step), reply "
                '{"done": true, "summary": "..."}. Respond with the JSON plan format.'
            )
        messages = [
            {"role": "system", "content": llm_agent.SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]
        print(f"  Asking {state['provider']}/{state.get('model') or '?'}...")
        text, err = _request(state, messages)
        if err:
            print(f"  [ai error] {err}")
            return
        plan = llm_agent.parse_plan(text)
        if plan is None:
            # One automatic retry: feed the reply back and demand JSON.
            messages.append({"role": "assistant", "content": text or ""})
            messages.append({"role": "user", "content":
                "That reply was not a valid change plan. Reply with ONLY the "
                'JSON object: {"summary": "...", "files": [...], '
                '"commands": [...]} or {"done": true, "summary": "..."}.'})
            print("  No JSON plan — asking again...")
            text2, err2 = _request(state, messages)
            if err2:
                print(f"  [ai error] {err2}")
                return
            plan = llm_agent.parse_plan(text2)
            text = text2
        if plan is None:
            print("  No valid plan. Raw reply:")
            print("  " + (text or "").replace("\n", "\n  "))
            return
        if llm_agent.plan_is_done(plan):
            print(f"  Done: {plan.get('summary', 'no summary')}")
            break

        # 1. Commands first — run them, show one-liners in chat, feed output back
        cmds = plan.get("commands") or []
        if cmds:
            results, chat_lines = llm_agent.execute_plan_commands(plan, project_dir)
            for line in chat_lines:
                print(f"  {dv.dim(line)}")
            cmd_out = "\n".join(
                f"$ {r.get('cmd')}\n{r.get('output', '')[:1200]}"
                for r in results if not r.get("blocked")
            )
            blocked = [r.get("cmd") for r in results if r.get("blocked")]
            if blocked:
                print(f"  {dv.red('blocked: ' + ', '.join(blocked))}")

        # 2. Files — review the colored diff and apply
        files = plan.get("files") or []
        if files:
            for f in files:
                print(f"    {f.get('action', '?'):6s} {f.get('path', '?')}")
            applied, skipped, msgs = llm_agent.interactive_apply(
                plan, project_dir, confirm_write=confirm_write)
            for m in msgs:
                print(m)
            for rel, why in skipped:
                print(f"  {dv.dim('skipped')} {rel}: {why}")

        # 3. Multi-agent verification: daughter agent reviews the result
        if (state.get("agents_enabled") and (files or cmds)
                and state.get("agent_model")):
            _daughter_verify(api, state, request, project_dir)

        # 4. Next step: model sees what changed / commands output
        if steps >= max_steps:
            break
        follow = [f"Step {steps} finished. Changes applied and reviewed."]
        if cmds:
            follow.append(f"Command results:\n{cmd_out or '(none)'}")
        if files:
            follow.append("Files were changed (see above). "
                          "Verify with commands, or reply with the next step "
                          "or {\"done\": true}.")
        else:
            follow.append("No files changed yet — propose the actual edits, "
                          "or {\"done\": true} if nothing is needed.")
        messages.append({"role": "assistant", "content": text})
        messages.append({"role": "user", "content": "\n".join(follow)})
        text, err = _request(state, messages)
        if err:
            print(f"  [ai error] {err}")
            return
        plan2 = llm_agent.parse_plan(text)
        if plan2 is None:
            print("  No valid next-step plan. Raw reply:")
            print("  " + (text or "").replace("\n", "\n  "))
            return
        plan = plan2
        if llm_agent.plan_is_done(plan):
            print(f"  Done: {plan.get('summary', 'no summary')}")
            break
        cmds = plan.get("commands") or []
        if cmds:
            results, chat_lines = llm_agent.execute_plan_commands(plan, project_dir)
            for line in chat_lines:
                print(f"  {dv.dim(line)}")
            cmd_out = "\n".join(
                f"$ {r.get('cmd')}\n{r.get('output', '')[:1200]}"
                for r in results if not r.get("blocked")
            )
        files = plan.get("files") or []
        if files:
            applied, skipped, msgs = llm_agent.interactive_apply(
                plan, project_dir, confirm_write=confirm_write)
            for m in msgs:
                print(m)
            for rel, why in skipped:
                print(f"  {dv.dim('skipped')} {rel}: {why}")
        if (state.get("agents_enabled") and (files or cmds)
                and state.get("agent_model")):
            _daughter_verify(api, state, request, project_dir)
        request = f"Continue: {request}"

    print(f"\n  Finished after {steps} step(s).")


def _daughter_verify(api, state, request, project_dir):
    """Multi-agent orchestration: the daughter agent model reviews the
    changes and reports problems. Never edits — only observes."""
    from . import diffview as dv
    model = state.get("agent_model") or state.get("model")
    if not model:
        return
    old_state = dict(state)
    state["model"] = model
    try:
        text, err = _request(state, [
            {"role": "system", "content":
             "You are a code reviewer. Review the recent changes for the "
             "request below. Report only real problems in 2-3 short lines, "
             "or say 'OK'."},
            {"role": "user", "content":
             f"Request: {request}\nReview the applied changes in the project."},
        ])
        if err:
            print(f"  {dv.dim(f'daughter agent error: {err}')}")
            return
        if text and text.strip().lower() != "ok":
            print(f"  {dv.yellow('daughter agent review:')}")
            print("  " + text.strip().replace("\n", "\n  "))
        else:
            print(f"  {dv.dim('daughter agent review: OK')}")
    finally:
        state["model"] = old_state["model"]


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
