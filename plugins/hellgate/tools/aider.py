"""hellgate tool: Aider (aider-chat).

Runs aider focused inside the project root. All launch-time config is
generated under <project>/hellgate-state/aider/ and passed with --config
(aider then stops searching for ~/.aider.conf.yml and project configs).
Aider's session files (.aider.chat.history.md etc.) are written into the
cwd — the project root — which is inside the confinement boundary.

Verified against aider 0.86.2 (this version has NO --system-prompt flag):
  - persona is injected via --model-settings-file with `system_prompt_prefix`
    (verified with --show-prompts)
  - knowledge is fed with --read full.md --read samples-index.md
  - the local model is used as `ollama_chat/<model>` with OLLAMA_API_BASE
    and --openai-api-base pointed at the ollama server (round-trip verified:
    model answered PONG)
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
    "id": "aider",
    "name": "Aider",
    "license": "Apache-2.0",
    "install_cmd": "python3.11 -m venv hellgate-state/.venvs/aider && "
                   "hellgate-state/.venvs/aider/bin/pip install aider-chat",
    "confined": True,
    "notes": "Installed into hellgate-state/.venvs/aider (aider-chat needs "
             "Python 3.11, not 3.14). Config via --config; persona via "
             "--model-settings-file system_prompt_prefix (0.86.x removed "
             "--system-prompt).",
}


def _root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))


def _venv_aider(project_dir):
    p = os.path.join(project_dir, "hellgate-state", ".venvs", "aider", "bin", "aider")
    return p if os.path.isfile(p) else None


def _bin(project_dir):
    return (_venv_aider(project_dir) or _venv_aider(_root())
            or shutil.which("aider"))


def _root():
    return os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))


def detect():
    if shutil.which("aider"):
        return True
    p = os.path.join(_root(), "hellgate-state", ".venvs", "aider", "bin", "aider")
    return os.path.isfile(p)


def _state_dir(project_dir):
    return os.path.join(project_dir, "hellgate-state", "aider")


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


def launch(project_dir, agent, knowledge_dir, extra_args, stream_out=print):
    exe = _bin(project_dir)
    if not exe:
        stream_out(f"hellgate: aider not installed — run: {TOOL['install_cmd']}")
        return 1
    state = _state_dir(project_dir)
    os.makedirs(state, exist_ok=True)

    conf_path = os.path.join(state, "aider.conf.yml")
    with open(conf_path, "w", encoding="utf-8") as f:
        f.write("no-auto-commits: true\n")

    cmd = [exe, "--config", conf_path, "--model", "ollama_chat/" + MODEL,
           "--openai-api-base", OLLAMA_URL]

    persona = None
    match = util.pick_agent(_load_agents(knowledge_dir), agent)
    persona = match["prompt"] if match else _inline_persona(agent)
    if persona:
        ms_path = os.path.join(state, "model-settings.yml")
        with open(ms_path, "w", encoding="utf-8") as f:
            f.write("- name: ollama_chat/%s\n" % MODEL)
            f.write("  edit_format: diff\n")
            f.write("  system_prompt_prefix: %s\n"
                    % persona.replace("\n", "\n    ").rstrip())
        cmd += ["--model-settings-file", ms_path]

    names = (("current.md",) if os.path.isfile(os.path.join(knowledge_dir, "current.md"))
             else ("full.md", "samples-index.md"))
    for name in names:
        p = os.path.join(knowledge_dir, name)
        if os.path.isfile(p):
            cmd += ["--read", p]

    cmd += [str(a) for a in (extra_args or [])]

    env = dict(os.environ)
    env["OLLAMA_API_BASE"] = OLLAMA_URL[:-3] if OLLAMA_URL.endswith("/v1") else OLLAMA_URL

    util.say(f"aider (ollama_chat/{MODEL}) in {project_dir}", stream_out)
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
