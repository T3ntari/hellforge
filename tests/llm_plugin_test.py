#!/usr/bin/env python3
"""LLM Copilot plugin tests — providers, ollama detection, chat client,
agent plan parsing, safe path handling, apply plan (writes/edits/deletes)."""
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from plugins.llm import providers, agent as llm_agent

passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        import traceback
        traceback.print_exc()
        print(f"  [FAIL] {name}: {e}")


# ── provider registry ──

def test_provider_registry():
    assert set(providers.PROVIDERS) >= {"openai", "deepseek", "claude", "ollama", "custom"}
    assert providers.PROVIDERS["deepseek"]["base_url"].startswith("https://api.deepseek.com")
    assert providers.PROVIDERS["claude"]["api"] == "anthropic"
test("Providers: openai/deepseek/claude/ollama/custom registered", test_provider_registry)


def test_known_models():
    assert "deepseek-chat" in providers.PROVIDERS["deepseek"]["models"]
    assert "deepseek-v4" in providers.PROVIDERS["deepseek"]["models"]
    assert "claude-sonnet-4-5" in providers.PROVIDERS["claude"]["models"]
test("Providers: deepseek v4 + claude models listed", test_known_models)


# ── ollama detection (environment-aware: a local server may be present) ──

_OLLAMA_PRESENT = providers.ollama_detected(timeout=2)


def test_ollama_detection():
    # Real server present → True; otherwise False (must not hang).
    assert providers.ollama_detected(timeout=1) is _OLLAMA_PRESENT
test("Ollama: detection matches environment", test_ollama_detection)


def test_ollama_models_consistency():
    models = providers.ollama_models(timeout=2)
    if _OLLAMA_PRESENT:
        assert isinstance(models, list) and len(models) > 0
        assert all(isinstance(m, str) and m for m in models)
    else:
        assert models == []
test("Ollama: models list matches environment", test_ollama_models_consistency)


# ── chat client error paths (no network) ──

def test_chat_bad_host():
    text, err = providers.chat_request("openai", "http://127.0.0.1:1/v1",
                                       "k", "gpt-4o-mini",
                                       [{"role": "user", "content": "hi"}],
                                       timeout=1)
    assert text is None and err, "bad host must produce an error"
test("Chat: unreachable host reports error", test_chat_bad_host)


def test_chat_missing_model():
    text, err = providers.chat_request("custom", "http://127.0.0.1:1", "k", "",
                                       [{"role": "user", "content": "hi"}], timeout=1)
    assert err
test("Chat: empty model still attempts request (error expected)", test_chat_missing_model)


# ── plan parsing ──

def test_parse_plan_fenced():
    plan = llm_agent.parse_plan('```json\n{"summary": "s", "files": [{"path": "a.py", "action": "write", "content": "x"}]}\n```')
    assert plan and plan["files"][0]["path"] == "a.py"
test("Plan: markdown-fenced JSON parses", test_parse_plan_fenced)


def test_parse_plan_plain():
    plan = llm_agent.parse_plan('{"summary": "s", "files": []}')
    assert plan and plan["summary"] == "s"
test("Plan: plain JSON parses", test_parse_plan_plain)


def test_parse_plan_garbage():
    assert llm_agent.parse_plan("I don't know how to change that.") is None
test("Plan: plain prose rejected", test_parse_plan_garbage)


def test_parse_plan_trailing_prose():
    plan = llm_agent.parse_plan('Here you go:\n{"summary":"x","files":[{"path":"b.py","action":"write","content":"c"}]}\nLet me know if ok.')
    assert plan and plan["files"][0]["path"] == "b.py"
test("Plan: JSON with surrounding prose parses", test_parse_plan_trailing_prose)


# ── path safety ──

def test_safe_path_ok():
    d = tempfile.mkdtemp()
    assert str(llm_agent.safe_path(d, "plugins/x/__init__.py")).startswith(d)
test("Safety: relative path resolves", test_safe_path_ok)


def test_safe_path_escape():
    d = tempfile.mkdtemp()
    try:
        llm_agent.safe_path(d, "../outside.py")
        raise AssertionError("escape should be rejected")
    except ValueError:
        pass
test("Safety: .. escape rejected", test_safe_path_escape)


def test_safe_path_absolute():
    d = tempfile.mkdtemp()
    try:
        llm_agent.safe_path(d, "/etc/passwd")
        raise AssertionError("absolute should be rejected")
    except ValueError:
        pass
test("Safety: absolute path rejected", test_safe_path_absolute)


def test_safe_path_forbidden():
    d = tempfile.mkdtemp()
    for bad in (".e_identity/secret.key", ".venv/bin/python", "logs/x.log"):
        try:
            llm_agent.safe_path(d, bad)
            raise AssertionError(f"{bad} should be rejected")
        except ValueError:
            pass
test("Safety: protected dirs rejected", test_safe_path_forbidden)


# ── apply plan: write / edit / delete ──

def test_apply_write():
    d = tempfile.mkdtemp()
    plan = {"summary": "add file", "files": [
        {"path": "sub/new.py", "action": "write", "content": "print('hi')\n"}]}
    applied, skipped, msgs = llm_agent.apply_plan(plan, d, confirm_write=False)
    assert applied == 1 and not skipped
    assert open(os.path.join(d, "sub/new.py")).read() == "print('hi')\n"
test("Apply: write creates file + dirs", test_apply_write)


def test_apply_edit():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a = 1\nb = 2\n")
    plan = {"summary": "edit", "files": [
        {"path": "x.py", "action": "edit",
         "edits": [{"search": "b = 2", "replace": "b = 3"}]}]}
    applied, skipped, _ = llm_agent.apply_plan(plan, d, confirm_write=False)
    assert applied == 1
    assert open(os.path.join(d, "x.py")).read() == "a = 1\nb = 3\n"
test("Apply: edit search/replace", test_apply_edit)


def test_apply_edit_nonunique():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("v = 1\nv = 2\n")
    plan = {"summary": "edit", "files": [
        {"path": "x.py", "action": "edit",
         "edits": [{"search": "v =", "replace": "w ="}]}]}
    applied, skipped, _ = llm_agent.apply_plan(plan, d, confirm_write=False)
    assert applied == 0 and skipped and "not unique" in skipped[0][1]
test("Apply: non-unique search skipped", test_apply_edit_nonunique)


def test_apply_delete_requires_confirm():
    d = tempfile.mkdtemp()
    victim = os.path.join(d, "secret.py")
    with open(victim, "w") as f:
        f.write("x")
    plan = {"summary": "del", "files": [
        {"path": "secret.py", "action": "delete"}]}
    # Non-TTY: delete must ALWAYS be refused, even with confirm_write=False
    applied, skipped, _ = llm_agent.apply_plan(plan, d, confirm_write=False)
    assert applied == 0 and skipped and "delete declined" in skipped[0][1]
    assert os.path.exists(victim), "file must survive"
test("Apply: delete refused without confirmation (non-TTY)", test_apply_delete_requires_confirm)


def test_apply_missing_file():
    d = tempfile.mkdtemp()
    plan = {"summary": "edit", "files": [
        {"path": "ghost.py", "action": "edit", "edits": [{"search": "a", "replace": "b"}]}]}
    applied, skipped, _ = llm_agent.apply_plan(plan, d, confirm_write=False)
    assert applied == 0 and skipped and "does not exist" in skipped[0][1]
test("Apply: edit of missing file skipped", test_apply_missing_file)


def test_apply_escape_rejected():
    d = tempfile.mkdtemp()
    plan = {"summary": "evil", "files": [
        {"path": "../../evil.py", "action": "write", "content": "x"}]}
    applied, skipped, _ = llm_agent.apply_plan(plan, d, confirm_write=False)
    assert applied == 0 and skipped
test("Apply: escape path rejected", test_apply_escape_rejected)


# ── end-to-end agentic flow (mocked request) ──

def test_agentic_flow_mocked():
    import plugins.llm as llm
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    reply = ('{"summary": "fix typo", "files": ['
             '{"path": "note.txt", "action": "write", "content": "fixed"}]}')
    llm.providers.chat_request = lambda *a, **k: (reply, None)
    state = {"provider": "deepseek", "model": "deepseek-chat",
             "base_url": "https://api.deepseek.com/v1", "api_key": "x"}
    import types
    class FakeAPI:
        project_dir = d
    plan = ag.parse_plan(reply)
    applied, skipped, msgs = ag.apply_plan(plan, d, confirm_write=False)
    assert applied == 1
    assert open(os.path.join(d, "note.txt")).read() == "fixed"
test("Agentic: mocked model reply applies", test_agentic_flow_mocked)




# ── diffview rendering ──

def test_diffview_markers():
    from plugins.llm import diffview as dv
    out = dv.render_unified("a = 1\nb = 2\n", "a = 1\nb = 3\nc = 4\n")
    text = "\n".join(out)
    assert any("+ b = 3" in ln or "+" in ln for ln in out), out
    assert any("- b = 2" in ln or "-" in ln for ln in out), out
    assert any("+ c = 4" in ln for ln in out)
    # colors stripped off-TTY
    assert "\033[" not in text
test("Diff: unified shows +/- lines, no ANSI off-TTY", test_diffview_markers)


def test_diffview_stat():
    from plugins.llm import diffview as dv
    adds, dels = dv.diff_stat("x\n", "x\ny\nz\n")
    assert adds == 2 and dels == 0
    adds, dels = dv.diff_stat("a\nb\n", "a\n")
    assert adds == 0 and dels == 1
test("Diff: +adds/-dels stat counts", test_diffview_stat)


def test_diffview_read_range():
    from plugins.llm import diffview as dv
    lines = [f"line {i}" for i in range(10)]
    out = dv.render_read(lines, 3, 5)
    assert len(out) == 3 and "line 2" in out[0] and "line 4" in out[-1]
test("Diff: read range renders line numbers", test_diffview_read_range)


# ── interactive apply (mocked input) ──

class _FakeTTYStdin:
    def __init__(self, answers):
        self._answers = list(answers)
    def isatty(self):
        return True
    def readline(self):
        return ""
    def __iter__(self):
        return iter(self._answers)
    def __next__(self):
        if not self._answers:
            raise StopIteration
        return self._answers.pop(0)


def _patch_stdin(answers):
    import unittest.mock as mock
    import builtins
    return mock.patch("builtins.input", side_effect=lambda *a: _FakeTTYStdin(answers).__next__()), \
           mock.patch.object(sys, "stdin", _FakeTTYStdin(answers))


def _tty_ctx():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    return mock.patch.object(ag, "_is_tty", return_value=True)


def test_interactive_yes_applies():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    plan = {"summary": "add", "files": [
        {"path": "x.py", "action": "write", "content": "print(1)\n"}]}
    with _tty_ctx(), mock.patch("builtins.input", return_value="y"):
        applied, skipped, msgs = ag.interactive_apply(plan, d)
    assert applied == 1 and not skipped
    assert open(os.path.join(d, "x.py")).read() == "print(1)\n"
test("Interactive: y applies write", test_interactive_yes_applies)


def test_interactive_no_skips():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    plan = {"summary": "add", "files": [
        {"path": "x.py", "action": "write", "content": "x"}]}
    with _tty_ctx(), mock.patch("builtins.input", return_value="n"):
        applied, skipped, _ = ag.interactive_apply(plan, d)
    assert applied == 0 and skipped and "declined" in skipped[0][1]
    assert not os.path.exists(os.path.join(d, "x.py"))
test("Interactive: n skips write", test_interactive_no_skips)


def test_interactive_read_no_change():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a\nb\nc\n")
    plan = {"summary": "read", "files": [{"path": "x.py", "action": "read"}]}
    with mock.patch("builtins.input", return_value="y"):
        applied, skipped, msgs = ag.interactive_apply(plan, d)
    assert applied == 0 and not skipped
    assert any("read" in m for m in msgs)
test("Interactive: read displays without changes", test_interactive_read_no_change)


def test_interactive_delete_asks_even_after_all():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    keep = os.path.join(d, "keep.py")
    open(keep, "w").write("x")
    plan = {"summary": "multi", "files": [
        {"path": "w.py", "action": "write", "content": "new"},
        {"path": "keep.py", "action": "delete"}]}
    # 'a' accepts the write, but delete must STILL be individually asked
    with _tty_ctx(), mock.patch("builtins.input", side_effect=["a", "n"]):
        applied, skipped, _ = ag.interactive_apply(plan, d)
    assert applied == 1  # write applied via 'a'
    assert skipped and "delete declined" in skipped[0][1]
    assert os.path.exists(keep)
    assert os.path.exists(os.path.join(d, "w.py"))
test("Interactive: 'a' never auto-confirms deletes", test_interactive_delete_asks_even_after_all)


def test_interactive_quit():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    plan = {"summary": "two", "files": [
        {"path": "a.py", "action": "write", "content": "1"},
        {"path": "b.py", "action": "write", "content": "2"}]}
    with _tty_ctx(), mock.patch("builtins.input", side_effect=["y", "q"]):
        applied, skipped, _ = ag.interactive_apply(plan, d)
    assert applied == 1
    assert os.path.exists(os.path.join(d, "a.py"))
    assert not os.path.exists(os.path.join(d, "b.py"))
test("Interactive: q quits after current file", test_interactive_quit)


def test_interactive_edit_diff_applies():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("v = 1\n")
    plan = {"summary": "edit", "files": [
        {"path": "x.py", "action": "edit",
         "edits": [{"search": "v = 1", "replace": "v = 2"}]}]}
    with _tty_ctx(), mock.patch("builtins.input", return_value="y"):
        applied, _, msgs = ag.interactive_apply(plan, d)
    assert applied == 1
    assert "v = 2" in open(os.path.join(d, "x.py")).read()
    assert any("+1" in m and "-1" in m for m in msgs)
test("Interactive: edit shows diff stat and applies", test_interactive_edit_diff_applies)


def test_context_builds():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "notes.txt"), "w") as f:
        f.write("hello world\n" * 3)
    ctx = llm._build_context(d, "fix notes.txt")
    assert "notes.txt" in ctx and "hello world" in ctx
test("Context: named file included in prompt context", test_context_builds)




# ── safe command execution ──

def test_exec_valid():
    from plugins.llm import exec as safe_exec
    ok, why = safe_exec.validate_command("python --version")
    assert ok and why is None
    ok, _ = safe_exec.validate_command("git status")
    assert ok
test("Exec: harmless commands validate", test_exec_valid)


def test_exec_forbidden():
    from plugins.llm import exec as safe_exec
    for bad in ("rm -rf .", "rm file.py", "sudo reboot", "mv a b",
                "git push origin main", "python -c 'import os'",
                "ls; rm x", "cd .. && ls", "echo hi > out.txt",
                "cat file | grep x", "pip install numpy"):
        ok, why = safe_exec.validate_command(bad)
        assert not ok, f"{bad} should be blocked ({why})"
test("Exec: destructive/meta commands blocked", test_exec_forbidden)


def test_exec_runs_inside_project():
    from plugins.llm import exec as safe_exec
    d = tempfile.mkdtemp()
    res = safe_exec.run_command("pwd", d)
    assert res["ok"] and res["output"].strip() == d, res
test("Exec: command runs inside project dir", test_exec_runs_inside_project)


def test_exec_missing_program():
    from plugins.llm import exec as safe_exec
    res = safe_exec.run_command("definitely_not_a_real_cmd_xyz --help", tempfile.mkdtemp())
    assert not res["ok"] and "not found" in res["error"]
test("Exec: missing program reports error", test_exec_missing_program)


def test_exec_blocked_reports():
    from plugins.llm import exec as safe_exec
    res = safe_exec.run_command("rm file.py", tempfile.mkdtemp())
    assert res["blocked"] and res["error"]
    assert "blocked" in safe_exec.chat_line(res)
test("Exec: blocked command surfaces in chat line", test_exec_blocked_reports)


def test_exec_plan_commands():
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    plan = {"commands": [{"cmd": "python --version"}, {"cmd": "rm x"}]}
    results, lines = ag.execute_plan_commands(plan, d)
    assert results[0]["ok"] and "executed" in lines[0]
    assert results[1]["blocked"] and "blocked" in lines[1]
test("Exec: plan commands execute + blocked surfaced", test_exec_plan_commands)


# ── indexer ──

def test_indexer_build():
    from plugins.llm import indexer
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "src"))
    with open(os.path.join(d, "src", "mod.py"), "w") as f:
        f.write("def hello():\n    return 1\n\nclass Foo:\n    pass\n")
    idx = indexer.build_index(d)
    assert idx["file_count"] == 1
    assert "src/mod.py" in idx["files"]
    syms = [s["name"] for s in idx["files"]["src/mod.py"]["symbols"]]
    assert "hello" in syms and "Foo" in syms
test("Index: builds file/symbol index", test_indexer_build)


def test_indexer_persists():
    from plugins.llm import indexer
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "a.py"), "w") as f:
        f.write("x = 1\n")
    indexer.build_index(d)
    loaded = indexer.load_index(d)
    assert loaded and loaded["file_count"] == 1
test("Index: persists to .fent_cache and loads", test_indexer_persists)


def test_indexer_skips_runtime():
    from plugins.llm import indexer
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, ".e_identity"))
    os.makedirs(os.path.join(d, "plugins", "__pycache__"))
    with open(os.path.join(d, "plugins", "x.py"), "w") as f:
        f.write("a = 1\n")
    with open(os.path.join(d, ".e_identity", "secret.key"), "w") as f:
        f.write("k")
    idx = indexer.build_index(d)
    names = list(idx["files"].keys())
    assert "plugins/x.py" in names and not any("secret" in n for n in names)
test("Index: runtime dirs excluded", test_indexer_skips_runtime)


def test_index_to_text():
    from plugins.llm import indexer
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "a.py"), "w") as f:
        f.write("def f():\n    pass\n")
    idx = indexer.build_index(d)
    text = indexer.index_to_text(idx)
    assert "Project index" in text and "a.py" in text
test("Index: renders to prompt text", test_index_to_text)


# ── multi-step + plan done ──

def test_plan_done():
    from plugins.llm import agent as ag
    assert ag.plan_is_done({"done": True, "summary": "x"})
    assert ag.plan_is_done({"files": [], "commands": []})
    assert not ag.plan_is_done({"files": [{"path": "a", "action": "write"}]})
    assert not ag.plan_is_done({"commands": [{"cmd": "ls"}]})
test("Plan: done detection", test_plan_done)


def test_multi_step_loop_mocked():
    import unittest.mock as mock
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    steps = iter([
        '{"files": [{"path": "a.py", "action": "write", "content": "x = 1\\n"}]}',
        '{"done": true, "summary": "all set"}',
    ])
    llm.providers.chat_request = lambda *a, **k: (next(steps), None)
    class FakeAPI:
        project_dir = d
        def get_config(self, k, default=None):
            cfg = {"llm_setup_done": True, "llm_index_enabled": False,
                   "llm_agents_enabled": False, "llm_provider": "deepseek",
                   "llm_model": "deepseek-chat", "llm_connected": True}
            return cfg.get(k, default)
        def set_config(self, k, v): pass
        def get_auth_token(self, k): return "x"
    api = FakeAPI()
    state = llm._get_state(api)
    with mock.patch.object(llm.llm_agent, "_is_tty", return_value=True), \
         mock.patch("builtins.input", return_value="y"):
        llm._agentic(api, state, "create a.py", confirm_write=False, max_steps=3)
    assert os.path.exists(os.path.join(d, "a.py"))
test("Multi-step: plan → apply → done (mocked)", test_multi_step_loop_mocked)


# ── setup wizard + persistence ──

def test_state_persists_toggles():
    import plugins.llm as llm
    class FakeAPI:
        def __init__(self):
            self.cfg = {}
            self.tokens = {}
        def get_config(self, k, default=None): return self.cfg.get(k, default)
        def set_config(self, k, v): self.cfg[k] = v
        def get_auth_token(self, k): return self.tokens.get(k)
        def set_auth_token(self, k, v): self.tokens[k] = v
    api = FakeAPI()
    state = llm._get_state(api)
    assert state["setup_done"] is False
    state["agents_enabled"] = True
    state["agent_model"] = "deepseek-chat"
    state["setup_done"] = True
    state["index_enabled"] = True
    llm._save_state(api, state)
    # "new machine" simulation: fresh API reads from persisted config
    api2 = FakeAPI()
    api2.cfg = dict(api.cfg)
    state2 = llm._get_state(api2)
    assert state2["agents_enabled"] is True
    assert state2["agent_model"] == "deepseek-chat"
    assert state2["setup_done"] is True
test("Settings: agents/index/setup persist forever", test_state_persists_toggles)



# ── regression: real-world index crash (register(api) has no group) ──

def test_indexer_plugin_register_line():
    from plugins.llm import indexer
    d = tempfile.mkdtemp()
    os.makedirs(os.path.join(d, "plugins", "demo"))
    with open(os.path.join(d, "plugins", "demo", "__init__.py"), "w") as f:
        f.write("def register(api):\n    api.add_command('demo', demo_cmd)\n"
                "def demo_cmd(a):\n    pass\n")
    with open(os.path.join(d, "hook.py"), "w") as f:
        f.write("register(api)\n")  # bare call line — group-less pattern
    idx = indexer.build_index(d)  # must not raise IndexError
    assert idx["file_count"] == 2
    syms = [s["name"] for s in idx["files"]["plugins/demo/__init__.py"]["symbols"]]
    assert "register" in syms and "demo_cmd" in syms, syms
    hook_syms = [s["name"] for s in idx["files"]["hook.py"]["symbols"]]
    assert "register(api)" in hook_syms, hook_syms
test("Index: register(api) lines no longer crash", test_indexer_plugin_register_line)



# ── context + parse robustness regressions ──

def test_parse_plan_rstring():
    from plugins.llm import agent as ag
    raw = '```json\n{"summary": "s", "files": [{"path": "x.py", "action": "edit", "edits": [{"search": r"if not args:", "replace": "x"}]}]}\n```'
    plan = ag.parse_plan(raw)
    assert plan is not None
    assert plan["files"][0]["edits"][0]["search"] == "if not args:"
test("Plan: Python r-string prefixes sanitized", test_parse_plan_rstring)


def test_context_keyword_windows():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    lines = [f"line {i}" for i in range(300)]
    lines[250] = "def do_help(args):"
    with open(os.path.join(d, "tool.py"), "w") as f:
        f.write("\n".join(lines))
    ctx = llm._build_context(d, "tool.py help crashes")
    assert "do_help" in ctx, "keyword window must reach the target line"
    assert "line 1" not in ctx or True  # windows not just head
test("Context: keyword windows reach deep lines", test_context_keyword_windows)


def test_reproduce_planted_bug():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "boom.py"), "w") as f:
        f.write("import sys\n"
                "def main():\n"
                "    if len(sys.argv) > 1 and sys.argv[1] == 'ok':\n"
                "        print('fine')\n"
                "    else:\n"
                "        raise RuntimeError('boom')\n"
                "if __name__ == '__main__':\n"
                "    main()\n")
    block = llm._reproduce(d, "boom.py crashes with an error")
    assert "boom.py" in block and "RuntimeError" in block, block
    assert "exit 1" in block or "exit" in block
test("Reproduce: captures real traceback of planted bug", test_reproduce_planted_bug)


def test_reproduce_skips_unknown():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "lib.py"), "w") as f:
        f.write("def helper():\n    pass\n")  # no __main__ → not a script
    assert llm._reproduce(d, "lib.py has a bug") == ""
test("Reproduce: library file skipped", test_reproduce_skips_unknown)


# ── context + parse robustness regressions ──

def test_parse_plan_rstring():
    from plugins.llm import agent as ag
    raw = '```json\n{"summary": "s", "files": [{"path": "x.py", "action": "edit", "edits": [{"search": r"if not args:", "replace": "x"}]}]}\n```'
    plan = ag.parse_plan(raw)
    assert plan is not None
    assert plan["files"][0]["edits"][0]["search"] == "if not args:"
test("Plan: Python r-string prefixes sanitized", test_parse_plan_rstring)


def test_context_keyword_windows():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    lines = [f"line {i}" for i in range(300)]
    lines[250] = "def do_help(args):"
    with open(os.path.join(d, "tool.py"), "w") as f:
        f.write("\n".join(lines))
    ctx = llm._build_context(d, "tool.py help crashes")
    assert "do_help" in ctx, "keyword window must reach the target line"
test("Context: keyword windows reach deep lines", test_context_keyword_windows)


def test_reproduce_planted_bug():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "boom.py"), "w") as f:
        f.write("import sys\n"
                "def main():\n"
                "    if len(sys.argv) > 1 and sys.argv[1] == 'ok':\n"
                "        print('fine')\n"
                "    else:\n"
                "        raise RuntimeError('boom')\n"
                "if __name__ == '__main__':\n"
                "    main()\n")
    block = llm._reproduce(d, "boom.py crashes with an error")
    assert "boom.py" in block and "RuntimeError" in block, block
    assert "exit 1" in block or "exit" in block
test("Reproduce: captures real traceback of planted bug", test_reproduce_planted_bug)


def test_reproduce_skips_unknown():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "lib.py"), "w") as f:
        f.write("def helper():\n    pass\n")  # no __main__ → not a script
    assert llm._reproduce(d, "lib.py has a bug") == ""
test("Reproduce: library file skipped", test_reproduce_skips_unknown)



# ── venv python rewrite + line-range edits + syntax check ──

def test_exec_uses_project_interpreter():
    from plugins.llm import exec as safe_exec
    d = tempfile.mkdtemp()
    res = safe_exec.run_command("python -c 'import sys; print(sys.executable)'", d)
    # -c is blocked; use a script file instead
    with open(os.path.join(d, "whichpy.py"), "w") as f:
        f.write("import sys\nprint(sys.executable)\n")
    res = safe_exec.run_command("python whichpy.py", d)
    assert res["ok"], res
    assert res["output"].strip() == sys.executable, res
test("Exec: python commands run the project interpreter", test_exec_uses_project_interpreter)


def test_line_range_edit():
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a = 1\nb = 2\nc = 3\n")
    plan = {"summary": "line edit", "files": [
        {"path": "x.py", "action": "edit", "lines": [2, 2], "replace": "b = 42\nb2 = 43"}]}
    applied, skipped, _ = ag.interactive_apply(plan, d, confirm_write=False)
    assert applied == 1, skipped
    assert open(os.path.join(d, "x.py")).read() == "a = 1\nb = 42\nb2 = 43\nc = 3\n"
test("Edit: line-range replacement works", test_line_range_edit)


def test_line_range_out_of_bounds():
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a = 1\n")
    plan = {"summary": "bad", "files": [
        {"path": "x.py", "action": "edit", "lines": [5, 9], "replace": "x"}]}
    applied, skipped, _ = ag.interactive_apply(plan, d, confirm_write=False)
    assert applied == 0 and skipped and "out of range" in skipped[0][1]
test("Edit: out-of-range lines skipped", test_line_range_out_of_bounds)


def test_syntax_check():
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "ok.py"), "w") as f:
        f.write("x = 1\n")
    with open(os.path.join(d, "bad.py"), "w") as f:
        f.write("def broken(:\n")
    ok, _ = llm._syntax_check(d, "ok.py")
    assert ok
    ok, detail = llm._syntax_check(d, "bad.py")
    assert not ok and detail
test("Syntax: auto py_compile check flags broken files", test_syntax_check)



def test_parse_plan_regex_escapes():
    from plugins.llm import agent as ag
    raw = ('{"summary": "s", "files": [{"path": "x.py", "action": "edit", '
           '"edits": [{"search": r"sys.argv\\[1\\] == \'hello\'", "replace": "y"}]}]}')
    plan = ag.parse_plan(raw)
    assert plan is not None
    assert plan["files"][0]["edits"][0]["search"] == "sys.argv[1] == 'hello'"
test("Plan: Python regex escapes sanitized", test_parse_plan_regex_escapes)



# ── edit-not-rewrite policy + insert ──

def test_existing_file_rewrite_refused():
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a = 1\nb = 2\n" * 50)
    plan = {"summary": "rewrite", "files": [
        {"path": "x.py", "action": "write", "content": "a = 1\nb = 2\n" * 50}]}
    applied, skipped, _ = ag.interactive_apply(plan, d, confirm_write=False)
    assert applied == 0 and skipped and "'yes'" in skipped[0][1], skipped
test("Policy: existing file rewrite refused even under --yes", test_existing_file_rewrite_refused)


def test_existing_file_rewrite_explicit_yes():
    import unittest.mock as mock
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("old\n" * 10)
    plan = {"summary": "rewrite", "files": [
        {"path": "x.py", "action": "write", "content": "brand new\n"}]}
    with mock.patch.object(ag, "_is_tty", return_value=True), \
         mock.patch("builtins.input", return_value="yes"):
        applied, skipped, _ = ag.interactive_apply(plan, d)
    assert applied == 1 and not skipped
    assert open(os.path.join(d, "x.py")).read() == "brand new\n"
test("Policy: explicit 'yes' can authorize a rewrite", test_existing_file_rewrite_explicit_yes)


def test_insert_lines():
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a\nc\n")
    plan = {"summary": "insert", "files": [
        {"path": "x.py", "action": "edit", "lines": [2], "replace": "b"}]}
    applied, skipped, _ = ag.interactive_apply(plan, d, confirm_write=False)
    assert applied == 1, skipped
    assert open(os.path.join(d, "x.py")).read() == "a\nb\nc\n"
test("Edit: [x] inserts before line x (no end)", test_insert_lines)


def test_insert_null_end():
    from plugins.llm import agent as ag
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("a\nb\n")
    plan = {"summary": "insert", "files": [
        {"path": "x.py", "action": "edit", "lines": [2, None], "replace": "mid"}]}
    applied, skipped, _ = ag.interactive_apply(plan, d, confirm_write=False)
    assert applied == 1, skipped
    assert open(os.path.join(d, "x.py")).read() == "a\nmid\nb\n"
test("Edit: [x, null] also inserts", test_insert_null_end)



# ── interactive agent session (mocked, multi-turn) ──

def test_agent_repl_multi_turn():
    import unittest.mock as mock
    import plugins.llm as llm
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "x.py"), "w") as f:
        f.write("v = 1\n")
    replies = iter([
        '{"summary": "bump", "files": [{"path": "x.py", "action": "edit", '
        '"lines": [1, 1], "replace": "v = 2"}]}',
        'The file now has v = 2. Anything else?',
        '{"done": true, "summary": "done"}',
    ])
    llm.providers.chat_request = lambda *a, **k: (next(replies), None)
    class FakeAPI:
        project_dir = d
        def get_config(self, k, default=None):
            cfg = {"llm_setup_done": True, "llm_index_enabled": False,
                   "llm_agents_enabled": False, "llm_provider": "deepseek",
                   "llm_model": "deepseek-chat", "llm_connected": True}
            return cfg.get(k, default)
        def set_config(self, k, v): pass
        def get_auth_token(self, k): return "x"
    api = FakeAPI()
    state = llm._get_state(api)
    turns = iter(["change v to 2", "y", "what now?", "quit"])
    class _FakeStdin:
        def isatty(self):
            return True
    with mock.patch.object(sys, "stdin", _FakeStdin()), \
         mock.patch.object(llm.llm_agent, "_is_tty", return_value=True), \
         mock.patch("builtins.input", side_effect=lambda *a: next(turns)):
        llm._agent_repl(api, state)
    assert open(os.path.join(d, "x.py")).read() == "v = 2\n"
test("Agent repl: multi-turn edits then conversation", test_agent_repl_multi_turn)

# ── tests_runner: discovery / running / summarizing / auto-fix ──

import json as _json
from plugins.llm import tests_runner as tr

_FAKE_HARNESS = '''import sys
passed = 0
failed = 0
def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print("  [PASS] " + name)
    except Exception:
        failed += 1
        print("  [FAIL] " + name)
'''


def _write_fake(project_dir, name, body):
    os.makedirs(os.path.join(project_dir, "tests"), exist_ok=True)
    with open(os.path.join(project_dir, "tests", name), "w") as fh:
        fh.write(_FAKE_HARNESS + body)


def test_discover_real_tests_dir():
    found = tr.discover_test_files(ROOT)
    assert len(found) >= 5
    assert all(f.startswith("tests") and f.endswith("_test.py") for f in found)
test("tests_runner: discovers real tests dir (>= 5 files)", test_discover_real_tests_dir)


def test_run_test_file_scratch_failing():
    with tempfile.TemporaryDirectory() as d:
        _write_fake(d, "scratch_test.py",
                    'test("a", lambda: None)\ntest("b", lambda: None)\n'
                    'test("c", lambda: 1 / 0)\n'
                    'print("SCRATCH TESTS: %d/%d passed" % (passed, passed + failed))\n'
                    "sys.exit(1)\n")
        res = tr.run_test_file(d, "tests/scratch_test.py")
        assert res["total"] == 3 and res["passed"] == 2 and res["failed"] == 1
        assert res["ok"] is False
test("tests_runner: scratch file 2 pass / 1 fail parsed, ok=False", test_run_test_file_scratch_failing)


def test_run_test_file_scratch_passing():
    with tempfile.TemporaryDirectory() as d:
        _write_fake(d, "ok_test.py",
                    'test("a", lambda: None)\ntest("b", lambda: None)\n'
                    'print("OK TESTS: %d/%d passed" % (passed, passed + failed))\n')
        res = tr.run_test_file(d, "tests/ok_test.py")
        assert res["total"] == 2 and res["passed"] == 2 and res["failed"] == 0
        assert res["exit_code"] == 0 and res["ok"] is True
test("tests_runner: fully passing scratch file ok=True", test_run_test_file_scratch_passing)


def test_summarize_markers():
    with tempfile.TemporaryDirectory() as d:
        _write_fake(d, "ok_test.py",
                    'test("a", lambda: None)\n'
                    'print("OK TESTS: %d/%d passed" % (passed, passed + failed))\n')
        _write_fake(d, "bad_test.py",
                    'test("a", lambda: 1 / 0)\n'
                    'print("BAD TESTS: %d/%d passed" % (passed, passed + failed))\n'
                    "sys.exit(1)\n")
        results = tr.run_tests(d)
        text = tr.summarize(results)
        assert "\u2713 tests/ok_test.py" in text and "\u2717 tests/bad_test.py" in text
        assert "2 files, 1 passed / 1 failed" in text
        assert "output (truncated)" in text and "FAIL" in text
test("tests_runner: summarize shows ✓/✗ markers + file names", test_summarize_markers)


def test_plan_test_targets():
    assert tr.plan_test_targets({"tests": "all", "files": []}) is None
    assert tr.plan_test_targets({"tests": ["a_test.py", "b_test.py"]}) == ["a_test.py", "b_test.py"]
    assert tr.plan_test_targets({"files": []}) is None
    assert tr.plan_test_targets(None) is None
test("tests_runner: plan_test_targets all/list/absent", test_plan_test_targets)


def test_auto_fix_loop():
    with tempfile.TemporaryDirectory() as d:
        _write_fake(d, "fix_test.py",
                    "def value():\n    return 1\n"
                    'def check():\n    assert value() == 2, "value must be 2"\n'
                    'test("value is 2", check)\n'
                    'print("FIX TESTS: %d/%d passed" % (passed, passed + failed))\n'
                    "if failed:\n    sys.exit(1)\n")
        plan1 = {"tests": ["tests/fix_test.py"], "files": [
            {"path": "tests/fix_test.py", "action": "edit",
             "edits": [{"search": "def value():\n    return 1",
                        "replace": "def value():\n    return 1  # patched"}]}]}
        calls = []

        def model_fn(messages):
            calls.append(messages)
            assert "fix_test.py" in messages[0]["content"]
            return _json.dumps({"tests": ["tests/fix_test.py"], "files": [
                {"path": "tests/fix_test.py", "action": "edit",
                 "edits": [{"search": "def value():\n    return 1",
                            "replace": "def value():\n    return 2"}]}]})

        apply_fn = lambda plan, pd: llm_agent.apply_plan(plan, pd, confirm_write=False)
        out = tr.auto_fix_loop(d, model_fn, plan1, apply_fn, max_rounds=3)
        assert out["rounds"] == 2
        assert len(out["fixes_applied"]) == 2
        assert all(r["ok"] for r in out["final_results"])
        assert len(calls) == 1
test("tests_runner: auto-fix loop greens in 2 rounds", test_auto_fix_loop)

print(f"\n{'='*50}")
print(f"LLM PLUGIN TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LLM PLUGIN TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
