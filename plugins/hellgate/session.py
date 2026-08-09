"""Hellgate session — picker + REPL.

    hellgate> 1        launch OpenCode (fresh chat, project dir = root by default)
    hellgate> $change  switch to another tool
    hellgate> $new     start a fresh chat in the current tool
    hellgate> $dir     show / change the project directory (default: root)
    hellgate> $agent   show / switch agent (Music-Composer | Music-Refiner | default)
    hellgate> $model   show the active model (HELLGATE_MODEL override)
    hellgate> $help    list commands
    hellgate> quit     exit

State (current tool / dir / agent) persists in hellgate-state/session.json
inside the project root. Every launch regenerates the knowledge digest
(current.md: distilled core.md for small-context models, full.md otherwise)
and confines the tool to the chosen project directory.
"""

import json
import os
import sys

from . import tools as T
from . import util
from . import knowledge as K
from . import providers as P

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = util.PROJECT_DIR

HELP = """\
$change            switch to another tool (back to the picker)
$new               start a fresh chat in the current tool
$dir [path]        show or change the project directory (default: project root)
$agent [name]      show or switch agent (Music-Composer / Music-Refiner / default)
$provider [name]   show or switch provider (ollama is only one option)
$model [name]      show or set the model for the current provider
$help              this list
quit / exit        leave the session"""


def state_path():
    return os.path.join(PROJECT_DIR, "hellgate-state", "session.json")


def load_state():
    try:
        with open(state_path()) as f:
            return json.load(f)
    except Exception:
        return {"tool": None, "dir": PROJECT_DIR, "agent": None}


def ensure_provider(state, stream_out=print):
    """Resolve the provider for a launch: state > default. Returns the
    provider dict, or None when unavailable (caller aborts)."""
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
    m = state.get("model", {}).get(prov["id"]) or prov["model"]
    if prov["id"] == "ollama" and P.installed_models():
        if m not in P.installed_models():
            fixed = P.ollama_default_model()
            stream_out(f"  model '{m}' is not installed on ollama — using '{fixed}'")
            m = fixed
    prov = dict(prov)
    prov["model"] = m
    stream_out(f"  provider: {prov['name']} ({prov['id']}) — model: {m or '(unset)'}")
    return prov


def save_state(state):
    os.makedirs(os.path.dirname(state_path()), exist_ok=True)
    with open(state_path(), "w") as f:
        json.dump(state, f, indent=2)


def prepare_knowledge(stream_out=print):
    """Write knowledge/current.md: distilled for small-context models,
    full knowledge otherwise. Returns the chosen kind."""
    kind, text = K.pick_for(model_context_tokens())
    path = os.path.join(HELLGATE_DIR, "knowledge", "current.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    if kind == "core":
        stream_out("context-aware knowledge: distilled core.md (small context model)")
    return kind


def model_context_tokens():
    try:
        from plugins.llm import providers as P
        return P.context_window()
    except Exception:
        return 32768


def picker(state, stream_out=print, prompt_input=input):
    """Numbered tool picker. Returns a tool id or None (quit)."""
    while True:
        tools = T.discover()
        stream_out("")
        stream_out("HELLFORGE hellgate — pick an agent TUI:")
        for i, t in enumerate(tools, 1):
            mark = "ok" if t["installed"] else "missing"
            note = f"  ({t['notes'][:60]})" if (t["notes"] and not t["installed"]) else ""
            stream_out(f"  {i}. {t['name']:<10} [{mark}]{note}")
        stream_out(f"  q. quit")
        prov = P.by_id(state.get("provider") or "") or P.resolve_default()
        stream_out(f"  current: {state.get('tool') or 'none'} | dir: {state.get('dir') or PROJECT_DIR}"
                   f" | agent: {state.get('agent') or 'default'}"
                   f" | provider: {prov['name']}")
        try:
            raw = prompt_input("hellgate> ").strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if raw.lower() in ("q", "quit", "exit"):
            return None
        if raw.isdigit():
            i = int(raw)
            if 1 <= i <= len(tools):
                return tools[i - 1]["id"]
        stream_out("  pick a number or q.")


def run_tool(tid, state, stream_out=print):
    """Launch one tool, confining it to state['dir']. Returns exit code."""
    tool = T.by_id(tid)
    if tool is None:
        stream_out(f"  unknown tool: {tid}")
        return 1
    if not tool["installed"]:
        stream_out(f"  {tool['name']} is not installed — run: {tool.get('install_cmd') or 'see docs'}")
        return 1
    prepare_knowledge(stream_out)
    provider = ensure_provider(state, stream_out)
    if provider is None:
        return 1
    P.write_provider_json(state["dir"], provider)
    agent = state.get("agent")
    if agent:
        stream_out(f"  agent: {agent}")
    stream_out(f"  launching {tool['name']} in {state['dir']} — exit the tool to return here.")
    stream_out("")
    try:
        code = tool["launch"](state["dir"], agent, os.path.join(HELLGATE_DIR, "knowledge"),
                              [], stream_out)
    except KeyboardInterrupt:
        code = 130
    except Exception as e:
        stream_out(f"  launch error: {e}")
        code = 1
    stream_out("")
    stream_out(f"  [{tool['name']} exited with code {code}]")
    return code


def run(api, tool_name=None):
    """Entry: run.py hellgate [tool]."""
    state = load_state()
    stream_out = print
    input_fn = input

    if tool_name:
        tid = tool_name.lower()
        if tid not in T.TOOL_IDS:
            stream_out(f"  unknown tool: {tid} — one of {', '.join(T.TOOL_IDS)}")
            return 1
        state["tool"] = tid
        save_state(state)
        return run_tool(tid, state, stream_out)

    # Always ask on open — the picker IS the launcher (per spec). $change
    # switches later, in the session REPL.
    tid = picker(state, stream_out, input_fn)
    if tid is None:
        return 0
    state["tool"] = tid
    save_state(state)

    while True:
        run_tool(state["tool"], state, stream_out)
        # Session REPL — seamless $change / $new / $dir / $agent.
        try:
            raw = input_fn("hellgate> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            continue  # Enter: relaunch the same tool (fresh chat)
        low = raw.lower()
        if low in ("quit", "exit", "q"):
            state["tool"] = None
            save_state(state)
            return 0
        if low in ("$help", "help"):
            stream_out(HELP)
            continue
        if low in ("$change", "change"):
            tid = picker(state, stream_out, input_fn)
            if tid is None:
                return 0
            state["tool"] = tid
            save_state(state)
            continue
        if low in ("$new", "new"):
            continue  # relaunch = fresh chat in the same tool
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
                           "tools stay focused on their project dir, but knowledge "
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
            stream_out(f"  provider set: {prov['name']} ({prov['id']})"
                       + (f" — model: {state.get('model', {}).get(pid) or prov['model'] or '(unset)'}"))
            continue
        if low.startswith("$model") or low.startswith("model "):
            parts = low.split(maxsplit=1)
            pid = state.get("provider") or P.resolve_default()["id"]
            prov = P.by_id(pid)
            if len(parts) < 2:
                m = state.get("model", {}).get(pid) or prov["model"]
                stream_out(f"  provider {pid}: model = {m or '(unset)'}  "
                           f"($model <name> to set)")
                continue
            state.setdefault("model", {})[pid] = parts[1]
            save_state(state)
            stream_out(f"  provider {pid}: model set to {parts[1]}")
            continue
        stream_out("  try: $help | $change | $new | $dir [path] | $agent [name] | quit")


if __name__ == "__main__":
    sys.exit(run(None))
