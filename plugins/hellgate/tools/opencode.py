"""hellgate tool: OpenCode (opencode-ai).

Runs the opencode TUI focused inside the project root. All launch-time
config lives under <project>/hellgate-state/opencode/: the opencode.json
(provider block for the active provider + model + knowledge instructions)
is passed via OPENCODE_CONFIG, and XDG_CONFIG/XDG_DATA/XDG_STATE_HOME are
redirected into hellgate-state so opencode never touches ~/.config or
~/.local/share.

The active provider is read from <project>/hellgate-state/provider.json
(written by the session before every launch); each provider id maps to its
own opencode provider block (see _opencode_cfg). When provider.json is
absent (older setups) it falls back to the ollama provider and streams a
note about it.

Agent presets (Music-Composer / Music-Refiner) are written as project
agents to <project>/.opencode/agents/<id>.md (never overwriting an existing
file) and selected with `--agent <id>`.

Verified against opencode 1.18.15: `opencode models` parses OPENCODE_CONFIG
generated for provider=ollama (lists the local model) and for
provider=anthropic with a dummy key (lists the anthropic models) without
calling any API; with XDG_* redirected, the session db, logs and locks all
land inside hellgate-state.
"""

import json
import os
import shutil
import subprocess

from .. import providers as P
from .. import util

DEFAULT_MODEL = os.environ.get(
    "HELLGATE_MODEL",
    "hf.co/bartowski/Qwen2.5-Coder-3B-Instruct-Abliterated-GGUF:latest",
)
DEFAULT_OLLAMA_URL = os.environ.get("HELLGATE_OLLAMA_URL", "http://127.0.0.1:11434/v1")

PROVIDER_IDS = ("ollama", "openai", "anthropic", "openrouter", "google", "custom")

TOOL = {
    "id": "opencode",
    "name": "OpenCode",
    "license": "MIT",
    "install_cmd": "npm i -g opencode-ai",
    "confined": True,
    "notes": "Config via OPENCODE_CONFIG + XDG_* redirected into hellgate-state; "
             "provider/model from hellgate-state/provider.json (ollama is one "
             "option); sessions/logs stay in hellgate-state.",
}


def _bin():
    return shutil.which("opencode")


def detect():
    return bool(_bin())


def _state_dir(project_dir):
    return os.path.join(project_dir, "hellgate-state", "opencode")


def _fallback_ollama():
    return {"id": "ollama", "name": "Ollama (local)",
            "model": DEFAULT_MODEL, "base_url": DEFAULT_OLLAMA_URL, "api_key": None}


def _provider(project_dir, stream_out):
    """Provider dict from hellgate-state/provider.json, or ollama fallback."""
    prov = P.read_provider_json(project_dir)
    if prov is None:
        stream_out("hellgate: no provider.json — falling back to ollama")
        return _fallback_ollama()
    if prov.get("id") not in PROVIDER_IDS:
        stream_out(f"hellgate: unknown provider '{prov.get('id')}' in provider.json "
                   "— falling back to ollama")
        return _fallback_ollama()
    return prov


def _ollama_model_url(prov):
    """Ollama model + base URL; HELLGATE_MODEL / HELLGATE_OLLAMA_URL override
    the provider.json values when set."""
    model = os.environ.get("HELLGATE_MODEL", prov.get("model") or DEFAULT_MODEL)
    url = os.environ.get("HELLGATE_OLLAMA_URL", prov.get("base_url") or DEFAULT_OLLAMA_URL)
    return model, url


def _opencode_cfg(prov):
    """provider.json -> opencode.json contents for the active provider.

    Keys live under provider.<id>.options (verified against opencode
    1.18.15: a top-level provider.<id>.apiKey is ignored — the binary's
    config loader merges the `options` object into the provider config).
    api_key is omitted when null (opencode then reads its own auth)."""
    pid = prov["id"]
    model = prov.get("model") or DEFAULT_MODEL
    url = prov.get("base_url")
    key = prov.get("api_key")
    cfg = {"autoupdate": False}
    if pid == "ollama":
        model, url = _ollama_model_url(prov)
        cfg["model"] = "ollama/" + model
        cfg["provider"] = {
            "ollama": {
                "options": {"baseURL": url},
                "models": {model: {"name": "HELLFORGE local (ollama)"}},
            }
        }
    elif pid == "anthropic":
        cfg["model"] = "anthropic/" + model
        if key:
            cfg["provider"] = {"anthropic": {"options": {"apiKey": key}}}
    elif pid == "openai":
        cfg["model"] = "openai/" + model
        opts = {}
        if key:
            opts["apiKey"] = key
        if url:
            opts["baseURL"] = url
        if opts:
            cfg["provider"] = {"openai": {"options": opts}}
    elif pid == "openrouter":
        cfg["model"] = "openrouter/" + model
        opts = {}
        if key:
            opts["apiKey"] = key
        if url:
            opts["baseURL"] = url
        if opts:
            cfg["provider"] = {"openrouter": {"options": opts}}
    elif pid == "google":
        cfg["model"] = "google/" + model
        if key:
            cfg["provider"] = {"google": {"options": {"apiKey": key}}}
    elif pid == "custom":
        # opencode requires the provider prefix in the model string; custom
        # endpoints ride on the openai provider block.
        cfg["model"] = "openai/" + model
        opts = {}
        if url:
            opts["baseURL"] = url
        if key:
            opts["apiKey"] = key
        if opts:
            cfg["provider"] = {"openai": {"options": opts}}
    return cfg


def _write_knowledge(state_dir, knowledge_dir):
    """Merge full.md + samples-index.md into state/knowledge.md. None if empty."""
    chunks = []
    names = (("current.md",) if os.path.isfile(os.path.join(knowledge_dir, "current.md"))
             else ("full.md", "samples-index.md"))
    for name in names:
        p = os.path.join(knowledge_dir, name)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                chunks.append(f"# {name}\n" + f.read())
    if not chunks:
        return None
    path = os.path.join(state_dir, "knowledge.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(chunks))
    return path


def _agent_md(project_dir, persona, agent_name, model):
    """Write .opencode/agents/<slug>.md under the project root (never clobber).

    Returns the agent id to pass as --agent, or None when the file already
    exists (the existing definition is reused then)."""
    slug = str(agent_name).lower().replace(" ", "-").replace("_", "-")
    agents_dir = os.path.join(project_dir, ".opencode", "agents")
    os.makedirs(agents_dir, exist_ok=True)
    path = os.path.join(agents_dir, slug + ".md")
    if os.path.exists(path):
        return slug
    body = (
        "---\n"
        f"description: {persona.splitlines()[0][:90]}\n"
        "mode: primary\n"
        f"model: {model}\n"
        "---\n"
        + persona
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(body)
    return slug


def launch(project_dir, agent, knowledge_dir, extra_args, stream_out=print):
    exe = _bin()
    if not exe:
        stream_out(f"hellgate: opencode not installed — run: {TOOL['install_cmd']}")
        return 1
    state = _state_dir(project_dir)
    os.makedirs(os.path.join(state, "xdg", "config"), exist_ok=True)
    os.makedirs(os.path.join(state, "xdg", "data"), exist_ok=True)
    os.makedirs(os.path.join(state, "xdg", "state"), exist_ok=True)

    prov = _provider(project_dir, stream_out)
    cfg = _opencode_cfg(prov)
    kfile = _write_knowledge(state, knowledge_dir)
    if kfile:
        cfg["instructions"] = [kfile]

    agent_args = []
    match = util.pick_agent(_load_agents(knowledge_dir), agent)
    persona = match["prompt"] if match else _inline_persona(agent)
    if persona:
        agent_id = _agent_md(project_dir, persona, agent, cfg["model"])
        if agent_id:
            agent_args = ["--agent", agent_id]
            stream_out(f"hellgate: opencode agent '{agent_id}' from .opencode/agents/")

    cfg_path = os.path.join(state, "opencode.json")
    with open(cfg_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)

    env = dict(os.environ)
    env["OPENCODE_CONFIG"] = cfg_path
    env["XDG_CONFIG_HOME"] = os.path.join(state, "xdg", "config")
    env["XDG_DATA_HOME"] = os.path.join(state, "xdg", "data")
    env["XDG_STATE_HOME"] = os.path.join(state, "xdg", "state")

    cmd = [exe] + agent_args + [str(a) for a in (extra_args or [])]
    util.say(f"opencode ({cfg['model']}) in {project_dir}", stream_out)
    p = subprocess.Popen(cmd, cwd=project_dir, env=env)
    try:
        return p.wait()
    except KeyboardInterrupt:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
        return 130


def _load_agents(knowledge_dir):
    """Parse agents.md (## Name heading → body). Empty list when absent."""
    p = os.path.join(knowledge_dir, "agents.md")
    if not os.path.isfile(p):
        return []
    agents = []
    try:
        with open(p, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return []
    current = None
    body = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") and not stripped.startswith("##"):
            continue
        if stripped.startswith("##"):
            if current:
                agents.append({"name": current, "prompt": "\n".join(body).strip()})
            current = stripped.lstrip("#").strip()
            body = []
        elif current is not None:
            body.append(line)
    if current:
        agents.append({"name": current, "prompt": "\n".join(body).strip()})
    return [a for a in agents if a["prompt"]]


def _inline_persona(agent):
    name = str(agent or "").lower()
    if name == "music-composer":
        return (
            "You are HELLFORGE-COMPOSER, a piano-music composer for the HELLFORGE (E) "
            "DSL. Your job: write complete, full-length HELLFORGE v5 songs — directives "
            "(@bpm, @key, @vol, @seed, ...), human-mode statements (play note/chord, "
            "pedal, rest, art), loops and macros — modeled on the samples/examples in "
            "this repo. Always deliver whole songs (with intro/development/outro), "
            "never fragments or placeholders. Keep every source valid v5 syntax."
        )
    if name == "music-refiner":
        return (
            "You are HELLFORGE-REFINER, an expert editor for the HELLFORGE (E) DSL. "
            "Your job: edit and optimize existing .ec sources — improve structure, "
            "dynamics, articulation and performance feel, tighten loops, fix "
            "non-idiomatic v5, and keep every edit small and surgical. Verify "
            "changes against the v5 syntax in SYNTAX.md before applying them."
        )
    return None
