"""hellgate tool: Goose (block/goose, now aaif-goose/goose).

Runs the goose session TUI focused inside the project root. Confinement is
done with GOOSE_PATH_ROOT (verified: config dir, sessions db and logs all
move under it) plus XDG_STATE_HOME/XDG_DATA_HOME for the CLI's leftover
log files, so nothing is written to ~/.config/goose or ~/.local/share/goose.

Provider wiring (verified with goose 1.45.0): goose 1.45 has NO profile
files or GOOSE_PROFILE_DIR — the provider/model/base are configured through
environment variables:
  GOOSE_PROVIDER=ollama  GOOSE_MODEL=<model>  OLLAMA_HOST=<host>
(round-trip verified: `goose run -t ...` answered PONG). GOOSE_TELEMETRY_OFF
skips the first-run "share usage data" prompt, and
GOOSE_SYSTEM_PROMPT_FILE_PATH feeds the agent persona/knowledge into the
session system prompt.
"""

import os
import shutil
import subprocess

from .. import util

MODEL = os.environ.get(
    "HELLGATE_MODEL",
    "hf.co/bartowski/Qwen2.5-Coder-3B-Instruct-Abliterated-GGUF:latest",
)
OLLAMA_URL = os.environ.get("HELLGATE_OLLAMA_URL", "http://127.0.0.1:11434/v1")

TOOL = {
    "id": "goose",
    "name": "Goose",
    "license": "Apache-2.0",
    "install_cmd": "curl -fsSL "
                   "https://github.com/aaif-goose/goose/releases/download/stable/"
                   "download_cli.sh | CONFIGURE=false bash",
    "confined": True,
    "notes": "Confined via GOOSE_PATH_ROOT + XDG_* (goose 1.45 has no "
             "profile dir; provider via GOOSE_PROVIDER/GOOSE_MODEL/OLLAMA_HOST). "
             "Persona via GOOSE_SYSTEM_PROMPT_FILE_PATH.",
}


def _bin():
    return shutil.which("goose")


def detect():
    return bool(_bin())


def _state_dir(project_dir):
    return os.path.join(project_dir, "hellgate-state", "goose")


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

    env = dict(os.environ)
    env["GOOSE_PATH_ROOT"] = root
    env["XDG_STATE_HOME"] = os.path.join(state, "xdg", "state")
    env["XDG_DATA_HOME"] = os.path.join(state, "xdg", "data")
    env["GOOSE_PROVIDER"] = "ollama"
    env["GOOSE_MODEL"] = MODEL
    env["OLLAMA_HOST"] = OLLAMA_URL[:-3] if OLLAMA_URL.endswith("/v1") else OLLAMA_URL
    env["GOOSE_TELEMETRY_OFF"] = "true"

    match = util.pick_agent(_load_agents(knowledge_dir), agent)
    persona = match["prompt"] if match else _inline_persona(agent)
    sp = _system_prompt(state, persona, knowledge_dir)
    if sp:
        env["GOOSE_SYSTEM_PROMPT_FILE_PATH"] = sp

    cmd = [exe, "session"] + [str(a) for a in (extra_args or [])]
    util.say(f"goose (ollama/{MODEL}) in {project_dir}", stream_out)
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
