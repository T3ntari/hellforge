"""Stdio bridge for the TypeScript TUI. JSON-lines protocol:
- TS → PY: {"type":"submit","line"} | {"type":"answer","key","value"} | {"type":"quit"}
- PY → TS: system/chunk/feed/thinking/box/boxline/ask/status/mode/done/error

The TS side spawns `python run.py ai bridge`; this process runs the agent
brain (two-mode router, streaming, plans) and streams events back."""

import json
import os
import sys
import threading

from . import agent as llm_agent
from . import providers
from . import indexer
import plugins.llm as llm  # _classify_mode, _reproduce, _build_context


class StdioBridge:
    def __init__(self):
        self._lock = threading.Lock()
        self._pending = {}  # key -> answer
        self._out = sys.stdout

    def _emit(self, obj):
        with self._lock:
            self._out.write(json.dumps(obj) + "\n")
            self._out.flush()

    def system(self, text):
        self._emit({"type": "system", "text": text})

    def chunk(self, text):
        self._emit({"type": "chunk", "text": text})

    def feed(self, text, color=None):
        self._emit({"type": "feed", "text": text, "color": color})

    def thinking(self, on):
        self._emit({"type": "thinking", "on": bool(on)})

    def box_open(self, title):
        self._emit({"type": "box", "open": True, "title": title})

    def box_line(self, text):
        self._emit({"type": "boxline", "text": text})

    def box_close(self, summary=""):
        self._emit({"type": "box", "open": False, "title": summary})

    def status(self, text):
        self._emit({"type": "status", "text": text})

    def mode(self, mode):
        self._emit({"type": "mode", "text": mode})

    def done(self):
        self._emit({"type": "done"})

    def ask(self, question, detail="", choices=("y", "n", "e")):
        key = str(len(self._pending) + 1)
        with self._lock:
            self._pending[key] = None
        self._emit({"type": "ask", "key": key, "question": question,
                    "detail": detail, "choices": list(choices)})
        while True:
            with self._lock:
                ans = self._pending.get(key)
            if ans is not None:
                with self._lock:
                    self._pending.pop(key, None)
                return ans
            import time
            time.sleep(0.05)

    def answer(self, key, value):
        with self._lock:
            if key in self._pending:
                self._pending[key] = value

    def quit(self):
        self._emit({"type": "done"})


def run(api, state):
    """Bridge main loop. Reads JSON lines from stdin."""
    bridge = StdioBridge()
    history = {"chat": [], "agent": [], "_agent_done": False}
    bridge.system(f"HELL'S CODE v0.1.13 • {state.get('provider')} / "
                  f"{state.get('model') or '?'} • chat mode")
    bridge.mode("chat")
    print("[bridge ready]", file=sys.stderr, flush=True)
    # Binary line reads: immune to pipe buffering quirks under node spawn.
    for raw in sys.stdin.buffer:
        raw = raw.decode("utf-8", errors="replace").strip()
        if not raw:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue
        mtype = msg.get("type")
        if mtype == "quit":
            bridge.done()
            break
        if mtype == "answer":
            bridge.answer(msg.get("key", ""), msg.get("value"))
            continue
        if mtype == "submit":
            _handle(api, state, bridge, history, msg.get("line", ""))
    return 0


def _run_suite_and_report(bridge, project_dir, history):
    """Run the project test suite and stream a summary — the engine-level
    answer to 'check bugs in the codebase' when the model won't act."""
    try:
        from . import tests_runner as tr
    except ImportError:
        return
    bridge.feed("running the test suite...", "accent2")
    bridge.box_open("tests")
    def _on_line(ln):
        bridge.box_line(ln)
    results = tr.run_tests(project_dir)
    bridge.box_close("done")
    summary = tr.summarize(results)
    for line in summary.splitlines()[:12]:
        bridge.feed(line, "ok" if "✓" in line or "passed" in line else "dim")
    failed = sum(1 for r in results if not r.get("ok"))
    bridge.feed("✓ all green" if failed == 0 else
                f"✗ {failed} file(s) failing — see above", "ok" if failed == 0 else "err")
    history["_agent_done"] = True
    history["agent"] = []


def _handle(api, state, bridge, history, line):
    line = llm_agent.strip_ansi(line).strip()
    if not line:
        return
    mode = llm._classify_mode(line)
    hist = history.setdefault(mode, [])
    if mode == "agent" and history.get("_agent_done"):
        hist = []
        history["agent"] = hist
        history["_agent_done"] = False
    bridge.mode(mode)
    if mode == "chat":
        idx = indexer.load_index(api.project_dir) or indexer.build_index(api.project_dir)
        system = (llm_agent.CHAT_PROMPT
                  + "\n\nThis conversation happens inside a real project. "
                    "Names like 'eshell', 'run.py', 'ep.py', 'player.py', "
                    "'plugins/llm' refer to THIS project's files (see the index). "
                    "Never answer with Emacs/other tools. For edits or agentic "
                    "tasks, the user will prefix /fix."
                  + "\n\nProject index:\n"
                  + indexer.index_to_text(idx, max_files=40)
                  + "\n\nRelevant file content for this question:\n"
                  + llm._build_context(api.project_dir, line, max_lines=120, budget=8000))
        messages = [{"role": "system", "content": system}]
        messages.extend(hist[-10:])
        messages.append({"role": "user", "content": line})
    else:
        project_dir = api.project_dir
        repro = llm._reproduce(project_dir, line, timeout=20)
        idx = indexer.load_index(project_dir) or indexer.build_index(project_dir)
        context = (f"Project context:\n{llm._build_context(project_dir, line)}\n\n"
                   f"{indexer.index_to_text(idx, max_files=20)}"
                   + (f"\n\n{repro}" if repro else ""))
        messages = [{"role": "system", "content":
            llm_agent.AGENT_PROMPT + "\n\n"
            + llm_agent.agent_docs_context(project_dir, cap=14000)}]
        if context:
            messages.append({"role": "user", "content": context})
        messages.append({"role": "user", "content": line})
    bridge.thinking(True)
    provider = state.get("provider") or "custom"
    base = state.get("base_url") or providers.PROVIDERS.get(provider, {}).get("base_url", "")
    model = state.get("model")
    if provider == "ollama":
        base = providers.OLLAMA_HEAD + "/v1"
        if not model:
            model = "llama3.2"
    # Agent mode: BUFFER the reply — raw JSON plans must never stream into
    # the chat feed. Chat mode keeps live streaming.
    def _on_chunk(t):
        if mode == "chat":
            bridge.chunk(t)
        else:
            _buf.append(t)

    _buf = []
    try:
        text, err, thinking = providers.stream_chat(
            provider, base, state.get("api_key"), model, messages,
            _on_chunk, timeout=600 if provider == "ollama" else 300)
    except Exception as e:
        text, err = None, str(e)
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
        return  # the reply already streamed as chunk events — no duplicate feed
    plan = llm_agent.parse_plan(text)
    bug_intent = any(k in line.lower() for k in ("bug", "check", "test", "debug", "verify"))
    if plan is not None and plan.get("done"):
        # A 'done' shrug is not enough for bug-check requests — the engine
        # still verifies the codebase and reports.
        if bug_intent:
            _run_suite_and_report(bridge, api.project_dir, history)
            if plan.get("summary"):
                bridge.feed(f"model note: {plan['summary']}", "dim")
        else:
            bridge.feed(f"done: {plan.get('summary', '')}", "ok")
            history["_agent_done"] = True
            history["agent"] = []
        return
    if plan is None or not (plan.get("files") or plan.get("commands")
                            or plan.get("tests") or plan.get("todo")
                            or plan.get("search") or plan.get("memory")):
        # Not a plan → show the buffered text as a normal reply (agent mode
        # buffered it, so it hasn't been displayed yet).
        if text:
            bridge.feed(text, "text")
        # Model didn't act (weak model, generic reply). For bug-check /
        # verify intents, the ENGINE runs the suite regardless — real value
        # even when the model just shrugs.
        if bug_intent:
            _run_suite_and_report(bridge, api.project_dir, history)
        return
    bridge.feed(f"plan: {plan.get('summary', 'no summary')}", "accent2")
    cmds = plan.get("commands") or []
    if cmds:
        from . import exec as safe_exec
        for c in cmds:
            cmd = c.get("cmd") if isinstance(c, dict) else str(c)
            bridge.box_open(f"command: {cmd[:40]}")
            safe_exec.run_command_streaming(cmd, api.project_dir, bridge.box_line)
            bridge.box_close("exit done")
    files = plan.get("files") or []
    for f in files:
        act = f.get("action", "edit")
        bridge.feed(f"  {act:6s} {f.get('path', '?')}", "dim")
    for f in files:
        rel = f.get("path", "")
        act = f.get("action", "edit")
        try:
            target = llm_agent.safe_path(api.project_dir, rel)
        except ValueError as e:
            bridge.feed(f"  skipped {rel}: {e}", "dim")
            continue
        if act == "read":
            continue
        if act == "delete":
            ans = bridge.ask(f"delete {rel}?", "", ("y", "n"))
            if ans == "y" and target.exists():
                target.unlink()
                bridge.feed(f"  deleted {rel}", "ok")
            continue
        if act == "write":
            ans = bridge.ask(f"write {rel}?", "", ("y", "n", "e"))
            if ans == "n":
                bridge.feed(f"  skipped {rel}: declined", "dim")
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(f.get("content", ""), encoding="utf-8")
            bridge.feed(f"  wrote {rel}", "ok")
            continue
        if not target.exists():
            bridge.feed(f"  skipped {rel}: no file", "dim")
            continue
        old_text = target.read_text(encoding="utf-8", errors="replace")
        new_text = old_text
        if f.get("lines") is not None:
            lo = int(f["lines"][0])
            hi = int(f["lines"][1]) if len(f["lines"]) > 1 and f["lines"][1] is not None else lo
            lines = old_text.splitlines()
            if lo < 1 or hi < lo or hi > len(lines):
                bridge.feed(f"  skipped {rel}: lines out of range", "dim")
                continue
            new_text = "\n".join(lines[:lo - 1] + f.get("replace", "").splitlines()
                                + lines[hi:])
        else:
            edits = f.get("edits") or []
            ok = True
            for pair in edits:
                search, replace = pair.get("search", ""), pair.get("replace", "")
                if new_text.count(search) != 1:
                    bridge.feed(f"  skipped {rel}: search not unique", "dim")
                    ok = False
                    break
                new_text = new_text.replace(search, replace)
            if not ok:
                continue
        if new_text != old_text:
            ans = bridge.ask(f"edit {rel}?", "", ("y", "n", "e"))
            if ans == "n":
                bridge.feed(f"  skipped {rel}: declined", "dim")
                continue
            target.write_text(new_text, encoding="utf-8")
            bridge.feed(f"  edited {rel}", "ok")
    bridge.status(f"{provider}/{model or '?'}")
