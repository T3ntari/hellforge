"""Multi-agent orchestration for the copilot — opt-in, persisted in config.
Roles map to models (selectable from Ollama, or any custom model id).
First-run setup wizard runs when no copilot config exists (fresh machine)."""

import json

ROLES = [
    ("planner", "proposes the change plan for the user's request"),
    ("implementer", "turns the plan into concrete file edits"),
    ("reviewer", "critiques the plan/diff and catches mistakes"),
]

DEFAULT_ASSIGNMENTS = {
    "planner": None,
    "implementer": None,
    "reviewer": None,
}


def setup_wizard(api, state, providers, ollama_models):
    """First-run setup: provider → model per role → indexing → agents.
    Falls back to safe defaults when not on a TTY."""
    import sys
    from . import diffview as dv

    def _ask(prompt, default=None):
        try:
            if sys.stdin.isatty():
                return input(f"  {prompt} ").strip() or default
        except EOFError:
            pass
        return default

    print("  ── HELLFORGE Copilot setup ──")
    print("  Providers: " + ", ".join(providers.PROVIDERS))
    if providers.ollama_detected():
        print(f"  {dv.green('Ollama detected')} — {len(ollama_models())} local model(s)")
        choice = _ask("Use Ollama? [Y/n]", "y").lower()
        if choice != "n":
            state["provider"] = "ollama"
            state["base_url"] = providers.OLLAMA_HEAD + "/v1"
            models = ollama_models()
            if models:
                print("  Local models:")
                for i, m in enumerate(models, 1):
                    print(f"    [{i}] {m}")
                pick = _ask(f"Select model [1] (or type a custom name):", "1")
                try:
                    state["model"] = models[int(pick) - 1]
                except (ValueError, IndexError):
                    state["model"] = pick or models[0]
            else:
                state["model"] = _ask("Model name (e.g. llama3.2):", "llama3.2")
    else:
        print("  Ollama not detected on 127.0.0.1:11434")
        p = _ask("Provider [openai|deepseek|claude|custom]:", "deepseek").lower()
        state["provider"] = p if p in providers.PROVIDERS else "deepseek"
        state["base_url"] = providers.PROVIDERS[state["provider"]]["base_url"]
        state["model"] = providers.DEFAULT_MODEL.get(state["provider"]) or \
            _ask("Model name:", "")
        if state["provider"] == "custom":
            state["base_url"] = _ask("Base URL:", "http://127.0.0.1:11434/v1")
        key = _ask("API key (enter to skip):")
        if key:
            state["api_key"] = key

    # Indexing: offer the embedding model pick (Ollama only)
    idx_model = _ask("Indexing model from Ollama (enter to skip, not recommended):")
    if idx_model:
        state["index_model"] = idx_model
    else:
        state["index_model"] = None
    state["index_enabled"] = True

    # Multi-agent orchestration
    want = _ask("Enable multi-agent orchestration? [y/N]", "n").lower()
    state["agents_enabled"] = want == "y"
    if state["agents_enabled"]:
        assignments = {}
        for role, desc in ROLES:
            m = _ask(f"  Model for '{role}' ({desc}) — Enter = same as main:", "")
            assignments[role] = m or state["model"]
        state["agents"] = assignments
    state["setup_done"] = True
    return state


def orchestrate(roles, main_state, role):
    """State for a daughter agent: same provider/url/key as the main agent,
    with the role's assigned model."""
    st = dict(main_state)
    st["model"] = (roles or {}).get(role) or main_state.get("model")
    return st
