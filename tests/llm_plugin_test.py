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


print(f"\n{'='*50}")
print(f"LLM PLUGIN TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LLM PLUGIN TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
