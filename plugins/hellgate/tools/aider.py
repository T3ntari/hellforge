"""hellgate tool: Aider (aider-chat).

Runs aider focused inside the project root. All launch-time config is
generated under <project>/hellgate-state/aider/ and passed with --config
(aider then stops searching for ~/.aider.conf.yml and project configs).
Aider's session files (.aider.chat.history.md etc.) are written into the
cwd — the project root — which is inside the confinement boundary.

The active provider is read from <project>/hellgate-state/provider.json
(written by the session before every launch); each provider id maps to its
own model prefix / env key (see _aider_cfg). When provider.json is absent
(older setups) it falls back to the ollama provider and streams a note
about it.

Verified against aider 0.86.2 (this version has NO --system-prompt flag):
  - persona is injected via --model-settings-file with `system_prompt_prefix`
    (verified with --show-prompts)
  - knowledge is fed with --read full.md --read samples-index.md
  - the ollama model is used as `ollama_chat/<model>` with OLLAMA_API_BASE
    and --openai-api-base pointed at the ollama server; the other provider
    ids use their native model prefixes (anthropic/, openai/, openrouter/,
    gemini/) which aider validates at startup (a bad prefix aborts with a
    provider-parse error before any API call)
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
    "id": "aider",
    "name": "Aider",
    "license": "Apache-2.0",
    "install_cmd": "python3.11 -m venv hellgate-state/.venvs/aider && "
                   "hellgate-state/.venvs/aider/bin/pip install aider-chat",
    "confined": True,
    "notes": "Installed into hellgate-state/.venvs/aider (aider-chat needs "
             "Python 3.11, not 3.14). Config via --config; provider/model "
             "from hellgate-state/provider.json; persona via "
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


def detect():
    if shutil.which("aider"):
        return True
    p = os.path.join(_root(), "hellgate-state", ".venvs", "aider", "bin", "aider")
    return os.path.isfile(p)


def _state_dir(project_dir):
    return os.path.join(project_dir, "hellgate-state", "aider")


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


def _aider_cfg(prov):
    """provider.json -> (model string, extra launch args, extra env).

    api_key is omitted when null (aider then reads its own env)."""
    pid = prov["id"]
    model = prov.get("model") or DEFAULT_MODEL
    url = prov.get("base_url")
    key = prov.get("api_key")
    args = []
    env = {}
    if pid == "ollama":
        model, url = _ollama_model_url(prov)
        args = ["--model", "ollama_chat/" + model, "--openai-api-base", url]
        env["OLLAMA_API_BASE"] = url[:-3] if url.endswith("/v1") else url
    elif pid == "anthropic":
        args = ["--model", "anthropic/" + model]
        if key:
            env["ANTHROPIC_API_KEY"] = key
    elif pid == "openai":
        args = ["--model", "openai/" + model]
        if url:
            args += ["--openai-api-base", url]
        if key:
            env["OPENAI_API_KEY"] = key
    elif pid == "openrouter":
        args = ["--model", "openrouter/" + model]
        if key:
            env["OPENROUTER_API_KEY"] = key
    elif pid == "google":
        args = ["--model", "gemini/" + model]
        if key:
            env["GEMINI_API_KEY"] = key
    elif pid == "custom":
        args = ["--model", "openai/" + model]
        if url:
            args += ["--openai-api-base", url]
        if key:
            env["OPENAI_API_KEY"] = key
    model_str = args[args.index("--model") + 1]
    return model_str, args, env


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


def _ensure_gitignore(project_dir):
    gi = os.path.join(project_dir, ".gitignore")
    try:
        with open(gi) as f:
            cur = f.read()
    except OSError:
        cur = ""
    if ".aider*" not in cur:
        with open(gi, "a") as f:
            f.write("\n# hellgate (aider)\n.aider*\n")
    return gi


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

    prov = _provider(project_dir, stream_out)
    model_str, args, extra_env = _aider_cfg(prov)
    cmd = [exe, "--config", conf_path] + args

    persona = None
    match = util.pick_agent(_load_agents(knowledge_dir), agent)
    persona = match["prompt"] if match else _inline_persona(agent)
    _ensure_gitignore(project_dir)
    cmd += ["--no-gitignore", "--no-show-model-warnings", "--no-auto-commits"]
    if persona:
        ms_path = os.path.join(state, "model-settings.yml")
        import json as _json
        with open(ms_path, "w", encoding="utf-8") as f:
            f.write("- name: %s\n" % model_str)
            f.write("  edit_format: diff\n")
            # json.dumps → a YAML-safe double-quoted scalar (persona contains
            # '**bold**' etc. that YAML would read as aliases otherwise).
            f.write("  system_prompt_prefix: %s\n" % _json.dumps(persona))
        cmd += ["--model-settings-file", ms_path]

    names = (("current.md",) if os.path.isfile(os.path.join(knowledge_dir, "current.md"))
             else ("full.md", "samples-index.md"))
    for name in names:
        p = os.path.join(knowledge_dir, name)
        if os.path.isfile(p):
            cmd += ["--read", p]

    cmd += [str(a) for a in (extra_args or [])]

    env = dict(os.environ)
    env.update(extra_env)

    util.say(f"aider ({model_str}) in {project_dir}", stream_out)
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
