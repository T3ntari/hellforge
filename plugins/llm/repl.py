"""Claude-Code-style REPL engine for the HELLFORGE copilot.

Standalone front-end: slash commands (/help /clear /status /mode /model
/compact /cost /memory /review /exit /quit), plan/auto/ask permission
modes with prompt badges, readline integration, per-turn status bar and a
/compact command that shrinks long histories via the model.

Decoupled: this module never imports plugins.llm.__init__ directly. The
model request, the plan apply and the per-turn hook are injected as
callbacks; optional feature modules (costs, select, review) are lazy
imports with graceful fallback when a module is not installed yet.

Injected callback contract:
- get_request(messages) -> (text, err)      model call; text may be a JSON plan
- apply_plan_fn(plan, project_dir, confirm_write=True) -> (applied, skipped, msgs)
- on_turn(event) -> dict                    fired after every processed line
"""

import sys
import time
from pathlib import Path

COMPACT_THRESHOLD = 60000   # history chars before /compact starts to make sense
RECENT_CHAR_LIMIT = 10000   # a "recent turn" kept under the compaction summary
MODES = ("plan", "auto", "ask")

SLASH_HELP = {
    "/help": ("", "show this command list"),
    "/clear": ("", "reset the conversation history (system prompt is kept)"),
    "/status": ("", "print the status bar (model / mode / tokens / cost / context)"),
    "/mode": ("plan|auto|ask", "switch permission mode; prompt badge updates"),
    "/model": ("", "open the model picker"),
    "/compact": ("", "summarize history via the model once past the threshold"),
    "/cost": ("", "print the session cost"),
    "/memory": ("", "show AGENTS.md / RULES.md / TODO.md heads"),
    "/review": ("", "run a review of the recent changes"),
    "/exit": ("", "leave the REPL"),
    "/quit": ("", "leave the REPL"),
}


def _interactive():
    """True when the REPL can use input() + readline history."""
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def _try_import(name):
    """Lazy import of a plugin module — None when not installed."""
    try:
        return __import__(f"plugins.llm.{name}", fromlist=["*"])
    except ImportError:
        return None


def _project_instructions(project_dir):
    """Fallback system prompt: capped heads of AGENTS/RULES/TODO."""
    if not project_dir:
        return ""
    root = Path(project_dir)
    parts = []
    for name, cap in (("AGENTS.md", 3000), ("RULES.md", 2000), ("TODO.md", 2000)):
        p = root / name
        if p.exists():
            try:
                parts.append(f"# {name}\n"
                             f"{p.read_text(encoding='utf-8', errors='replace')[:cap]}")
            except Exception:
                pass
    return "\n\n".join(parts)


def _history_chars(history):
    return sum(len(m.get("content") or "") for m in history)


def _history_text(history, per_message=2000):
    """Serialized history for the compaction prompt (capped per message)."""
    return "\n".join(f"<{m.get('role', '?')}> {(m.get('content') or '')[:per_message]}"
                     for m in history)


def _stats(api, state, history):
    """Session stats: tokens/cost from plugins.llm.costs (lazy, zeros when
    absent); context = fraction of the compact threshold used so far."""
    stats = {"tokens": 0, "cost": 0.0}
    costs = _try_import("costs")
    if costs is not None:
        for fn_name in ("session_stats", "stats"):
            fn = getattr(costs, fn_name, None)
            if fn is None:
                continue
            try:
                res = fn(api, state)
                if isinstance(res, dict):
                    stats.update({k: v for k, v in res.items()
                                  if k in ("tokens", "cost", "context")})
                break
            except Exception:
                continue
    chars = _history_chars(history or [])
    stats["chars"] = chars
    stats["context"] = min(1.0, chars / COMPACT_THRESHOLD)
    return stats


def _parse_plan(text):
    try:
        from plugins.llm import agent as llm_agent
        return llm_agent.parse_plan(text)
    except Exception:
        return None


# ── in-memory edit preview (plan mode shows the diff without applying) ──

def _edit_text_preview(old_text, spec):
    """Apply a file edit in memory; None when the edit is invalid.
    Mirrors the agent's line-range and search/replace semantics."""
    old_lines = old_text.splitlines()
    line_edit = spec.get("lines")
    if line_edit is not None:
        try:
            lo = int(line_edit[0])
        except (TypeError, ValueError, IndexError):
            return None
        hi = None
        if len(line_edit) > 1 and line_edit[1] is not None:
            try:
                hi = int(line_edit[1])
            except (TypeError, ValueError):
                return None
        replace = (spec.get("replace") or "").splitlines()
        if hi is None:
            if lo < 1 or lo > len(old_lines) + 1:
                return None
            new_lines = old_lines[:lo - 1] + replace + old_lines[lo - 1:]
        else:
            if lo < 1 or hi < lo or hi > len(old_lines):
                return None
            new_lines = old_lines[:lo - 1] + replace + old_lines[hi:]
        text = "\n".join(new_lines)
        return text + ("\n" if old_text.endswith("\n") else "")
    new_text = old_text
    for pair in spec.get("edits") or []:
        search, replace = pair.get("search", ""), pair.get("replace", "")
        if not search or new_text.count(search) != 1:
            return None
        new_text = new_text.replace(search, replace)
    return new_text


def _preview_plan(plan, project_dir):
    """Plan mode: render what each proposed change would do, apply nothing."""
    from plugins.llm import agent as llm_agent
    from plugins.llm import diffview as dv
    from plugins.llm import ui
    files = plan.get("files") or []
    if not files:
        print(ui.dim("  (no file changes in this plan)"))
        return
    for f in files:
        rel = f.get("path", "")
        action = f.get("action", "edit")
        try:
            target = llm_agent.safe_path(project_dir, rel) if project_dir else None
        except ValueError as e:
            print(ui.error_line(f"  {rel}: {e}"))
            continue
        if target is None:
            print(ui.error_line(f"  {rel}: no project directory for preview"))
            continue
        if action == "write":
            old = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
            dv.print_diff(old, f.get("content", ""), rel)
        elif action == "read":
            if not target.exists():
                print(f"  {dv.dim('read')} {rel}: file does not exist")
                continue
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            start = int(f.get("start", 1) or 1)
            end = int(f.get("end") or 0) or None
            for line in dv.render_read(lines, start, end):
                print(f"  {line}")
        elif action == "delete":
            print(f"  {dv.red(f'DELETE {rel}')} — preview only, nothing deleted")
        elif action == "edit":
            if not target.exists():
                print(f"  {dv.dim('edit')} {rel}: file does not exist")
                continue
            old = target.read_text(encoding="utf-8", errors="replace")
            new = _edit_text_preview(old, f)
            if new is None:
                print(ui.error_line(f"  {rel}: edit cannot be previewed (bad range/search)"))
                continue
            dv.print_diff(old, new, rel)
        else:
            print(ui.warn_line(f"  {rel}: unknown action '{action}'"))


# ── slash command handlers ──

def _delegate(module_name, hint, fn):
    """Run fn against a lazily imported module; graceful fallback."""
    from plugins.llm import ui
    mod = _try_import(module_name)
    if mod is None:
        print(ui.warn_line(hint))
        return
    try:
        fn(mod)
    except Exception as e:
        print(ui.error_line(f"{module_name} failed: {e}"))


def _cmd_help():
    from plugins.llm import ui
    print("  slash commands:")
    for name, (args, desc) in SLASH_HELP.items():
        use = f"{name} {args}".strip()
        pad = " " * max(1, 26 - len(use))
        print(ui.dim(f"  {use}{pad}{desc}"))


def _cmd_clear(history):
    from plugins.llm import ui
    history[:] = history[:1]
    print(ui.result_line("history cleared (system prompt kept)", "ok"))


def _cmd_mode(state, rest):
    from plugins.llm import ui
    if not rest:
        print(ui.result_line(f"mode is {state.get('mode') or 'ask'}", "info"))
        return True
    mode = rest.lower()
    if mode not in MODES:
        print(ui.warn_line(f"unknown mode '{mode}' — expected plan | auto | ask"))
        return True
    state["mode"] = mode
    print(ui.result_line(f"mode → {mode}", "ok"))
    return True


def _cmd_memory(project_dir):
    from plugins.llm import ui
    for name in ("AGENTS.md", "RULES.md", "TODO.md"):
        path = Path(project_dir) / name if project_dir else None
        if path is None or not path.exists():
            print(ui.dim(f"  {name} — not present"))
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"  {name} — {len(lines)} line(s)")
        for ln in lines[:12]:
            print(f"    {ln}")


def _cmd_compact(history, get_request):
    """Summarize long history via the model; keep the summary + recent turns."""
    from plugins.llm import ui
    chars = _history_chars(history)
    if chars <= COMPACT_THRESHOLD:
        print(ui.result_line(
            f"history is {chars} chars — below the {COMPACT_THRESHOLD} compact "
            f"threshold, nothing to do", "info"))
        return
    print(ui.thinking("compacting history via the model..."))
    job = ("Compress the conversation below into one plain-text handoff summary "
           "that keeps: what was done, what still needs verification, and open "
           "questions (concise, ~150 words).\n\n--- history ---\n"
           + _history_text(history))
    text, err = get_request([{"role": "user", "content": job}])
    if err:
        print(ui.error_line(f"compaction failed: {err}"))
        return
    summary = (text or "").strip() or "[empty summary]"
    recent = [m for m in history[-4:]
              if len(m.get("content") or "") <= RECENT_CHAR_LIMIT]
    history[:] = (history[:1]
                  + [{"role": "assistant", "content": f"[compacted summary] {summary}"}]
                  + recent)
    print(ui.result_line(
        f"compacted {chars} chars → summary + {len(recent)} recent message(s)", "ok"))


def _cmd_model(api, state):
    def pick(mod):
        fn = getattr(mod, "pick_model", None) or getattr(mod, "select_model", None)
        if fn is None:
            raise AttributeError("no pick_model()/select_model() found")
        fn(api, state)
    _delegate("select", "model picker not installed — use 'ai model <name>' instead", pick)


def _cmd_cost(api, state, history):
    def walk(mod):
        from plugins.llm import ui
        if hasattr(mod, "session_cost"):
            print(f"  session cost: {mod.session_cost(api, state)}")
        else:
            print(ui.status_bar(state, _stats(api, state, history)))
    _delegate("costs",
              "cost tracking not installed — add plugins/llm/costs.py "
              "(or use /status for the zero fallback)",
              walk)


def _cmd_review(api, state):
    def run(mod):
        fn = getattr(mod, "review", None)
        if fn is None:
            raise AttributeError("no review() found")
        fn(api, state)
    _delegate("review", "review not installed — add plugins/llm/review.py", run)


def _dispatch(api, state, history, cmd, rest, get_request, apply_plan_fn):
    """Run one slash command; return False when the REPL should exit."""
    from plugins.llm import ui
    if cmd == "/help":
        _cmd_help()
    elif cmd == "/clear":
        _cmd_clear(history)
    elif cmd == "/status":
        print(ui.status_bar(state, _stats(api, state, history)))
    elif cmd == "/mode":
        _cmd_mode(state, rest)
    elif cmd == "/model":
        _cmd_model(api, state)
    elif cmd == "/compact":
        _cmd_compact(history, get_request)
    elif cmd == "/cost":
        _cmd_cost(api, state, history)
    elif cmd == "/memory":
        _cmd_memory(getattr(api, "project_dir", None))
    elif cmd == "/review":
        _cmd_review(api, state)
    elif cmd == "/search":
        _cmd_search(api, state, rest)
    elif cmd in ("/exit", "/quit"):
        return False
    else:
        print(ui.warn_line(f"unknown command {cmd} — try /help"))
    return True


# ── turn loop ──

def _apply_plan_step(api, state, history, plan, text, apply_plan_fn):
    """Mode-aware plan handling: plan previews only; auto applies un-prompted."""
    from plugins.llm import agent as llm_agent
    from plugins.llm import ui
    project_dir = getattr(api, "project_dir", None)
    mode = state.get("mode") or "ask"
    print(f"  {ui.chip('plan', 'plan')} {plan.get('summary', 'no summary')}")
    if mode == "plan":
        _preview_plan(plan, project_dir)
        print(ui.warn_line("mode is plan — switch to auto/ask with /mode to apply"))
        history.append({"role": "assistant", "content": text})
        history.append({"role": "user",
                        "content": "[tool result] plan mode: changes previewed, "
                                   "NOT applied (use /mode auto or /mode ask)"})
        return
    history.append({"role": "assistant", "content": text})
    cmd_out = ""
    if plan.get("commands") and project_dir:
        try:
            results, chat_lines = llm_agent.execute_plan_commands(plan, project_dir)
            for line in chat_lines:
                print(f"  {line}")
            cmd_out = "\n".join(f"$ {r.get('cmd')}\n{r.get('output', '')[:800]}"
                                for r in results if not r.get("blocked"))
        except Exception as e:
            print(ui.error_line(f"commands: {e}"))
    try:
        applied, skipped, msgs = apply_plan_fn(
            plan, project_dir, confirm_write=(mode == "ask"))
    except TypeError:
        # positional-only apply callbacks (e.g. lambdas over interactive_apply)
        applied, skipped, msgs = apply_plan_fn(plan, project_dir)
    except Exception as e:
        print(ui.error_line(f"apply failed: {e}"))
        history.append({"role": "user", "content": f"[tool error] {e}"})
        return
    for m in msgs:
        print(m)
    for rel, why in skipped:
        print(f"  {ui.dim('skipped')} {rel}: {why}")
    note = (f"[tool result] applied {applied} change(s); skipped: "
            f"{', '.join(rel for rel, _ in skipped) or 'none'}.")
    if cmd_out:
        note += f" Commands run:\n{cmd_out[:800]}"
    if plan.get("tests"):
        note = note[:-1] + "; tests queued (see /submit or ai test)"
    print(f"  {ui.dim(note)}")
    history.append({"role": "user", "content": note})


def _turn(api, state, history, request, context_builder, get_request, apply_plan_fn):
    """One user turn: think → model call → plan/chat → elapsed + status bar."""
    from plugins.llm import ui
    t0 = time.perf_counter()
    context = context_builder(request)
    content = request if not context else f"{request}\n\nProject context:\n{context}"
    ui.thinking("thinking...")
    history.append({"role": "user", "content": content})
    text, err = get_request(history)
    if err:
        print(f"  {ui.chip('error', 'error')} {err}")
        history.pop()
        return
    plan = _parse_plan(text)
    if plan is not None and (plan.get("files") or plan.get("commands")
                             or plan.get("tests") or plan.get("todo")):
        _apply_plan_step(api, state, history, plan, text, apply_plan_fn)
    elif plan is not None and plan.get("done"):
        print(f"  {ui.chip('done', 'done')} {plan.get('summary', '')}")
        history.append({"role": "assistant", "content": text})
    else:
        print(ui.wrap(text or "", prefix="  agent> "))
        history.append({"role": "assistant", "content": text})
    print(ui.elapsed(time.perf_counter() - t0))
    print(ui.status_bar(state, _stats(api, state, history)))


def run_repl(api, state, get_request, apply_plan_fn, on_turn=None,
             system_prompt=None, context_builder=None):
    """Claude-Code-style REPL loop.

    Prompts with a mode badge, dispatches slash commands, runs one model
    turn per free-form line and prints the status bar after every turn.
    Returns the mode the session ended in (state is mutated in place, so the
    caller can persist it afterwards).
    """
    from plugins.llm import ui

    project_dir = getattr(api, "project_dir", None)
    state["mode"] = state.get("mode") if state.get("mode") in MODES else "ask"
    if context_builder is None:
        context_builder = lambda _request: ""  # noqa: E731
    sys_prompt = system_prompt if system_prompt is not None \
        else _project_instructions(project_dir)
    history = ([{"role": "system", "content": sys_prompt}] if sys_prompt else [])
    if _interactive():  # readline: arrow-key history comes free with input()
        try:
            import readline  # noqa: F401
        except ImportError:
            pass

    def _prompt():
        return f"{ui.mode_badge(state['mode'])} {ui.prompt('you')}"

    def _notify(event):
        if on_turn:
            try:
                on_turn(event)
            except Exception:
                pass

    try:
        while True:
            try:
                if _interactive():
                    line = input(_prompt())
                else:
                    raw = sys.stdin.readline()
                    if not raw:
                        break
                    line = raw.strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not line:
                continue
            if line.strip().lower() in ("quit", "exit"):
                break
            if line.startswith("/"):
                cmd, _, rest = line.partition(" ")
                cont = _dispatch(api, state, history, cmd.lower(), rest.strip(),
                                 get_request, apply_plan_fn)
                _notify({"type": "command", "line": line, "mode": state["mode"]})
                if not cont:
                    break
                continue
            _turn(api, state, history, line, context_builder,
                  get_request, apply_plan_fn)
            _notify({"type": "turn", "line": line, "mode": state["mode"]})
    except KeyboardInterrupt:
        pass
    return state["mode"]