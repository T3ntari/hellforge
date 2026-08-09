"""HellGate session — boots and launches OpenCode directly.

    run.py hellgate

Flow per launch:
  wrapper warning (every time)
  → first-run onboarding on a NEW machine (specs-based, even with history)
  → provider/model resolution (ollama asks for a model via the select list)
  → HellCode welcome page + loading screen (real init, x/1024)
  → OpenCode TUI, focused inside the project dir

After OpenCode exits: Enter relaunches, $provider / $model / $agent / $dir
manage the session, q quits.
"""

import json
import os
import sys

from . import boot
from . import knowledge as K
from . import providers as P
from . import util
from . import welcome
from .tools import opencode as OC

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = util.PROJECT_DIR

HELP = """\
Enter / $new      relaunch OpenCode (fresh chat)
$agent [name]     show or switch agent (Music-Composer / Music-Refiner / default)
$provider [name]  show or switch provider (ollama is one option — and asks
                  for a model)
$model [name]     show or set the model for the current provider
$dir [path]       show or change the project directory (default: project root)
$help             this list
quit / exit / q   leave the session"""


def state_path():
    return os.path.join(PROJECT_DIR, "hellgate-state", "session.json")


def load_state():
    try:
        with open(state_path()) as f:
            return json.load(f)
    except Exception:
        return {"dir": PROJECT_DIR, "agent": None}


def save_state(state):
    os.makedirs(os.path.dirname(state_path()), exist_ok=True)
    with open(state_path(), "w") as f:
        json.dump(state, f, indent=2)


def ensure_provider(state, stream_out=print, input_fn=input):
    """Resolve the provider for a launch: state > default. When ollama is
    the provider without an explicitly chosen model, ALWAYS ask via the
    select list. Returns the provider dict or None (abort)."""
    pid = state.get("provider")
    prov = P.by_id(pid) if pid else None
    if prov is None:
        prov = P.resolve_default()
        if prov["id"] == "ollama" and not P.available("ollama"):
            stream_out("  no provider configured and Ollama is not reachable — "
                       "set one with $provider (or start ollama serve)")
            return None
    if not P.available(prov["id"]):
        stream_out(f"  provider '{prov['id']}' not configured — "
                   "$provider to pick another (ollama is one option)")
        return None
    explicit = state.get("model", {}).get(prov["id"])
    m = explicit or prov["model"]
    if prov["id"] == "ollama":
        if not explicit:
            select_ollama_model(state, stream_out, input_fn)
            explicit = state.get("model", {}).get("ollama")
            m = explicit or m
        if P.installed_models() and m not in P.installed_models():
            fixed = P.ollama_default_model()
            stream_out(f"  model '{m}' is not installed on ollama — using '{fixed}'")
            m = fixed
    prov = dict(prov)
    prov["model"] = m
    stream_out(f"  provider: {prov['name']} ({prov['id']}) — model: {m or '(unset)'}")
    return prov


def select_ollama_model(state, stream_out=print, input_fn=input):
    """Interactive select list of installed ollama models. Persists the pick."""
    models = P.installed_models()
    if not models:
        stream_out("  ollama unreachable — no models to list (start `ollama serve`)")
        return False
    stream_out("  ollama models on this machine:")
    for i, m in enumerate(models, 1):
        stream_out(f"    {i}. {m}")
    stream_out("  0 / Enter = keep current default")
    try:
        raw = input_fn("  pick model> ").strip()
    except (EOFError, KeyboardInterrupt):
        return False
    if raw.isdigit():
        i = int(raw)
        if 1 <= i <= len(models):
            state.setdefault("model", {})["ollama"] = models[i - 1]
            save_state(state)
            stream_out(f"  ollama model set: {models[i - 1]}")
            return True
    stream_out("  keeping current default")
    return False


def prepare_knowledge(stream_out=print):
    """Write knowledge/current.md: distilled for small-context models,
    full knowledge otherwise."""
    kind, text = K.pick_for(model_context_tokens())
    path = os.path.join(HELLGATE_DIR, "knowledge", "current.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if kind == "core":
        stream_out("context-aware knowledge: distilled core.md (small context model)")
    return kind


def model_context_tokens():
    try:
        from plugins.llm import providers as Pmod
        return Pmod.context_window()
    except Exception:
        return 32768


def launch_opencode(state, stream_out=print, input_fn=input):
    """Provider + knowledge + config, then the OpenCode TUI."""
    provider = ensure_provider(state, stream_out, input_fn)
    if provider is None:
        return 1
    P.write_provider_json(state["dir"], provider)
    prepare_knowledge(stream_out)
    agent = state.get("agent")
    if agent:
        stream_out(f"  agent: {agent}")
    stream_out(f"  launching OpenCode in {state['dir']} — exit it to return here.")
    stream_out("")
    try:
        code = OC.launch(state["dir"], agent,
                         os.path.join(HELLGATE_DIR, "knowledge"), [], stream_out)
    except KeyboardInterrupt:
        code = 130
    except Exception as e:
        stream_out(f"  launch error: {e}")
        code = 1
    stream_out("")
    stream_out(f"  [OpenCode exited with code {code}]")
    return code


def run(api, tool_name=None):
    """Entry: run.py hellgate."""
    from . import HELLGATE_VERSION
    state = load_state()
    stream_out = print
    input_fn = input

    if tool_name:
        stream_out(f"  hellgate is OpenCode-only now — launching OpenCode"
                   f" (ignoring '{tool_name}')")

    while True:
        # 1. wrapper warning — every single launch.
        welcome.show_warning(stream_out)
        # 2. first-run onboarding on a NEW machine (specs-based).
        if welcome.needs_onboarding():
            if not welcome.onboarding(stream_out, input_fn):
                return 0
        # 3. provider/model resolution (ollama asks for a model).
        provider = ensure_provider(state, stream_out, input_fn)
        if provider is None:
            return 1
        P.write_provider_json(state["dir"], provider)
        # 4. welcome page + loading screen (real init, x/1024).
        boot.run_boot(PROJECT_DIR, HELLGATE_VERSION, stream_out)
        # 5. OpenCode, directly.
        launch_opencode(state, stream_out, input_fn)

        # After OpenCode exits.
        try:
            raw = input_fn("hellgate> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue  # relaunch
        low = raw.lower()
        if low in ("quit", "exit", "q"):
            return 0
        if low in ("$help", "help"):
            stream_out(HELP)
            continue
        if low in ("$new", "new"):
            continue
        if low.startswith("$dir") or low.startswith("dir "):
            parts = low.split(maxsplit=1)
            if len(parts) < 2:
                stream_out(f"  project dir: {state['dir']}")
                stream_out("  default is the HELLFORGE root — set one with: $dir <path>")
                continue
            d = os.path.abspath(os.path.expanduser(parts[1]))
            if not os.path.isdir(d):
                stream_out(f"  not a directory: {d}")
                continue
            if not util.confine(d, PROJECT_DIR):
                stream_out(f"  warning: {d} is OUTSIDE the HELLFORGE root — "
                           "OpenCode stays focused on its project dir, but knowledge "
                           "still targets HELLFORGE.")
            state["dir"] = d
            save_state(state)
            stream_out(f"  project dir set: {d}")
            continue
        if low.startswith("$agent") or low.startswith("agent "):
            parts = low.split(maxsplit=1)
            if len(parts) < 2:
                stream_out(f"  agent: {state.get('agent') or 'default'}")
                stream_out("  options: Music-Composer, Music-Refiner, default")
                continue
            name = parts[1]
            if name.lower() in ("default", "none", "off"):
                state["agent"] = None
            else:
                agents = K.agent_names()
                if name.lower() not in [a.lower() for a in agents]:
                    stream_out(f"  unknown agent: {name} — options: {', '.join(agents)}")
                    continue
                state["agent"] = next(a for a in agents if a.lower() == name.lower())
            save_state(state)
            stream_out(f"  agent set: {state.get('agent') or 'default'}")
            continue
        if low.startswith("$provider") or low.startswith("provider "):
            parts = low.split(maxsplit=1)
            if len(parts) < 2:
                prov = P.by_id(state.get("provider") or "") or P.resolve_default()
                stream_out(f"  provider: {prov['name']} ({prov['id']}) — model: "
                           f"{prov.get('model') or '(unset)'}")
                for p, ok in P.available():
                    mark = "ok" if ok else "key missing"
                    stream_out(f"    {p['id']:<11} {p['name']:<28} [{mark}]")
                stream_out("  set one with: $provider <id>  (ollama is just one option)")
                continue
            pid = parts[1].lower()
            if P.by_id(pid) is None:
                stream_out(f"  unknown provider: {pid} — options: "
                           f"{', '.join(p['id'] for p in P.PROVIDERS)}")
                continue
            state["provider"] = pid
            state.setdefault("model", {})
            save_state(state)
            prov = P.by_id(pid)
            stream_out(f"  provider set: {prov['name']} ({prov['id']})")
            if pid == "ollama":
                select_ollama_model(state, stream_out, input_fn)
            continue
        if low.startswith("$model") or low.startswith("model "):
            parts = low.split(maxsplit=1)
            pid = state.get("provider") or P.resolve_default()["id"]
            prov = P.by_id(pid)
            if len(parts) < 2:
                if pid == "ollama" and P.installed_models():
                    select_ollama_model(state, stream_out, input_fn)
                else:
                    m = state.get("model", {}).get(pid) or prov["model"]
                    stream_out(f"  provider {pid}: model = {m or '(unset)'}  "
                               f"($model <name> to set)")
                continue
            state.setdefault("model", {})[pid] = parts[1]
            save_state(state)
            stream_out(f"  provider {pid}: model set to {parts[1]}")
            continue
        stream_out("  try: $help | $new | $dir [path] | $agent [name] | $provider [name] | quit")


if __name__ == "__main__":
    sys.exit(run(None))
