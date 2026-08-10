#!/usr/bin/env python3
"""K-rip plugin tests — run with:
    python3 plugins/krip/tests/test_krip.py
"""

import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, ROOT)

from plugins import krip as K

passed = failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except AssertionError as e:
        failed += 1
        print(f"  [FAIL] {name}: {e}")


class FakeApi:
    project_dir = ROOT
    def get_config(self, k):
        return None
    def set_config(self, k, v):
        pass
    def add_command(self, *a):
        pass
    def add_boot_step(self, *a):
        pass


def test_gpu_env():
    assert K._gpu_env("auto") == {}
    assert K._gpu_env("all") == {}
    env = K._gpu_env("0,1")
    assert env.get("CUDA_VISIBLE_DEVICES") == "0,1", env
    env = K._gpu_env("2 3")
    assert env.get("CUDA_VISIBLE_DEVICES") == "2,3", env
check("gpu env: auto/all/ids + multi-GPU", test_gpu_env)


def test_mem_apply():
    import resource as _r
    r = K._apply_rlimits(0)
    assert r == "unlimited"
    r = K._apply_rlimits(512)
    assert r == "512 MB"
    # restore (soft-only limit) so the rest of the suite is unaffected
    _r.setrlimit(_r.RLIMIT_AS, (_r.RLIM_INFINITY, _r.RLIM_INFINITY))
check("mem: unlimited + budget apply", test_mem_apply)


def test_engine_validation():
    K._config["engine"] = "vulkan"
    out = K._cmd(["engine", "opengl"], FakeApi())
    assert "opengl" in out and K._config["engine"] == "opengl"
    out = K._cmd(["engine", "nonsense"], FakeApi())
    assert "usage" in out
    K._config["engine"] = "vulkan"
check("engine: vulkan default, opengl switch, invalid rejected", test_engine_validation)


def test_tensor_vulkanrt():
    K._config["vulkanrt"] = False
    K._cmd(["vulkanrt", "on"], FakeApi())
    assert K._config["vulkanrt"] is True
    K._cmd(["tensor", "off"], FakeApi())
    assert K._config["tensor"] == "off"
    K._cmd(["tensor", "auto"], FakeApi())
    assert K._config["tensor"] == "auto"
check("vulkanrt on/off + tensor on/off/auto", test_tensor_vulkanrt)


def test_sandbox_run_list_kill():
    K.PROJECT_DIR = ROOT
    out = K.sandbox_run("probe1", [sys.executable, "-c", "import time; time.sleep(30)"],
                        0, 0, "auto")
    assert "started" in out, out
    out = K.sandbox_run("probe1", [sys.executable, "-c", "pass"], 0, 0, "auto")
    assert "already running" in out
    st = K.sandbox_status()
    assert "probe1" in st
    out = K.sandbox_kill("probe1")
    assert "killed" in out
    st = K.sandbox_status()
    assert "probe1" not in st
check("sandbox: run/list/kill lifecycle", test_sandbox_run_list_kill)


def test_sandbox_rlimits():
    K.PROJECT_DIR = ROOT
    out = K.sandbox_run("rlim1", [sys.executable, "-c", "pass"], 64, 1, "0")
    assert "started" in out, out
    K.sandbox_kill("rlim1")
check("sandbox: spawn with memory/cpu/gpu limits", test_sandbox_rlimits)


def test_os_view():
    out = K._cmd(["os"], FakeApi())
    assert "kernel" in out and "hypervisor" in out and "drivers" in out
    assert "krip" in out.lower()
check("os: HELLFORGE OS view (kernel/hypervisor/drivers)", test_os_view)


def test_status():
    out = K._cmd(["status"], FakeApi())
    assert "memory" in out and "cpu" in out and "gpu" in out
    assert "engine" in out and "vulkanrt" in out and "tensor" in out
check("status: full allocation view", test_status)


def test_config_file_init():
    import tempfile, json as _json
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    _json.dump({"mem_mb": 128, "cpu_threads": 4, "gpu": "0,1",
                "engine": "opengl", "vulkanrt": True, "tensor": "off"},
               open(os.path.join(tmp, "krip.json"), "w"))
    api = FakeApi()
    api.project_dir = tmp
    K._load(api)
    assert K._config["mem_mb"] == 128, K._config
    assert K._config["gpu"] == "0,1"
    assert K._config["engine"] == "opengl"
    assert K._config["vulkanrt"] is True
    assert K._config["tensor"] == "off"
    K._config["mem_mb"] = 256
    K._cmd(["save"], api)
    K._config["mem_mb"] = 0
    K._cmd(["reload"], api)
    assert K._config["mem_mb"] == 256, "reload must read the saved file"
    import resource as _r
    _r.setrlimit(_r.RLIMIT_AS, (_r.RLIM_INFINITY, _r.RLIM_INFINITY))
check("config: krip.json read at init, save, reload", test_config_file_init)


def test_config_file_missing_defaults():
    import tempfile
    tmp = tempfile.mkdtemp()
    api = FakeApi()
    api.project_dir = tmp
    K.PROJECT_DIR = tmp
    K._load(api)
    assert K._config["engine"] == "vulkan"
    assert K._config["gpu"] == "auto"
check("config: no krip.json -> built-in defaults", test_config_file_missing_defaults)


def test_boot_registry_rollback():
    import tempfile, unittest.mock as mock
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    cur_ver, _ = K._kernel_meta()
    K.record_current_kernel()
    K.snapshot_previous_kernel()
    with mock.patch.object(K, "_kernel_meta",
                           return_value=("0.9.9-beta", "m1")):
        K.record_current_kernel()
    entries = K.load_kernels()
    vers = [e["version"] for e in entries]
    assert vers.count("0.9.9-beta") == 2, vers
    assert vers.count(cur_ver) == 2, vers
    cur = [e for e in entries if e.get("current")]
    assert all(e["version"] == "0.9.9-beta" for e in cur)
check("boot: registry rolls old latest to previous, new becomes current", test_boot_registry_rollback)


def test_boot_menu_default_and_console():
    import tempfile
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    K.record_current_kernel()
    r = K.boot_menu(lambda l, **k: None, lambda p='': '', interactive=False)
    assert r[0] == "boot" and r[1]["mode"] == "normal", r
    r = K.boot_menu(lambda l, **k: None, lambda p='': 'console', interactive=False)
    assert r[0] == "console", r
check("boot: menu defaults to normal kernel, console via input", test_boot_menu_default_and_console)


def test_boot_menu_numbered_selection():
    import tempfile, unittest.mock as mock
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    K.record_current_kernel()
    with mock.patch.object(K, "_kernel_meta",
                           return_value=("0.9.9-beta", "m1")):
        K.record_current_kernel()
    r = K.boot_menu(lambda l, **k: None, lambda p='': '1', interactive=False)
    assert r[1]["version"] == "0.9.9-beta", r
check("boot: numbered selection picks a previous kernel", test_boot_menu_numbered_selection)


def test_edit_uses_editor_and_reloads():
    import tempfile, subprocess as _sp
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    K._last_api = None
    K._load(None)
    # fake editor: writes a new mem value into krip.json
    editor = sys.executable + " -c 'import json,sys; d=json.load(open(sys.argv[1])); d[\"mem_mb\"]=768; json.dump(d,open(sys.argv[1],\"w\"),indent=2)'"
    old = os.environ.get("KRIP_EDITOR")
    os.environ["KRIP_EDITOR"] = editor
    try:
        K._cmd(["edit"], None)
    finally:
        if old is None:
            os.environ.pop("KRIP_EDITOR", None)
        else:
            os.environ["KRIP_EDITOR"] = old
    assert K._config["mem_mb"] == 768, K._config["mem_mb"]
check("edit: editor writes config, K-rip reloads it", test_edit_uses_editor_and_reloads)


# restore any memory budget the tests applied, so the process is unharmed
try:
    import resource as _r
    _r.setrlimit(_r.RLIMIT_AS, (_r.RLIM_INFINITY, _r.RLIM_INFINITY))
except Exception:
    pass


def test_hypervisor_entry_run():
    import tempfile, unittest.mock as mock
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    calls = []
    with mock.patch.object(K, "_spawn", side_effect=lambda cmd, name="x", stream_out=print: calls.append((cmd, name)) or 0):
        K.hypervisor_entry(["run", "echo", "hi"])
    assert calls and calls[0][0] == ["echo", "hi"], calls
check("hypervisor: krip run <cmd> spawns inside the sandbox", test_hypervisor_entry_run)


def test_hypervisor_entry_console():
    import tempfile, unittest.mock as mock
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    calls = []
    with mock.patch.object(K, "boot_menu", return_value=("boot", {"version": "x", "mode": "normal"})), \
         mock.patch.object(K, "boot_entry", return_value=0), \
         mock.patch.object(K, "_spawn_eshell", side_effect=lambda so=print: calls.append("eshell") or 0):
        K.hypervisor_entry([])
    assert "eshell" in calls
check("hypervisor: krip (no args) -> menu -> console", test_hypervisor_entry_console)


def test_hypervisor_entry_status():
    import tempfile, unittest.mock as mock
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    out = []
    rc = K.hypervisor_entry(["status"], lambda l, **k: out.append(l))
    assert rc == 0 and any("memory" in l for l in out)
check("hypervisor: krip status", test_hypervisor_entry_status)


def test_escape_exits_krip():
    import tempfile, unittest.mock as mock
    tmp = tempfile.mkdtemp()
    K.PROJECT_DIR = tmp
    K.record_current_kernel()
    # ESC in the interactive menu -> ("exit", None)
    with mock.patch.object(K, "_read_key_raw", side_effect=["escape"]):
        r = K.boot_menu(lambda l, **k: None, lambda p='': '',
                        interactive=True, timeout=0.1)
    assert r[0] == "exit", r
    # hypervisor honors it: no console spawn, rc 0
    spawned = []
    with mock.patch.object(K, "boot_menu", return_value=("exit", None)), \
         mock.patch.object(K, "_spawn_eshell",
                           side_effect=lambda so=print: spawned.append(1) or 0):
        outs = []
        rc = K.hypervisor_entry([], lambda l, **k: outs.append(l), lambda p='': '')
    assert rc == 0 and not spawned, (rc, spawned)
check("escape: exits krip to the terminal, no console spawn", test_escape_exits_krip)


print(f"\nKRIP TESTS: {passed}/{passed + failed} passed")
sys.exit(0 if failed == 0 else 1)
