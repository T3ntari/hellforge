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


print(f"\n{'='*50}")
print(f"LLM PLUGIN TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LLM PLUGIN TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
