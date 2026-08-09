"""hellgate tool: OpenHands (openhands-ai, pip CLI).

Runs the OpenHands CLI focused inside the project root. All launch-time
config is generated under <project>/hellgate-state/openhands/ and passed
with --config-file (default would be config.toml in the cwd).

OpenHands 0.9.8 realities (verified against the installed package):
  - the `openhands` console script never awaits main() (a coroutine), so it
    is launched through `python -c "import asyncio; ...asyncio.run(main())"`.
  - the CLI is a line REPL ("How can I help? >>"), not a full TUI, and its
    -t/--task flag is parsed but ignored by main(); there is no
    --system-prompt flag or system_prompt config key — so the agent persona
    cannot be injected. The persona is still passed via -t (harmless, and
    honored by newer versions).
  - Docker IS required: the eventstream runtime calls docker.from_env() at
    startup and dies with DockerException when no docker daemon is reachable
    (verified on this machine: no docker). detect() therefore returns True
    only when the CLI is installed AND a docker runtime is reachable.
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
    "id": "openhands",
    "name": "OpenHands",
    "license": "MIT",
    "install_cmd": "python3.11 -m venv hellgate-state/.venvs/openhands && "
                   "hellgate-state/.venvs/openhands/bin/pip install openhands-ai",
    "confined": False,
    "notes": "Docker required (eventstream runtime calls docker.from_env(); "
             "pip CLI has no docker-free runtime). CLI is a line REPL; "
             "persona/-t task flag is ignored by 0.9.8 (no --system-prompt). "
             "Broken `openhands` bin script → launched via asyncio wrapper.",
}


def _venv_py(project_dir):
    p = os.path.join(project_dir, "hellgate-state", ".venvs", "openhands", "bin", "python")
    return p if os.path.isfile(p) else None


def _root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))


def _cli_installed(project_dir):
    py = _venv_py(project_dir) or _venv_py(_root())
    if not py:
        return False
    r = subprocess.run([py, "-c", "import openhands"], capture_output=True)
    return r.returncode == 0


def _docker_ok():
    if not shutil.which("docker"):
        return False
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=8)
        return r.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))


def detect():
    if not _cli_installed(_root()):
        return False
    return _docker_ok()


def _state_dir(project_dir):
    return os.path.join(project_dir, "hellgate-state", "openhands")


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


def _task_text(state, persona, knowledge_dir):
    """Persona + knowledge preamble for -t (ignored by 0.9.8, future-proof)."""
    parts = ["(HELLFORGE context for this session)"]
    if persona:
        parts.append(persona)
    names = (("current.md",) if os.path.isfile(os.path.join(knowledge_dir, "current.md"))
             else ("full.md", "samples-index.md"))
    for name in names:
        p = os.path.join(knowledge_dir, name)
        if os.path.isfile(p):
            with open(p, "r", encoding="utf-8", errors="replace") as f:
                parts.append(f"# {name}\n" + f.read())
    return "\n\n".join(parts)


WRAP = (
    "import asyncio, sys\n"
    "from openhands.core.cli import main\n"
    "sys.argv = ['openhands'] + sys.argv[1:]\n"
    "sys.exit(asyncio.run(main()))"
)


def launch(project_dir, agent, knowledge_dir, extra_args, stream_out=print):
    py = _venv_py(project_dir) or _venv_py(_root())
    if not py or not _cli_installed(project_dir):
        stream_out(f"hellgate: openhands not installed — run: {TOOL['install_cmd']}")
        return 1
    state = _state_dir(project_dir)
    os.makedirs(state, exist_ok=True)

    conf_path = os.path.join(state, "config.toml")
    with open(conf_path, "w", encoding="utf-8") as f:
        f.write("[llm]\n")
        f.write(f'model = "{MODEL}"\n')
        f.write('api_key = "ollama"\n')
        f.write(f'base_url = "{OLLAMA_URL}"\n')
        f.write("\n[agent]\n")
        f.write('default_agent = "CodeActAgent"\n')

    if not _docker_ok():
        stream_out("hellgate: openhands needs a reachable Docker daemon "
                   "(docker not found or not running) — no docker-free runtime "
                   "exists in openhands-ai 0.9.8; start Docker and retry. "
                   f"Config written to {conf_path}.")
        return 1

    cmd = [py, "-c", WRAP, "--config-file", conf_path, "-d", project_dir]

    match = util.pick_agent(_load_agents(knowledge_dir), agent)
    persona = match["prompt"] if match else _inline_persona(agent)
    task = _task_text(state, persona, knowledge_dir)
    if persona:
        stream_out("hellgate: note: openhands 0.9.8 CLI ignores -t and has no "
                   "system-prompt hook; paste the persona/knowledge at the "
                   "'How can I help?' prompt instead.")
    cmd += ["-t", task]
    cmd += [str(a) for a in (extra_args or [])]

    util.say(f"openhands ({MODEL}) in {project_dir}", stream_out)
    p = subprocess.Popen(cmd, cwd=project_dir)
    try:
        return p.wait()
    except KeyboardInterrupt:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
        return 130
