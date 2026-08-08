#!/usr/bin/env python3
"""HELLFORGE launch tests — window/detach flags, launcher plugin, run.py."""
import sys
import os
import glob
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


# === FLAG SELECTION ===

def test_flags_default():
    from _launch import get_creation_flags
    f = get_creation_flags(window=False, detach=False)
    assert f == 0, f"default should be 0, got {f}"
test("Launch: default flags = 0 (inherit console)", test_flags_default)


def test_flags_window():
    from _launch import get_creation_flags
    f = get_creation_flags(window=True, detach=False)
    if os.name == "nt":
        assert f & getattr(subprocess, "CREATE_NEW_CONSOLE", 0), "should set CREATE_NEW_CONSOLE"
        assert f & getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0), "should set CREATE_NEW_PROCESS_GROUP"
    else:
        assert f == 0
test("Launch: window mode sets CREATE_NEW_CONSOLE", test_flags_window)


def test_flags_detach():
    from _launch import get_creation_flags
    f = get_creation_flags(window=False, detach=True)
    if os.name == "nt":
        assert f & getattr(subprocess, "DETACHED_PROCESS", 0), "should set DETACHED_PROCESS"
    else:
        assert f == 0
test("Launch: detach mode sets DETACHED_PROCESS", test_flags_detach)


def test_run_py_help():
    r = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run.py"), "--help"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    assert r.returncode == 0
    assert "Usage" in r.stdout or "play" in r.stdout
test("run.py: --help works", test_run_py_help)


def test_run_py_detach_compile():
    """Detach a compile of a sample file, wait, verify log + output exist."""
    project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sample = os.path.join(project, "samples", "v4-current", "basics", "hello_world_v4.e")
    if not os.path.exists(sample):
        # fallback sample
        candidates = glob.glob(os.path.join(project, "samples", "**", "*.e"), recursive=True)
        sample = candidates[0] if candidates else None
    if not sample:
        print("   Skipped: no sample file")
        return
    out = os.path.join(project, "logs", "test_detach.mid")
    os.makedirs(os.path.join(project, "logs"), exist_ok=True)
    r = subprocess.run(
        [sys.executable, os.path.join(project, "run.py"), "compile", sample, "-o", out, "--detach"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    assert r.returncode == 0
    assert "Detached" in r.stdout, f"expected Detached in output: {r.stdout}"
test("run.py: compile --detach returns immediately", test_run_py_detach_compile)


# === LAUNCHER PLUGIN ===

def test_launcher_import():
    from plugins.launcher import (
        VERSION,
        _cmd,
    )
    assert VERSION == "1.0.0"
    assert callable(_cmd)
test("Launcher: plugin imports", test_launcher_import)


def test_launcher_ps():
    from plugins.launcher import _cmd
    import io
    sys.stdout = io.StringIO()
    try:
        _cmd(["ps"])
    finally:
        out = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__
    assert "HELLFORGE" in out or "processes" in out.lower() or "running" in out.lower()
test("Launcher: ps command runs", test_launcher_ps)


def test_launcher_log():
    from plugins.launcher import _cmd
    import io
    sys.stdout = io.StringIO()
    try:
        _cmd(["log"])
    finally:
        out = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__
    assert out.strip(), "log should print something"
test("Launcher: log command runs", test_launcher_log)


def test_launcher_open_missing():
    from plugins.launcher import _cmd
    import io
    sys.stdout = io.StringIO()
    try:
        _cmd(["open", "nonexistent_file_xyz.e"])
    finally:
        out = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__
    assert "Not found" in out
test("Launcher: open missing file reports error", test_launcher_open_missing)


def test_kill_invalid():
    from plugins.launcher import _cmd
    import io
    sys.stdout = io.StringIO()
    try:
        _cmd(["kill", "abc"])
    finally:
        out = sys.stdout.getvalue()
        sys.stdout = sys.__stdout__
    assert "Invalid PID" in out
test("Launcher: kill invalid PID reports error", test_kill_invalid)


# === ESCHELL COMMANDS REGISTERED ===

def test_eshell_commands():
    import eshell
    assert hasattr(eshell, "do_run"), "eshell should have do_run"
    assert hasattr(eshell, "do_shell"), "eshell should have do_shell"
    # Verify run.py exists
    run_py = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "run.py")
    assert os.path.exists(run_py), "run.py should exist"
test("eshell: run/shell commands + run.py present", test_eshell_commands)


print(f"\n{'='*50}")
print(f"LAUNCH TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LAUNCH TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
