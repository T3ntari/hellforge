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
from pathlib import Path

VERSION = "1.0.0"
author = "HELLFORGE"
description = ("LLM copilot — OpenAI/DeepSeek/Claude/Ollama, multi-step agent, "
               "indexing, safe command execution")

from . import providers
from . import agent as llm_agent
from . import indexer
from . import ui

CONF = {}

# Current provider/model for scaled system prompts (updated per command)
_CURRENT_STATE = {}


def _system_prompt(project_dir, base=None):
    """Build the system prompt, SCALED to the model profile: small models get
    the distilled briefing, large models get the full docs/agent/* set."""
    try:
        from . import scale as scale_mod
        return scale_mod.system_prompt_scaled(
            project_dir, _CURRENT_STATE.get("model"), _CURRENT_STATE.get("provider"))
    except Exception:
        pass
    # Fallback: AGENTS.md + RULES.md + TODO.md (capped)
    from pathlib import Path
    root = Path(project_dir)
    parts = []
    for name in ("AGENTS.md", "RULES.md"):
        p = root / name
        if p.exists():
            try:
                text = p.read_text(encoding="utf-8", errors="replace")
                parts.append(f"# {name} (project instructions)\n{text[:12000]}")
            except Exception:
                pass
    todo_path = root / "TODO.md"
    if todo_path.exists():
        try:
            parts.append(f"# TODO.md (live checklist — update via the 'todo' plan key)\n"
                         f"{todo_path.read_text(encoding='utf-8', errors='replace')[:4000]}")
        except Exception:
            pass
    prompt = (base or llm_agent.SYSTEM_PROMPT)
    if parts:
        prompt = prompt + "\n\n" + "\n\n".join(parts)
    return prompt


def _cfg(api, key, default=None):
    return api.get_config(key, default)


def _get_state(api):
    global _CURRENT_STATE
    _st = {
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
    _CURRENT_STATE = _st
    return _st


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
    return providers.chat_request(provider, base, state.get("api_key"), model, messages,
                                  timeout=600 if provider == "ollama" else 300)


def _request_visible(state, messages, on_thinking=None):
    """_request + thinking-tag handling: strips <thinking> blocks, shows them
    per config (full or collapsed 'thought for Xs'), returns visible text."""
    import time as _t
    t0 = _t.time()
    text, err = _request(state, messages)
    dt = _t.time() - t0
    if not text:
        return text, err
    try:
        from . import thinking as th
        blocks, visible = th.extract_thinking(text)
        if blocks:
            cfg = th.apply_config(state)
            if cfg.get("show_full"):
                print(th.render_full(blocks))
            else:
                print("  " + ui.thinking_collapsed(dt))
            if on_thinking:
                on_thinking(blocks, dt)
            return visible, err
    except Exception:
        pass
    return text, err


# ── eshell command ─────────────────────────────

def _cmd(args, api):
    state = _get_state(api)
    global _CURRENT_STATE
    _CURRENT_STATE = state
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
            try:
                from . import select as sel
                sel.pick_model(api, state)
            except ImportError:
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

    elif sub in ("agent", "interact", "session"):
        use_tui = "--tui" in rest
        if "--no-tui" not in rest:
            try:
                from . import tui as tui_mod
                if tui_mod.tui_available():
                    use_tui = True
            except ImportError:
                pass
        rest = [a for a in rest if not a.startswith("--")]
        if use_tui:
            _agent_tui(state, api, rest)
        else:
            _agent_cc(state, api, rest)

    elif sub == "resume":
        _resume_cmd(api, state, rest)

    elif sub == "sessions":
        _sessions_cmd(api)

    elif sub == "review":
        _review_cmd(api, state, rest)

    elif sub in ("doctor", "checkup"):
        _doctor_cmd(api)

    elif sub == "search":
        _search_cmd(api, state, rest)

    elif sub == "context":
        _context_cmd(api, state, rest)

    elif sub == "memory":
        _memory_cmd(api, rest)

    elif sub == "note":
        _note_cmd(api, rest)

    elif sub == "ticket":
        _ticket_cmd(api, rest)

    elif sub == "undo":
        _undo_cmd(api, rest)

    elif sub == "upload":
        _upload_cmd(api, rest)

    elif sub == "config":
        _config_cmd(api, state, rest)

    elif sub == "init":
        _init_cmd(api)

    elif sub == "cost":
        _cost_cmd(api, state, rest)

    elif sub == "todo":
        _todo_cmd(api, rest)

    elif sub == "test":
        _test_cmd(api, state, rest)

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


def _todo_cmd(api, rest):
    """ai todo — show / add / done. The agent-managed checklist."""
    from pathlib import Path
    from . import todo as todo_mod
    path = Path(api.project_dir) / "TODO.md"
    if not rest:
        text = todo_mod.render_todo(path)
        print(text if text else "  (no TODO.md yet — 'ai todo add \"first item\"')")
        return
    sub = rest[0].lower()
    item = " ".join(rest[1:]).strip()
    if sub in ("add", "+"):
        if not item:
            print("  Usage: ai todo add \"<item>\"")
            return
        added, _ = todo_mod.apply_todo([{"item": item, "status": "open"}], path)
        print(f"  {ui.chip('todo', 'done')} added: {item}" if added else f"  already listed: {item}")
    elif sub in ("done", "check", "x"):
        if not item:
            print("  Usage: ai todo done \"<item>\"")
            return
        _, marked = todo_mod.apply_todo([{"item": item, "status": "done"}], path)
        print(f"  {ui.chip('done', 'done')} marked done: {item}" if marked else f"  not found: {item}")
    else:
        print("  Usage: ai todo | ai todo add \"<item>\" | ai todo done \"<item>\"")


def _test_cmd(api, state, rest):
    """ai test [file...] [--smoke] — run the project test suite (or a subset)
    from inside the copilot."""
    from . import tests_runner as tr
    smoke = "--smoke" in rest
    files = [a for a in rest if not a.startswith("--")]
    if smoke:
        results = tr.run_tests(api.project_dir, smoke=True)
    elif files:
        results = tr.run_tests(api.project_dir, files=files)
    else:
        results = tr.run_tests(api.project_dir)
    print(tr.summarize(results))
    failed = sum(1 for r in results if not r.get("ok"))
    print(f"  {ui.result_line('all green' if failed == 0 else f'{failed} file(s) failing', 'ok' if failed == 0 else 'err')}")


def _search_cmd(api, state, rest):
    """ai search <query> — codebase search (prefix ~ for similar)."""
    query = " ".join(rest).strip()
    if not query:
        print("  Usage: ai search <query>   (prefix ~ for similar-to)")
        return
    try:
        from . import search as search_mod
        from . import scale as scale_mod
        b = scale_mod.budget_for(state.get("model"), state.get("provider"))
        top = b.get("search_top", 5)
    except ImportError:
        search_mod = None
        top = 5
    if search_mod is None:
        print(f"  {ui.chip('error', 'error')} search support missing")
        return
    if search_mod.is_stale(api.project_dir):
        print("  rebuilding search index...")
        search_mod.build_search_index(api.project_dir)
    print(search_mod.run_query(api.project_dir, query, top_k=top))


def _context_cmd(api, state, rest):
    """ai context small|medium|large|auto — override the context profile."""
    if not rest:
        try:
            from . import scale as scale_mod
            ov = scale_mod.get_override()
            p = scale_mod.profile(state.get("model"), state.get("provider"))
            print(f"  profile: {p} (override: {ov or 'auto'})")
        except ImportError:
            print("  scale support missing")
        return
    choice = rest[0].lower()
    try:
        from . import scale as scale_mod
        if choice in ("auto", "default", "off"):
            scale_mod.set_override(None)
            print("  context profile: auto")
        elif choice in ("small", "medium", "large"):
            scale_mod.set_override(choice)
            print(f"  context profile forced: {choice}")
        else:
            print("  Usage: ai context small|medium|large|auto")
    except ImportError:
        print(f"  {ui.chip('error', 'error')} scale support missing")


def _memory_cmd(api, rest):
    """ai memory [add|remove|list] — long-form memory (MEMORY.md)."""
    from pathlib import Path as _P
    try:
        from . import memory as mem_mod
    except ImportError:
        print(f"  {ui.chip('error', 'error')} memory support missing")
        return
    path = _P(api.project_dir) / "MEMORY.md"
    sub = rest[0].lower() if rest else "list"
    item = " ".join(rest[1:]).strip()
    if sub == "list":
        pts = mem_mod.load_memory(path)
        print(f"  {len(pts)} memory point(s):")
        for p in pts:
            print(f"    - {p}")
    elif sub in ("add", "+"):
        if not item:
            print("  usage: ai memory add <point>")
            return
        a, r = mem_mod.apply_memory([{"point": item, "action": "add"}], path)
        print(f"  {ui.chip('memory', 'done')} added: {item}")
    elif sub in ("remove", "rm", "-"):
        if not item:
            print("  usage: ai memory remove <point>")
            return
        a, r = mem_mod.apply_memory([{"point": item, "action": "remove"}], path)
        print(f"  removed: {item}" if r else f"  not found: {item}")
    else:
        print("  usage: ai memory list | add <point> | remove <point>")


def _note_cmd(api, rest):
    """ai note <text> — append a global note (NOTES.md)."""
    from pathlib import Path as _P
    text = " ".join(rest).strip()
    if not text:
        print("  usage: ai note <text>")
        return
    try:
        from . import memory as mem_mod
        mem_mod.add_note(_P(api.project_dir) / "NOTES.md", text)
        print(f"  {ui.chip('note', 'done')} NOTES.md updated")
    except ImportError:
        print(f"  {ui.chip('error', 'error')} memory support missing")


def _ticket_cmd(api, rest):
    """ai ticket list | create <title> --body <text> [--assignee <bot>] | done <n>"""
    from pathlib import Path as _P
    try:
        from . import memory as mem_mod
    except ImportError:
        print(f"  {ui.chip('error', 'error')} memory support missing")
        return
    path = _P(api.project_dir) / "TICKETS.md"
    sub = rest[0].lower() if rest else "list"
    if sub == "list":
        ts = mem_mod.list_tickets(path)
        if not ts:
            print("  No tickets.")
            return
        for t in ts:
            print(f"    TICKET-{t['num']} [{t.get('status', 'open')}] "
                  f"{t['title']} — {t.get('assignee') or 'unassigned'}")
    elif sub == "create":
        args = rest[1:]
        body = ""
        assignee = ""
        if "--assignee" in args:
            i = args.index("--assignee")
            assignee = args[i + 1] if i + 1 < len(args) else ""
            args = args[:i]
        if "--body" in args:
            i = args.index("--body")
            body = " ".join(args[i + 1:])
            args = args[:i]
        title = " ".join(args).strip()
        if not title:
            print("  usage: ai ticket create <title> --body <text> [--assignee <bot>]")
            return
        num = mem_mod.create_ticket(path, title, body, assignee)
        print(f"  {ui.chip('ticket', 'done')} created TICKET-{num}: {title}")
    elif sub == "done":
        try:
            n = int(rest[1])
        except (ValueError, IndexError):
            print("  usage: ai ticket done <num>")
            return
        mem_mod.update_ticket(path, n, status="done")
        print(f"  TICKET-{n} marked done")
    else:
        print("  usage: ai ticket list | create | done <num>")


def _undo_cmd(api, rest):
    """ai undo [N] — undo the last N applied turns."""
    n = 1
    if rest:
        try:
            n = int(rest[0])
        except ValueError:
            print("  usage: ai undo [N]")
            return
    try:
        from . import undo as undo_mod
    except ImportError:
        print(f"  {ui.chip('error', 'error')} undo support missing")
        return
    undone, count = undo_mod.undo(api.project_dir, n)
    if count == 0:
        print("  nothing to undo")
        return
    for path, what in undone:
        print(f"  {ui.result_line(what, 'ok')} {path}")
    print(f"  {ui.chip('undo', 'done')} {count} turn(s) undone")


def _upload_cmd(api, rest):
    """ai upload <path> — attach a file to the session (image/text/code/binary)."""
    path = " ".join(rest).strip()
    if not path:
        print("  usage: ai upload <path>")
        return
    try:
        from . import upload as up_mod
        if not os.path.isabs(path):
            cand = os.path.join(api.project_dir, path)
            path = cand if os.path.exists(cand) else path
        u = up_mod.load_upload(path)
        print(up_mod.format_for_context(u))
        print(f"  {ui.chip('uploaded', 'done')} {u['path']} "
              f"({u['kind']}, {u['size']} bytes)")
    except Exception as e:
        print(f"  {ui.chip('error', 'error')} upload: {e}")


def _config_cmd(api, state, rest):
    """ai config [key=value] — show or set copilot config (llm_*)."""
    keys = ["llm_provider", "llm_model", "llm_mode", "llm_show_thinking",
            "llm_compact_threshold", "llm_compact_target", "llm_compact_model",
            "llm_guard", "llm_guard_model", "llm_embed_model", "llm_index_model",
            "llm_agent_model", "llm_agents_enabled", "llm_connected"]
    if not rest:
        print(f"  {ui.chip('config', 'command')} copilot config:")
        for k in keys:
            print(f"    {k} = {api.get_config(k, '')}")
        print("  set: ai config <key>=<value>")
        return
    if "=" in rest:
        k, _, v = rest.partition("=")
        k = k.strip()
        if k not in keys:
            print(f"  unknown key {k} — known: {', '.join(keys)}")
            return
        try:
            v = v.strip()
            if v.lower() in ("true", "false"):
                v = v.lower() == "true"
            elif v.replace(".", "", 1).isdigit():
                v = float(v) if "." in v else int(v)
            api.set_config(k, v)
            print(f"  {ui.chip('config', 'done')} {k} = {v}")
        except Exception as e:
            print(f"  {ui.chip('error', 'error')} {e}")
    else:
        print("  usage: ai config <key>=<value>")


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


def _agent_cc(state, api, rest):
    """Claude-Code-style `ai agent` — the full REPL with slash commands,
    permission modes, status bar, sessions and cost tracking."""
    project_dir = api.project_dir
    mode = (rest[0].lower() if rest and rest[0] in ("plan", "auto", "ask")
            else api.get_config("llm_mode", "ask"))
    state["mode"] = mode

    turn_counts = {"reads": 0, "edits": 0, "commands": 0}

    # ── True persistence: auto-resume the latest session + saved state ──
    uploads = []
    resume_history = None
    resume_id = None
    try:
        from . import session as sess
        sessions = sess.list_sessions(project_dir)
        if sessions:
            sid = sessions[0]["id"]
            want_resume = True
            if sys.stdin.isatty():
                try:
                    ans = input(f"  Resume last session {sid} "
                                f"({sessions[0].get('turns', 0)} turns)? [Y/n] ").strip().lower()
                    want_resume = ans != "n"
                except EOFError:
                    pass
            if want_resume:
                data = sess.load_session(project_dir, sid)
                if data:
                    resume_history = data.get("history") or []
                    resume_id = sid
                    meta = data.get("meta") or {}
                    for up in (meta.get("uploads") or [])[:5]:
                        try:
                            from . import upload as up_mod
                            uploads.append(up_mod.load_upload(up))
                        except Exception:
                            pass
                    if meta.get("mode"):
                        state["mode"] = meta["mode"]
                    if meta.get("model"):
                        state["model"] = meta["model"]
                    print(f"  {ui.chip('resumed', 'done')} session {sid} "
                          f"({len(resume_history)} messages, "
                          f"{len(uploads)} upload(s))")
        try:
            from . import undo as undo_mod
            n = undo_mod.load_stack(project_dir)
            if n:
                print(f"  {ui.dim(f'undo history restored: {n} snapshot(s)')}")
        except Exception:
            pass
    except Exception:
        pass

    def _get_request(messages):
        def _on_thinking(blocks, dt):
            pass
        return _request_visible(state, messages)

    def _apply_plan(plan, pd, confirm_write=True):
        res = llm_agent.interactive_apply(plan, pd, confirm_write=confirm_write)
        for f in plan.get("files") or []:
            act = f.get("action", "")
            if act == "read":
                turn_counts["reads"] += 1
            elif act in ("edit", "write"):
                turn_counts["edits"] += 1
        return res

    def _on_turn(history, event=None):
        try:
            from . import session as sess
            meta = {}
            meta["uploads"] = [u.get("path") for u in uploads]
            meta["mode"] = state.get("mode", "ask")
            sid = sess.save_session(project_dir, history, meta)
            try:
                from . import undo as undo_mod
                undo_mod.save_stack(project_dir)
            except Exception:
                pass
            try:
                api.set_config("llm_mode", state.get("mode", "ask"))
            except Exception:
                pass
            if any(turn_counts.values()):
                print("  " + ui.explored(turn_counts["reads"],
                                         turn_counts["edits"],
                                         turn_counts["commands"]))
                turn_counts.update(reads=0, edits=0, commands=0)
        except Exception:
            pass

    def _context_builder(request):
        idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
        parts = [f"Project context:\n{_build_context(project_dir, request)}\n\n"
                 f"{indexer.index_to_text(idx, max_files=25)}"]
        try:
            from . import upload as up_mod
            for u in uploads:
                parts.append(up_mod.format_for_context(u))
        except Exception:
            pass
        return "\n\n".join(parts)

    try:
        from . import repl as repl_mod
        from . import costs as costs_mod
    except ImportError:
        print(f"  {ui.chip('error', 'error')} copilot REPL not available")
        return
    # Wire the compact engine's model config into the repl
    try:
        from . import compact as compact_mod
        repl_mod._CURRENT_MODEL.update({
            "model": state.get("model") or "",
            "provider": state.get("provider") or "custom",
            "compact_threshold": api.get_config("llm_compact_threshold", 0.9),
            "compact_target": api.get_config("llm_compact_target", 0.75),
        })
        if not api.get_config("llm_compact_model"):
            print("  " + compact_mod.recommend_line())
    except Exception:
        pass

    # Auto-compact + guard + meter hooks
    uploads = []
    undo_pending = []

    def _pre_request(history):
        try:
            from . import compact as compact_mod
            window = compact_mod.context_window(state.get("provider") or "custom",
                                                state.get("model") or "")
            threshold = float(api.get_config("llm_compact_threshold", 0.9))
            target = float(api.get_config("llm_compact_target", 0.75))
            if compact_mod.should_compact(history, window, threshold):
                print("  " + ui.thinking(
                    f"auto-compact at {int(threshold * 100)}% of "
                    f"{window} tokens..."))
                def _cmodel(messages):
                    cm = api.get_config("llm_compact_model")
                    if cm and cm != state.get("model"):
                        st2 = dict(state); st2["model"] = cm
                        return _request(st2, messages)
                    return _request(state, messages)
                nh, stats = compact_mod.compact_history(
                    history, _cmodel, window, threshold=threshold, target=target)
                if stats.get("compacted"):
                    print(f"  {ui.chip('compacted', 'done')} "
                          f"{stats['tokens_before']} → {stats['tokens_after']} "
                          f"tokens ({stats.get('chunks', 0)} chunks)")
                    return nh
        except Exception:
            pass
        return history

    def _post_turn(history):
        try:
            from . import compact as compact_mod
            window = compact_mod.context_window(state.get("provider") or "custom",
                                                state.get("model") or "")
            print("  " + compact_mod.render_meter(history, window))
        except Exception:
            pass

    # Two-mode router for the classic REPL: chat stays lightweight, only
    # agent-prefixed inputs get the heavy plan history.
    orig_get_request = _get_request
    def _get_request_guarded(messages):
        try:
            last_user = next((m.get("content", "") for m in reversed(messages)
                              if m.get("role") == "user"), "")
            if _classify_mode(last_user) == "chat":
                idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
                system = (llm_agent.CHAT_PROMPT
                          + "\n\nThis conversation happens inside a real project. "
                            "Names like 'eshell', 'run.py', 'ep.py' refer to THIS "
                            "project's files (see the index). Never answer with "
                            "Emacs/other tools. For edits or agentic tasks, prefix /fix."
                          + "\n\nProject index:\n"
                          + indexer.index_to_text(idx, max_files=40))
                msgs = [{"role": "system", "content": system}]
                msgs.extend([m for m in messages if m.get("role") == "user"][-4:])
                messages = msgs
        except Exception:
            pass
        try:
            from . import guard as guard_mod
            if guard_mod.get_enabled():
                def _gmodel(prompt):
                    gm = api.get_config("llm_guard_model", "prompt-guard")
                    if state.get("provider") == "ollama" or gm:
                        st2 = dict(state)
                        st2["model"] = gm if gm else st2.get("model")
                        try:
                            t, e = _request(st2, [{"role": "user", "content": prompt}])
                            return t or ""
                        except Exception:
                            return ""
                msgs, res = guard_mod.guard_messages(messages, model_fn=_gmodel)
                if not res.get("ok") and res.get("quarantined"):
                    print(f"  {ui.warn_line('prompt guard: ' + '; '.join(res.get('reasons', [])))}")
                messages = msgs
        except Exception:
            pass
        return orig_get_request(messages)

    # undo snapshots around applies + per-message line stats
    def _apply_plan_undo(plan, pd, confirm_write=True):
        try:
            from . import undo as undo_mod
            paths = [f.get("path", "") for f in (plan.get("files") or [])]
            undo_mod.begin_turn(pd, paths)
        except Exception:
            pass
        res = _apply_plan(plan, pd, confirm_write=confirm_write)
        try:
            from . import undo as undo_mod
            undo_mod.end_turn(pd)
        except Exception:
            pass
        for f in plan.get("files") or []:
            act = f.get("action", "")
            if act == "read":
                turn_counts["reads"] += 1
            elif act in ("edit", "write"):
                turn_counts["edits"] += 1
        return res

    # Streaming responses (live, Claude-Code style)
    def _get_stream(messages, on_chunk):
        try:
            from . import providers as prov
            provider = state.get("provider") or "custom"
            base = state.get("base_url") or prov.PROVIDERS.get(provider, {}).get("base_url", "")
            model = state.get("model")
            if provider == "ollama":
                base = prov.OLLAMA_HEAD + "/v1"
                if not model:
                    model = "llama3.2"
            if not model:
                return None, "no model selected", ""
            return prov.stream_chat(provider, base, state.get("api_key"),
                                    model, messages, on_chunk,
                                    timeout=600 if provider == "ollama" else 300)
        except Exception as e:
            return None, str(e), ""

    final_mode = repl_mod.run_repl(
        api, state, _get_request_guarded, _apply_plan_undo,
        on_turn=_on_turn,
        system_prompt=_system_prompt(project_dir),
        context_builder=_context_builder,
        pre_request=_pre_request,
        uploads=uploads,
        post_turn=_post_turn,
        history=resume_history,
        get_stream=_get_stream,
        splash=None,
    )
    if final_mode:
        api.set_config("llm_mode", final_mode)
        print(f"  mode saved: {final_mode}")


def _resume_cmd(api, state, rest):
    """ai resume [id] — continue a past session (list when no id)."""
    project_dir = api.project_dir
    try:
        from . import session as sess
        from . import repl as repl_mod
    except ImportError:
        print(f"  {ui.chip('error', 'error')} session support missing")
        return
    sessions = sess.list_sessions(project_dir)
    if not rest:
        if not sessions:
            print("  No past sessions.")
            return
        print("  Past sessions (ai resume <id>):")
        for s in sessions[:10]:
            print(f"    {s['id']}  {s.get('model', '?')}  "
                  f"{s.get('turns', 0)} turns  — {s.get('summary', '')[:60]}")
        return
    sid = rest[0]
    data = sess.load_session(project_dir, sid)
    if not data:
        print(f"  Session not found: {sid}")
        return
    history = data.get("history", [])
    print(f"  Resuming session {sid} ({len(history)} messages)...")
    def _get_request(messages):
        return _request(state, messages)
    def _apply_plan(plan, pd, confirm_write=True):
        return llm_agent.interactive_apply(plan, pd, confirm_write=confirm_write)
    def _on_turn(h, event=None):
        try:
            sess.save_session(project_dir, h, {"mode": state.get("mode", "ask")})
        except Exception:
            pass
    repl_mod.run_repl(api, state, _get_request, _apply_plan,
                      on_turn=_on_turn, history=history,
                      system_prompt=_system_prompt(project_dir))


def _sessions_cmd(api):
    """ai sessions — list past sessions."""
    try:
        from . import session as sess
    except ImportError:
        print(f"  {ui.chip('error', 'error')} session support missing")
        return
    sessions = sess.list_sessions(api.project_dir)
    if not sessions:
        print("  No past sessions.")
        return
    print(f"  {len(sessions)} session(s):")
    for s in sessions[:10]:
        print(f"    {s['id']}  {s.get('model', '?')}  "
              f"{s.get('turns', 0)} turns  — {s.get('summary', '')[:60]}")


def _review_cmd(api, state, rest):
    """ai review — the model reviews the working-tree diff."""
    try:
        from . import review as rev
    except ImportError:
        print(f"  {ui.chip('error', 'error')} review support missing")
        return
    diff = rev.git_diff(api.project_dir)
    if not diff:
        print("  No changes to review (git diff HEAD is empty or not a repo).")
        return
    print("  Reviewing working-tree diff...")
    text = rev.review_changes(lambda m: _request(state, m), api.project_dir)
    print(rev.review_summary(text or "no review produced"))


def _doctor_cmd(api):
    """ai doctor — environment checks."""
    try:
        from . import initdocs as doc
    except ImportError:
        print(f"  {ui.chip('error', 'error')} doctor support missing")
        return
    checks = doc.doctor(api.project_dir)
    print(doc.render(checks))


def _init_cmd(api):
    """ai init — ensure AGENTS.md / RULES.md / TODO.md exist."""
    try:
        from . import initdocs as doc
    except ImportError:
        print(f"  {ui.chip('error', 'error')} init support missing")
        return
    created = doc.ensure_instructions(api.project_dir)
    if created:
        for name in created:
            print(f"  {ui.chip('ok', 'done')} created {name}")
    else:
        print("  AGENTS.md / RULES.md / TODO.md already present.")


def _cost_cmd(api, state, rest):
    """ai cost — session cost summary."""
    try:
        from . import costs as costs_mod
        if hasattr(costs_mod, "session_cost"):
            print(costs_mod.session_cost(api, state))
            return
        print(costs_mod.SessionCost().render())
    except Exception as e:
        print(f"  {ui.chip('error', 'error')} {e}")


AGENT_PREFIXES = ("/fix", "/edit", "/tool", "/write", "/plugin", "/agent",
                  "/test", "/search", "/upload", "/review", "/refactor")

# Task-intent phrases: plain-language requests that need the agent (tools,
# files, edits). Routed to agent mode automatically instead of chat.
AGENT_INTENT = (
    "find a bug", "find bugs", "look for a bug", "look for bugs",
    "spot the bug", "check bugs", "check for bugs", "check the codebase",
    "check the project", "check for issues", "find issues", "find the bug",
    "is there a bug", "any bugs", "debug", "test the", "run the tests",
    "search the codebase", "search the project", "analyze", "inspect",
    "refactor", "fix the", "fix a", "fix it", "fix this", "fix that",
    "create a", "create an", "write a", "write an", "add a", "add an",
    "implement", "review the code", "review", "explain the code",
    "explain how", "how does", "what does", "where is", "find the",
    "look at", "look for", "check the",
)


def _classify_mode(line):
    """Two-mode router: explicit /fix-style prefixes and task-intent phrases
    run in agent mode (tools, files, edits); everything else is lightweight
    chat (small models choke on JSON for chit-chat)."""
    l = line.strip().lower()
    if l.startswith(AGENT_PREFIXES):
        return "agent"
    if l.startswith("/"):
        return "command"   # slash commands handled by the UI, not the model
    if any(k in l for k in AGENT_INTENT):
        return "agent"
    return "chat"


def _agent_tui(state, api, rest):
    """Full-screen HELL'S CODE TUI session. The agent logic runs on a
    background thread, talking to the frame loop through a Bridge."""
    try:
        from . import tui as tui_mod
    except ImportError:
        print(f"  {ui.chip('error', 'error')} TUI unavailable — using classic REPL")
        _agent_cc(state, api, rest)
        return
    _submit_history = {"chat": [], "agent": [], "_agent_done": False}
    project_dir = api.project_dir
    mode = (rest[0].lower() if rest and rest[0] in ("plan", "auto", "ask")
            else api.get_config("llm_mode", "ask"))
    state["mode"] = mode
    theme = api.get_config("llm_tui_theme", "hellfire")

    def _submit(line, bridge):
        """Agent thread: one user turn through the bridge, TWO-MODE:
        chat (lightweight prompt, no JSON) vs agent (heavy prompt, tools)."""
        try:
            from . import session as sess
        except Exception:
            pass
        line = llm_agent.strip_ansi(line).strip()
        if not line:
            return  # empty-input guard — no ghost submissions
        mode = _classify_mode(line)
        hist = _submit_history.setdefault(mode, [])
        # agent history resets after each completed task (fresh brain)
        if mode == "agent" and _submit_history.get("_agent_done"):
            hist = []
            _submit_history["agent"] = hist
            _submit_history["_agent_done"] = False
        if mode == "chat":
            idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
            system = (llm_agent.CHAT_PROMPT
                      + "\n\nThis conversation happens inside a real project. "
                        "Names like 'eshell', 'run.py', 'ep.py', 'player.py', "
                        "'plugins/llm' refer to THIS project's files (see the index). "
                        "Never answer with Emacs/other tools. For edits or agentic "
                        "tasks, the user will prefix /fix."
                      + "\n\nProject index:\n"
                      + indexer.index_to_text(idx, max_files=40)
                      + "\n\nRelevant file content for this question:\n"
                      + _build_context(project_dir, line, max_lines=120, budget=8000))
            messages = [{"role": "system", "content": system}]
            messages.extend(hist[-10:])
            messages.append({"role": "user", "content": line})
        else:
            repro = _reproduce(project_dir, line, timeout=20)
            idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
            context = (f"Project context:\n{_build_context(project_dir, line)}\n\n"
                       f"{indexer.index_to_text(idx, max_files=20)}"
                       + (f"\n\n{repro}" if repro else ""))
            messages = [{"role": "system", "content": llm_agent.AGENT_PROMPT}]
            if context:
                messages.append({"role": "user", "content": context})
            messages.append({"role": "user", "content": line})
        if mode == "chat":
            messages.append({"role": "user", "content": line})

        bridge.thinking(True)
        chunks = []
        try:
            from . import providers as prov
            provider = state.get("provider") or "custom"
            base = state.get("base_url") or prov.PROVIDERS.get(provider, {}).get("base_url", "")
            model = state.get("model")
            if provider == "ollama":
                base = prov.OLLAMA_HEAD + "/v1"
                if not model:
                    model = "llama3.2"
            text, err, thinking = prov.stream_chat(
                provider, base, state.get("api_key"), model, messages,
                lambda t: (chunks.append(t), bridge.stream(t))[1],
                timeout=600 if provider == "ollama" else 300)
        except Exception as e:
            text, err, thinking = None, str(e), ""
        bridge.thinking(False)
        if err:
            bridge.feed(f"[error] {err}", "err")
            return
        if not text:
            bridge.feed("(no reply)", "dim")
            return
        hist.append({"role": "user", "content": line})
        hist.append({"role": "assistant", "content": text})
        if mode == "chat":
            # the reply already streamed as chunks — no duplicate feed
            try:
                sess.save_session(project_dir, hist[-6:],
                                  {"mode": "chat", "uploads": []})
            except Exception:
                pass
            return
        # agent mode: plan handling through the bridge
        plan = llm_agent.parse_plan(text)
        if plan is not None and plan.get("done"):
            bridge.feed(f"done: {plan.get('summary', '')}", "ok")
            _submit_history["_agent_done"] = True
            hist = []
            _submit_history["agent"] = hist
            return
        if plan is None or not (plan.get("files") or plan.get("commands")
                                or plan.get("tests") or plan.get("todo")
                                or plan.get("search") or plan.get("memory")):
            return  # already streamed as chunks — no duplicate feed
        bridge.feed(f"plan: {plan.get('summary', 'no summary')}", "accent2")
        cmds = plan.get("commands") or []
        if cmds:
            try:
                from . import exec as safe_exec
                for c in cmds:
                    cmd = c.get("cmd") if isinstance(c, dict) else str(c)
                    bridge.box_open(f"command: {cmd[:40]}")
                    def _on_line(ln, bridge=bridge):
                        bridge.box_line(ln)
                    res = safe_exec.run_command_streaming(cmd, project_dir, _on_line)
                    bridge.box_close(f"exit {res.get('exit_code')}")
                    bridge.feed("  " + safe_exec.chat_line({**res, "cmd": cmd}), "dim")
            except Exception as e:
                bridge.feed(f"[command error] {e}", "err")
        files = plan.get("files") or []
        if files:
            for f in files:
                act = f.get("action", "edit")
                bridge.feed(f"  {act:6s} {f.get('path', '?')}", "dim")
            applied, skipped, msgs = _apply_plan_tui(plan, bridge, project_dir)
            for m in msgs:
                bridge.feed(m, "ok" if "wrote" in m or "edited" in m else "dim")
            for rel, why in skipped:
                bridge.feed(f"  skipped {rel}: {why}", "dim")
        try:
            sess.save_session(project_dir,
                              [{"role": "user", "content": line},
                               {"role": "assistant", "content": text}],
                              {"mode": "agent", "uploads": []})
        except Exception:
            pass
        bridge.status(f"{state.get('provider')}/{state.get('model') or '?'}")

    def _apply_plan_tui(plan, bridge, project_dir):
        """Apply a plan through the TUI bridge (gatekeeper for approvals)."""
        applied, skipped, msgs = 0, [], []
        for f in plan.get("files") or []:
            rel = f.get("path", "")
            act = f.get("action", "edit")
            try:
                target = llm_agent.safe_path(project_dir, rel)
            except ValueError as e:
                skipped.append((rel, str(e)))
                continue
            if act == "read":
                if target.exists():
                    bridge.feed(f"  read {rel}", "dim")
                continue
            if act == "delete":
                ans = bridge.ask(f"delete {rel}?", "", ("y", "n"))
                if ans != "y":
                    skipped.append((rel, "delete declined"))
                    continue
                if target.exists():
                    target.unlink()
                    applied += 1
                    msgs.append(f"  deleted {rel}")
                continue
            if act == "write":
                ans = bridge.ask(f"write {rel}?", "", ("y", "n", "e"))
                if ans == "n":
                    skipped.append((rel, "declined"))
                    continue
                if ans == "e":
                    # edit block: replace content via a temp file + editor
                    import tempfile, subprocess as _sp
                    tmp = tempfile.mktemp(suffix=".txt")
                    with open(tmp, "w") as fh:
                        fh.write(f.get("content", ""))
                    editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "nano"))
                    try:
                        _sp.run([editor, tmp])
                        with open(tmp) as fh:
                            f["content"] = fh.read()
                    except Exception:
                        pass
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(f.get("content", ""), encoding="utf-8")
                applied += 1
                msgs.append(f"  wrote {rel}")
                continue
            # edit (line ranges / search-replace)
            if not target.exists():
                skipped.append((rel, "file does not exist"))
                continue
            old_text = target.read_text(encoding="utf-8", errors="replace")
            new_text = old_text
            if f.get("lines") is not None:
                lo = int(f["lines"][0])
                hi = int(f["lines"][1]) if len(f["lines"]) > 1 and f["lines"][1] is not None else lo
                lines = old_text.splitlines()
                if lo < 1 or hi < lo or hi > len(lines):
                    skipped.append((rel, "lines out of range"))
                    continue
                new_text = "\n".join(lines[:lo - 1] + f.get("replace", "").splitlines()
                                    + lines[hi:])
            else:
                edits = f.get("edits") or []
                ok = True
                for pair in edits:
                    search, replace = pair.get("search", ""), pair.get("replace", "")
                    if new_text.count(search) != 1:
                        skipped.append((rel, f"search not unique ({new_text.count(search)})"))
                        ok = False
                        break
                    new_text = new_text.replace(search, replace)
                if not ok:
                    continue
            if new_text != old_text:
                ans = bridge.ask(f"edit {rel}?", "", ("y", "n", "e"))
                if ans == "n":
                    skipped.append((rel, "declined"))
                    continue
                target.write_text(new_text, encoding="utf-8")
                applied += 1
                try:
                    from . import undo as undo_mod
                    undo_mod.begin_turn(project_dir, [rel])
                    undo_mod.end_turn(project_dir)
                except Exception:
                    pass
                msgs.append(f"  edited {rel}")
        return applied, skipped, msgs

    def _run(stdscr):
        app = tui_mod.HellTui(palette_name=theme, on_submit=_submit)
        app.run(stdscr)

    try:
        import threading as _th
        threading = _th
        tui_mod.curses.wrapper(_run)
    except Exception as e:
        print(f"  TUI failed ({e}) — falling back to classic REPL")
        _agent_cc(state, api, rest)


def _agent_repl(api, state):
    """Interactive multi-turn agent session. You talk to the agent like a
    chat, but it can read files, edit line ranges, create files and run safe
    commands — every proposed change is reviewed inline (y/n/v/a/q), then
    the conversation continues. 'quit' / Ctrl-C exits."""
    project_dir = api.project_dir
    from . import diffview as dv
    print(ui.banner({"model": state.get("model") or "?",
                     "provider": providers.PROVIDERS.get(state["provider"], {}).get("label", state["provider"]),
                     "multi_agent": "on" if state.get("agents_enabled") else "off"}))
    ui.section("interactive agent session")
    print("  Ask anything. The agent can read files, edit line ranges, create")
    print("  files, run safe commands and the test suite — changes are reviewed")
    print("  inline. 'quit' or Ctrl-C exits.")
    history = [{"role": "system", "content": _system_prompt(project_dir)}]
    idx = None
    if state.get("index_enabled", True):
        idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
    try:
        while True:
            try:
                if sys.stdin.isatty():
                    line = input(ui.prompt("you"))
                else:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    line = line.strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line or line.strip().lower() in ("quit", "exit", "bye"):
                break
            ui.thinking("thinking...")
            repro = _reproduce(project_dir, line, timeout=20)
            prompt = (f"User: {line}\n\n"
                      f"Project context:\n{_build_context(project_dir, line)}\n\n"
                      f"{indexer.index_to_text(idx, max_files=25)}\n\n"
                      + (f"{repro}\n\n" if repro else "")
                      + "Answer questions in plain text. When changes are needed, "
                      "reply with the JSON plan format "
                      "(read/edit/write/commands/tests/todo).")
            history.append({"role": "user", "content": prompt})
            text, err = _request(state, history)
            if err:
                print(f"  {ui.chip('error', 'error')} {err}")
                history.pop()
                continue
            plan = llm_agent.parse_plan(text)
            if plan is not None and (plan.get("files") or plan.get("commands")
                                     or plan.get("tests") or plan.get("todo")):
                print(f"  {ui.chip('plan', 'plan')} {plan.get('summary', 'no summary')}")
                cmds = plan.get("commands") or []
                cmd_out = ""
                if cmds:
                    results, chat_lines = llm_agent.execute_plan_commands(plan, project_dir)
                    for l in chat_lines:
                        print(f"  {dv.dim(l)}")
                    cmd_out = "\n".join(
                        f"$ {r.get('cmd')}\n{r.get('output', '')[:1200]}"
                        for r in results if not r.get("blocked"))
                applied, skipped, msgs = llm_agent.interactive_apply(
                    plan, project_dir)
                for m in msgs:
                    print(m)
                for rel, why in skipped:
                    print(f"  {dv.dim('skipped')} {rel}: {why}")
                note = (f"Applied {len(msgs)} change(s); skipped: "
                        f"{', '.join(r for r, _ in skipped) or 'none'}.")
                if any(m.startswith("  edited") or m.startswith("  wrote")
                       or m.startswith("  deleted") for m in msgs):
                    for f in plan.get("files") or []:
                        rel = f.get("path", "")
                        if rel.endswith(".py"):
                            ok, reason = _syntax_check(project_dir, rel)
                            note += (f" Syntax check {rel}: "
                                     f"{'ok' if ok else 'FAILED: ' + reason}")
                if cmd_out:
                    note += f" Commands run:\n{cmd_out[:800]}"
                todos = plan.get("todo")
                if todos:
                    try:
                        from . import todo as todo_mod
                        added, marked = todo_mod.apply_todo(
                            todos, Path(project_dir) / "TODO.md")
                        if added or marked:
                            print(f"  {ui.chip('todo', 'done')} TODO.md: "
                                  f"{added} added, {marked} checked off")
                            note += f" TODO.md updated ({added} added, {marked} done)."
                    except Exception:
                        pass
                if plan.get("tests"):
                    try:
                        from . import tests_runner as tr
                        print(f"  {ui.chip('test', 'test')} running tests...")
                        out = tr.auto_fix_loop(
                            project_dir,
                            lambda msgs: _request(state, msgs),
                            plan,
                            lambda p, pd: llm_agent.interactive_apply(p, pd),
                            max_rounds=3)
                        summ = tr.summarize(out.get("final_results", []))
                        print(summ)
                        note += f"\nTests:\n{summ[:800]}"
                    except Exception as e:
                        print(f"  {ui.chip('error', 'error')} tests: {e}")
                history.append({"role": "assistant", "content": text})
                history.append({"role": "user", "content": f"[tool result] {note}"})
            elif plan is not None and plan.get("done"):
                print(f"  {ui.chip('done', 'done')} {plan.get('summary', '')}")
                history.append({"role": "assistant", "content": text})
            else:
                print(ui.wrap(text or "", prefix="  agent> "))
                history.append({"role": "assistant", "content": text})
    except KeyboardInterrupt:
        pass
    print("  session ended")


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
                    line = input(ui.prompt("you"))
                else:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    line = line.strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line or line.strip().lower() in ("quit", "exit"):
                break
            ui.thinking("thinking...")
            history.append({"role": "user", "content": line})
            text, err = _request(state, history)
            if err:
                print(f"  {ui.chip('error', 'error')} {err}")
                break
            print(ui.wrap(text or "", prefix="  ai> "))
            history.append({"role": "assistant", "content": text})
    except KeyboardInterrupt:
        pass


ENTRY_POINTS = {"eshell", "run", "ep", "player", "eshell.py", "run.py",
                "ep.py", "player.py"}


def _reproduce(project_dir, request, timeout=25):
    """Reproduce the reported failure: when the request names an entry-point
    script, run it with the mentioned subcommand (or 'help') and capture the
    real exit code + output for the model. Returns prompt block or ''."""
    import re as _re
    from . import exec as safe_exec
    files = _re.findall(r"([\w./\\-]+\.py)", request)
    bare = _re.findall(r"(?<![\w./])([A-Za-z_]\w*)(?![\w.])", request)
    entry = None
    is_known_entry = False
    for f in files:
        if f.split("/")[-1] in ENTRY_POINTS:
            entry, is_known_entry = f, True
            break
    if entry is None:
        for b in bare:
            if b in ENTRY_POINTS:
                entry, is_known_entry = b + ".py", True
                break
    if entry is None and files:
        # any named .py that looks like a script (has __main__ guard)
        cand = files[0].replace("\\", "/").lstrip("./")
        try:
            target = (Path(project_dir) / cand).resolve()
            if str(target).startswith(str(Path(project_dir).resolve())) and target.is_file():
                src = target.read_text(encoding="utf-8", errors="replace")
                if "__main__" in src:
                    entry = cand
        except Exception:
            pass
    if entry is None:
        return ""
    # subcommand words mentioned in the request
    sub_words = ["compile", "play", "lint", "check", "help", "stats", "tracks",
                 "inspect", "transpose", "tempo", "merge", "new", "convert",
                 "generate", "encrypt", "info"]
    if is_known_entry:
        sub = next((w for w in sub_words if _re.search(rf"\b{w}\b", request, _re.I)), "help")
    else:
        sub = None
    cmd = f"{sys.executable} {entry}" + (f" {sub}" if sub else "")
    res = safe_exec.run_command(cmd, project_dir, timeout=timeout)
    out = res.get("output", "")
    if res.get("blocked"):
        return ""
    status = f"exit {res.get('exit_code')}" if res.get("exit_code") is not None else "no output"
    line = f"Reproduction: `{cmd}` → {status} ({res.get('duration_s', 0)}s)"
    if res.get("ok"):
        line += " (ran without error)"
        snippet = out[:800]
        if snippet:
            line += f"\nOutput:\n{snippet}"
    else:
        line += f"\nERROR OUTPUT:\n{out[:2000]}"
    return line


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
        ui.section(f"step {steps}/{max_steps}")
        if plugin:
            prompt = (
                f"Create a HELLFORGE plugin that: {request}\n\n"
                "The plugin lives in plugins/<name>/__init__.py and registers via "
                "def register(api): api.add_command('name', handler, help) or "
                "api.on('post_compile', fn) etc. Respond with the JSON plan format "
                "(action write)."
            )
        else:
            repro = _reproduce(project_dir, request)
            prompt = (
                f"The user reports this issue / wants this change: {request}\n\n"
                f"Project context:\n{_build_context(project_dir, request)}\n\n"
                f"{indexer.index_to_text(idx, max_files=30)}\n\n"
                + (f"{repro}\n\n" if repro else "")
                + "You may use 'read' to inspect files, 'commands' to run checks "
                "(e.g. python tests/...), and write/edit to change files. "
                "When the change is complete (or on the final step), reply "
                '{"done": true, "summary": "..."}. Respond with the JSON plan format.'
            )
        messages = [
            {"role": "system", "content": _system_prompt(project_dir)},
            {"role": "user", "content": prompt},
        ]
        ui.thinking(f"asking {state.get('provider')}/{state.get('model') or '?'}...")
        text, err = _request_visible(state, messages)
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

        # 2. Tests: plan may carry "tests" — run the suite with the auto-fix
        # loop (baseline → apply → retest → model fixes → retest until green).
        files = plan.get("files") or []
        test_summary = None
        try:
            from . import tests_runner as tr
        except ImportError:
            tr = None
        if tr is not None and tr.plan_test_targets(plan) is not None:
            applied_any = False
            print(f"  {ui.chip('test', 'test')} running tests (auto-fix loop)...")
            def _model_fn(msgs):
                return _request(state, msgs)
            def _apply_fn(p, pd):
                return llm_agent.interactive_apply(p, pd, confirm_write=confirm_write)
            out = tr.auto_fix_loop(project_dir, _model_fn, plan, _apply_fn, max_rounds=3)
            test_summary = tr.summarize(out.get("final_results", []))
            print(test_summary)
            if out.get("rounds", 0) > 1:
                print(f"  {ui.chip('fixed', 'done')} auto-fix loop: "
                      f"{out['rounds']} round(s), {out.get('fixes_applied', 0)} fix(es) applied")
            # auto_fix_loop applied the files itself — skip the apply block.
        elif files:
            # 2b. Files — review the colored diff and apply
            for f in files:
                print(f"    {f.get('action', '?'):6s} {f.get('path', '?')}")
            applied, skipped, msgs = llm_agent.interactive_apply(
                plan, project_dir, confirm_write=confirm_write)
            applied_any = applied > 0
            for m in msgs:
                print(m)
            for rel, why in skipped:
                print(f"  {dv.dim('skipped')} {rel}: {why}")
        else:
            applied_any = False
        # Auto syntax check: any edited/written .py must still parse.
        if applied_any:
            for f in files:
                rel = f.get("path", "")
                if not rel.endswith(".py"):
                    continue
                ok, reason = _syntax_check(project_dir, rel)
                if ok:
                    print(f"  {dv.dim(f'syntax ok: {rel}')}")
                else:
                    print(f"  {dv.red(f'syntax error in {rel}: {reason}')}")

        # 2c. TODO: plan may carry "todo" — update the agent checklist.
        todos = plan.get("todo")
        if todos:
            try:
                from . import todo as todo_mod
                added, marked = todo_mod.apply_todo(
                    todos, Path(project_dir) / "TODO.md")
                if added or marked:
                    print(f"  {ui.chip('todo', 'done')} TODO.md: "
                          f"{added} added, {marked} checked off")
            except Exception:
                pass

        # 2d-prime. Search: plan may carry "search" — index + query the
        # codebase; results are printed and fed back.
        sq = plan.get("search")
        if sq:
            try:
                from . import search as search_mod
                q = sq.get("query", "") if isinstance(sq, dict) else str(sq)
                tk = sq.get("top", 5) if isinstance(sq, dict) else 5
                if q and search_mod.is_stale(project_dir):
                    search_mod.build_search_index(project_dir)
                if q:
                    print(f"  {ui.chip('search', 'command')} {q}")
                    print(search_mod.run_query(project_dir, q, top_k=tk))
            except Exception as e:
                print(f"  {ui.chip('error', 'error')} search: {e}")

        # 2e. Memory/notes/tickets plan keys.
        if plan.get("memory") or plan.get("note") or plan.get("tickets"):
            try:
                from . import memory as mem_mod
                mpath = Path(project_dir) / "MEMORY.md"
                if plan.get("memory"):
                    added, removed = mem_mod.apply_memory(
                        plan["memory"], mpath)
                    print(f"  {ui.chip('memory', 'done')} MEMORY.md: "
                          f"{added} added, {removed} removed")
                if plan.get("note"):
                    mem_mod.add_note(Path(project_dir) / "NOTES.md",
                                     plan["note"].get("text", ""))
                    print(f"  {ui.chip('note', 'done')} NOTES.md updated")
                if plan.get("tickets"):
                    n = mem_mod.apply_tickets(
                        plan["tickets"], Path(project_dir) / "TICKETS.md")
                    print(f"  {ui.chip('ticket', 'done')} TICKETS.md: {n} applied")
            except Exception as e:
                print(f"  {ui.chip('error', 'error')} memory: {e}")

        # 2d. Subagents: plan may carry "subagents" — spawn focused child
        # chats; results are fed back to the main loop.
        subs = plan.get("subagents")
        if subs:
            try:
                from . import subagents as sub_mod
                print(f"  {ui.chip('subagent', 'command')} spawning "
                      f"{len(subs)} subagent(s)...")
                results = sub_mod.run_plan_subagents(
                    plan, lambda msgs: _request(state, msgs))
                summary = sub_mod.summarize(results)
                print(summary)
            except Exception as e:
                print(f"  {ui.chip('error', 'error')} subagents: {e}")

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
        text, err = _request_visible(state, messages)
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
        test_summary = None
        if tr is not None and tr.plan_test_targets(plan) is not None:
            applied_any = False
            print(f"  {ui.chip('test', 'test')} running tests (auto-fix loop)...")
            def _model_fn2(msgs):
                return _request(state, msgs)
            def _apply_fn2(p, pd):
                return llm_agent.interactive_apply(p, pd, confirm_write=confirm_write)
            out = tr.auto_fix_loop(project_dir, _model_fn2, plan, _apply_fn2, max_rounds=3)
            test_summary = tr.summarize(out.get("final_results", []))
            print(test_summary)
            if out.get("rounds", 0) > 1:
                print(f"  {ui.chip('fixed', 'done')} auto-fix loop: "
                      f"{out['rounds']} round(s), {out.get('fixes_applied', 0)} fix(es) applied")
        elif files:
            applied, skipped, msgs = llm_agent.interactive_apply(
                plan, project_dir, confirm_write=confirm_write)
            for m in msgs:
                print(m)
            for rel, why in skipped:
                print(f"  {dv.dim('skipped')} {rel}: {why}")
        todos = plan.get("todo")
        if todos:
            try:
                from . import todo as todo_mod
                added, marked = todo_mod.apply_todo(
                    todos, Path(project_dir) / "TODO.md")
                if added or marked:
                    print(f"  {ui.chip('todo', 'done')} TODO.md: "
                          f"{added} added, {marked} checked off")
            except Exception:
                pass
        if (state.get("agents_enabled") and (files or cmds)
                and state.get("agent_model")):
            _daughter_verify(api, state, request, project_dir)
        request = f"Continue: {request}"

    print(f"\n  Finished after {steps} step(s).")


def _syntax_check(project_dir, rel):
    """Compile-check a .py file with the project interpreter. Returns
    (ok, detail)."""
    from . import exec as safe_exec
    res = safe_exec.run_command(
        f"{sys.executable} -m py_compile {rel}", project_dir, timeout=30)
    if res.get("ok"):
        return True, ""
    return False, (res.get("output") or res.get("error") or "compile failed")[:400]


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


def _build_context(project_dir, request, max_files=3, max_lines=500, budget=60000,
                   keyword_radius=25):
    """Compact project context for agentic prompts: a top-level tree plus the
    contents of files the request explicitly names (up to budget bytes).
    Names may include or omit the extension ('eshell' → eshell.py).
    KEYWORD-AWARE: for each matched file, lines around request keywords are
    included (not just the file head) so the model sees the RELEVANT code."""
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
    bare = re.findall(r"(?<![\w./])([A-Za-z_][\w-]*)(?![\w.])", request)
    bare = [b for b in bare if b.lower() not in ("fix", "bug", "add", "the", "and",
                                                 "with", "that", "this", "run",
                                                 "file", "code", "issue", "why",
                                                 "find", "still", "it", "on")]
    # keyword set from the request for in-file search
    stop = set(("fix", "bug", "add", "the", "and", "with", "that", "this", "run",
                "file", "code", "issue", "why", "find", "still", "it", "on",
                "for", "in", "to", "a", "of", "exits", "exit"))
    keywords = [w.lower() for w in re.findall(r"[A-Za-z_]\w*", request)
                if w.lower() not in stop and len(w) >= 3]

    def _keyword_windows(text, max_windows=10, per_kw=4):
        """Windows around keyword matches. Matches per keyword are spread
        evenly across the file (first/middle/last) so early noise (like the
        file name appearing in its own header) never starves the tail."""
        lines = text.splitlines()
        windows, seen_spans = [], []
        for kw in keywords:
            hits = [m for m in re.finditer(re.escape(kw), text, re.IGNORECASE)]
            if not hits:
                continue
            picks = {hits[0]}
            if len(hits) > 1:
                picks.add(hits[-1])
            if len(hits) > 2:
                picks.add(hits[len(hits) // 2])
            for m in sorted(picks, key=lambda x: x.start()):
                ln = text[:m.start()].count("\n")
                lo, hi = max(0, ln - keyword_radius), min(len(lines), ln + keyword_radius + 1)
                if any(lo < s[1] and hi > s[0] for s in seen_spans):
                    continue
                seen_spans.append((lo, hi))
                windows.append((lo, hi))
                if len(windows) >= max_windows:
                    return windows
        return windows

    def _include(target, rel):
        text = target.read_text(encoding="utf-8", errors="replace")
        size = target.stat().st_size
        lines = text.splitlines()
        # Keyword windows (context around matches) — prioritized.
        windows = _keyword_windows(text)
        merged = []
        for lo, hi in sorted(windows):
            if merged and lo <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], hi))
            else:
                merged.append((lo, hi))
        if not merged:
            merged = [(0, min(len(lines), 40))]
        block_lines = []
        for lo, hi in merged[:12]:
            for i in range(lo, hi):
                block_lines.append(f"{i + 1:5} | {lines[i]}")
            if hi < len(lines):
                block_lines.append(f"      | ...")
        body = "\n".join(block_lines[:max_lines])
        if len(block_lines) > max_lines:
            body += f"\n      | ... ({len(block_lines) - max_lines} more context lines)"
        parts.append(f"--- {rel} ({size} bytes) [lines around: "
                     f"{', '.join(f'{a + 1}-{b}' for a, b in merged[:4])}] ---\n{body}")
        return len(body)

    used = 0
    seen_files = set()
    for rel in named[:max_files]:
        rel = rel.replace("\\", "/").lstrip("./")
        try:
            target = (root / rel).resolve()
            if not str(target).startswith(str(root)) or not target.is_file():
                continue
            used += _include(target, rel)
            seen_files.add(str(target))
            if used > budget:
                break
        except Exception:
            continue
    if len(bare) > 0 and used < budget:
        all_files = []
        for p in root.rglob("*"):
            if p.is_file() and not any(part.startswith(".") or part in
                                       (".venv", "node_modules", "__pycache__")
                                       for part in p.relative_to(root).parts):
                all_files.append(p)
        for name in bare[:max_files]:
            matches = [p for p in all_files
                       if p.stem.lower() == name.lower() or p.name.lower() == name.lower()]
            if not matches or str(matches[0]) in seen_files:
                continue
            target = matches[0]
            rel = str(target.relative_to(root))
            used += _include(target, rel)
            seen_files.add(str(target))
            if used > budget:
                break
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
