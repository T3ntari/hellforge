"""hellgate tool: Goose (block/goose, now aaif-goose/goose).

Runs the goose session TUI focused inside the project root. Confinement is
done with GOOSE_PATH_ROOT (verified: config dir, sessions db and logs all
move under it) plus XDG_STATE_HOME/XDG_DATA_HOME for the CLI's leftover
log files, so nothing is written to ~/.config/goose or ~/.local/share/goose.

The active provider is read from <project>/hellgate-state/provider.json
(written by the session before every launch); each provider id maps to its
GOOSE_PROVIDER value + API key env (see _goose_env). When provider.json is
absent (older setups) it falls back to the ollama provider and streams a
note about it.

Provider wiring (verified with goose 1.45.0): goose 1.45 has NO profile
files or GOOSE_PROFILE_DIR — the provider/model/base are configured through
environment variables. Verified env names (present in the goose 1.45.0
binary; there is NO generic GOOSE_API_KEY):
  ollama:     GOOSE_PROVIDER=ollama  GOOSE_MODEL=<model>  OLLAMA_HOST=<host>
  anthropic:  GOOSE_PROVIDER=anthropic  ANTHROPIC_API_KEY
  openai:     GOOSE_PROVIDER=openai  OPENAI_API_KEY  OPENAI_BASE_URL
  openrouter: GOOSE_PROVIDER=openrouter  OPENROUTER_API_KEY  (native provider)
  google:     GOOSE_PROVIDER=google  GOOGLE_API_KEY
  custom:     GOOSE_PROVIDER=openai (openai-compatible)  OPENAI_API_KEY  OPENAI_BASE_URL
GOOSE_TELEMETRY_OFF skips the first-run "share usage data" prompt, and
GOOSE_SYSTEM_PROMPT_FILE_PATH feeds the agent persona/knowledge into the
session system prompt.
"""

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
    "id": "goose",
    "name": "Goose",
    "license": "Apache-2.0",
    "install_cmd": "curl -fsSL "
                   "https://github.com/aaif-goose/goose/releases/download/stable/"
                   "download_cli.sh | CONFIGURE=false bash",
    "confined": True,
    "notes": "Confined via GOOSE_PATH_ROOT + XDG_* (goose 1.45 has no "
             "profile dir; provider/model/key via GOOSE_*/provider env, from "
             "hellgate-state/provider.json). Persona via "
             "GOOSE_SYSTEM_PROMPT_FILE_PATH.",
}


def _bin():
    return shutil.which("goose")


def detect():
    return bool(_bin())


def _state_dir(project_dir):
    return os.path.join(project_dir, "hellgate-state", "goose")


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


def _goose_env(prov):
    """provider.json -> GOOSE_PROVIDER / model / key / base URL env vars.

    api_key is omitted when null (goose then falls back to its own secrets
    store / env)."""
    pid = prov["id"]
    model = prov.get("model") or DEFAULT_MODEL
    url = prov.get("base_url")
    key = prov.get("api_key")
    if pid == "ollama":
        model, url = _ollama_model_url(prov)
        env = {"GOOSE_PROVIDER": "ollama", "GOOSE_MODEL": model}
        env["OLLAMA_HOST"] = url[:-3] if url.endswith("/v1") else url
    elif pid == "anthropic":
        env = {"GOOSE_PROVIDER": "anthropic", "GOOSE_MODEL": model}
        if key:
            env["ANTHROPIC_API_KEY"] = key
    elif pid == "openai":
        env = {"GOOSE_PROVIDER": "openai", "GOOSE_MODEL": model}
        if key:
            env["OPENAI_API_KEY"] = key
        if url:
            env["OPENAI_BASE_URL"] = url
    elif pid == "openrouter":
        env = {"GOOSE_PROVIDER": "openrouter", "GOOSE_MODEL": model}
        if key:
            env["OPENROUTER_API_KEY"] = key
    elif pid == "google":
        env = {"GOOSE_PROVIDER": "google", "GOOSE_MODEL": model}
        if key:
            env["GOOGLE_API_KEY"] = key
    else:  # custom -> openai-compatible path
        env = {"GOOSE_PROVIDER": "openai", "GOOSE_MODEL": model}
        if key:
            env["OPENAI_API_KEY"] = key
        if url:
            env["OPENAI_BASE_URL"] = url
    return env


def _load_agents(knowledge_dir):
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
            "DSL. Write complete, full-length HELLFORGE v5 songs — directives (@bpm, "
            "@key, @vol, @seed, ...), human-mode statements (play note/chord, pedal, "
            "rest, art), loops and macros — modeled on the samples/examples in this "
            "repo. Always deliver whole songs, never fragments. Keep every source "
            "valid v5 syntax."
        )
    if name == "music-refiner":
        return (
            "You are HELLFORGE-REFINER, an expert editor for the HELLFORGE (E) DSL. "
            "Edit and optimize existing .ec sources — improve structure, dynamics, "
            "articulation and performance feel, tighten loops, fix non-idiomatic v5. "
            "Apply small, surgical edits and verify against the v5 syntax before "
            "changing anything."
        )
    return None


def _system_prompt(state, persona, knowledge_dir):
    """Build the persona + knowledge text for GOOSE_SYSTEM_PROMPT_FILE_PATH."""
    parts = []
    if persona:
        parts.append(persona)
    names = (("current.md",) if os.path.isfile(os.path.join(knowledge_dir, "current.md"))
             else ("full.md", "samples-index.md"))
    for name in names:
        p = os.path.join(knowledge_dir, name)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                parts.append(f"# {name}\n" + f.read())
    if not parts:
        return None
    path = os.path.join(state, "system-prompt.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n\n".join(parts))
    return path


def launch(project_dir, agent, knowledge_dir, extra_args, stream_out=print):
    exe = _bin()
    if not exe:
        stream_out(f"hellgate: goose not installed — run: {TOOL['install_cmd']}")
        return 1
    state = _state_dir(project_dir)
    root = os.path.join(state, "root")
    os.makedirs(os.path.join(root, "config"), exist_ok=True)

    prov = _provider(project_dir, stream_out)
    env = dict(os.environ)
    env.update(_goose_env(prov))
    env["GOOSE_PATH_ROOT"] = root
    env["XDG_STATE_HOME"] = os.path.join(state, "xdg", "state")
    env["XDG_DATA_HOME"] = os.path.join(state, "xdg", "data")
    env["GOOSE_TELEMETRY_OFF"] = "true"

    match = util.pick_agent(_load_agents(knowledge_dir), agent)
    persona = match["prompt"] if match else _inline_persona(agent)
    sp = _system_prompt(state, persona, knowledge_dir)
    if sp:
        env["GOOSE_SYSTEM_PROMPT_FILE_PATH"] = sp

    cmd = [exe, "session"] + [str(a) for a in (extra_args or [])]
    util.say(f"goose ({prov['id']}/{prov.get('model')}) in {project_dir}", stream_out)
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
