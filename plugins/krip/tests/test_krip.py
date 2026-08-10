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
    r = K._apply_rlimits(0)
    assert r == "unlimited"
    r = K._apply_rlimits(512)
    assert r == "512 MB"
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


print(f"\nKRIP TESTS: {passed}/{passed + failed} passed")
sys.exit(0 if failed == 0 else 1)
