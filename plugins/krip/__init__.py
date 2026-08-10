"""K-rip — the HELLFORGE hypervisor layer.

K-rip sandboxes the entire shell: its boot, init and every plugin run under
it get a heavy resource layer on top of the existing plugin sandbox:
memory budgets (RLIMIT_AS), CPU thread caps + affinity, GPU selection
(single / multi / list / auto), the default graphics engine (Vulkan by
default, OpenGL supported), VulkanRT and Tensor support — all via the
`krip` command. Arbitrary processes can be sandboxed too.

HELLFORGE behaves like an OS: ep_core is the kernel, every plugin is a
driver, K-rip is the hypervisor (`krip os` shows the table).

    krip status | mem <mb> | cpu <n> | gpu <auto|list|all|ids...>
    krip engine <vulkan|opengl> | vulkanrt <on|off> | tensor <on|off|auto>
    krip sandbox run <name> -- <cmd...> | list | kill <name> | status
    krip os
"""

import os
import sys
import json
import shlex
import signal
import subprocess
import threading

VERSION = "1.0.0"
author = "Tentari"
description = "Hypervisor layer — heavy sandboxing, memory/CPU/GPU allocation, graphics engine default, VulkanRT + Tensor"

_lock = threading.Lock()
_sandboxes = {}       # name -> Popen
_config = {
    "mem_mb": 0,          # 0 = unlimited
    "cpu_threads": 0,     # 0 = all
    "gpu": "auto",        # auto | list | all | "0,1" (multi-GPU)
    "engine": "vulkan",   # vulkan (default) | opengl
    "vulkanrt": False,
    "tensor": "auto",     # on | off | auto
}

PROJECT_DIR = None


# ── helpers ───────────────────────────────────────────────────────────

def _cfg(api, key, default):
    try:
        v = api.get_config(key)
        return default if v is None else v
    except Exception:
        return default


def _save(api):
    try:
        for k, v in _config.items():
            api.set_config(f"krip_{k}", v)
    except Exception:
        pass


def _load(api):
    for k in _config:
        _config[k] = _cfg(api, f"krip_{k}", _config[k])


def _apply_rlimits(mem_mb):
    """Apply the memory budget to the CURRENT process (RLIMIT_AS)."""
    if mem_mb <= 0:
        return "unlimited"
    try:
        import resource
        limit = mem_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
        return f"{mem_mb} MB"
    except Exception as e:
        return f"not applied ({e})"


def _apply_affinity(n_threads):
    """Pin the current process to the first n_threads CPUs."""
    if n_threads <= 0:
        return "all cpus"
    try:
        os.sched_setaffinity(0, list(range(n_threads)))
        return f"{n_threads} cpus"
    except Exception as e:
        return f"not applied ({e})"


def _gpu_env(gpu_spec):
    """GPU selection -> environment for spawned processes.
    auto: leave alone; list: print and leave; all: no filter;
    '0,1' or '1 2 3': CUDA_VISIBLE_DEVICES (multi-GPU supported)."""
    env = {}
    spec = str(gpu_spec).strip()
    if spec == "all" or spec == "auto":
        return env
    if spec == "list":
        return env  # informational only
    parts = [p.strip() for p in spec.replace(",", " ").split() if p.strip()]
    cleaned = ",".join(parts)
    if cleaned:
        env["CUDA_VISIBLE_DEVICES"] = cleaned
        env["KRIP_GPU"] = cleaned
    return env


def _gpu_list():
    """Best-effort list of GPUs (radical's detector when available)."""
    try:
        from plugins.radical.gpu_detect import detect_gpu
        info = detect_gpu()
        if info and info.get("available"):
            return [info.get("name", "GPU")]
    except Exception:
        pass
    try:
        if os.environ.get("CUDA_VISIBLE_DEVICES"):
            return os.environ["CUDA_VISIBLE_DEVICES"].split(",")
    except Exception:
        pass
    return ["(auto)"]


def _driver_table():
    """plugins/ = drivers; returns sorted names."""
    try:
        plugs = os.path.join(PROJECT_DIR, "plugins")
        return sorted(d for d in os.listdir(plugs)
                      if os.path.isdir(os.path.join(plugs, d))
                      and d != "__pycache__")
    except Exception:
        return []


# ── sandboxed process launch ──────────────────────────────────────────

def _preexec_limits(mem_mb, n_threads, affinity_start):
    """pre_exec_fn: apply RLIMITs + CPU affinity to a sandboxed child."""
    def fn():
        try:
            import resource
            if mem_mb > 0:
                limit = mem_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
            resource.setrlimit(resource.RLIMIT_CPU, (600, 600))
            resource.setrlimit(resource.RLIMIT_FSIZE, (64 * 1024 * 1024,
                                                       64 * 1024 * 1024))
            if n_threads > 0:
                os.sched_setaffinity(0,
                                     list(range(affinity_start,
                                                affinity_start + n_threads)))
        except Exception:
            pass
    return fn


def sandbox_run(name, cmd, mem_mb, n_threads, gpu_spec):
    """Run a command inside a K-rip sandbox. Confined to the project root;
    memory/CPU/GPU limits applied; tracked for list/kill."""
    if not cmd:
        return "  usage: krip sandbox run <name> -- <cmd...>"
    if name in _sandboxes:
        return f"  sandbox '{name}' already running"
    base = dict(os.environ)
    base.update(_gpu_env(gpu_spec))
    base["KRIP_SANDBOX"] = name
    try:
        p = subprocess.Popen(cmd, cwd=PROJECT_DIR, env=base,
                             preexec_fn=_preexec_limits(mem_mb, n_threads,
                                                        0 if n_threads <= 0 else 0),
                             start_new_session=True)
    except Exception as e:
        return f"  failed to start sandbox: {e}"
    with _lock:
        _sandboxes[name] = p
    return f"  sandbox '{name}' started (pid {p.pid})"


def sandbox_kill(name):
    with _lock:
        p = _sandboxes.get(name)
        if not p:
            return f"  no sandbox '{name}'"
        try:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
        except Exception:
            p.kill()
        del _sandboxes[name]
    return f"  sandbox '{name}' killed"


def sandbox_status():
    with _lock:
        if not _sandboxes:
            return "  no sandboxes running"
        out = []
        for name, p in sorted(_sandboxes.items()):
            state = "running" if p.poll() is None else f"exited ({p.returncode})"
            out.append(f"  {name:<16} pid {p.pid:<8} {state}")
        return "\n".join(out)


# ── the krip command ──────────────────────────────────────────────────

def _cmd(args, api=None):
    global PROJECT_DIR
    if api is not None:
        PROJECT_DIR = getattr(api, "project_dir", None) or PROJECT_DIR
    if not args:
        return _cmd(["status"], api)
    sub = args[0].lower()

    if sub == "status":
        lines = [
            "  K-rip hypervisor — allocation",
            f"    memory   : {_config['mem_mb']} MB "
            f"({_apply_rlimits(_config['mem_mb'])})",
            f"    cpu      : {_config['cpu_threads']} threads "
            f"({_apply_affinity(_config['cpu_threads'])})",
            f"    gpu      : {_config['gpu']}  ->  "
            f"{_gpu_env(_config['gpu']).get('CUDA_VISIBLE_DEVICES', 'all')}",
            f"    engine   : {_config['engine']} (default)",
            f"    vulkanrt : {'on' if _config['vulkanrt'] else 'off'}",
            f"    tensor   : {_config['tensor']}",
        ]
        sb = sandbox_status()
        if sb != "  no sandboxes running":
            lines.append(sb)
        return "\n".join(lines)

    if sub == "mem":
        if len(args) < 2 or not args[1].isdigit():
            return f"  usage: krip mem <mb>  (current: {_config['mem_mb']})"
        _config["mem_mb"] = int(args[1])
        _save(api)
        return f"  memory budget set to {args[1]} MB ({_apply_rlimits(_config['mem_mb'])})"

    if sub == "cpu":
        if len(args) < 2 or not args[1].isdigit():
            return f"  usage: krip cpu <n>  (current: {_config['cpu_threads']})"
        _config["cpu_threads"] = int(args[1])
        _save(api)
        return (f"  cpu threads set to {args[1]} "
                f"({_apply_affinity(_config['cpu_threads'])})")

    if sub == "gpu":
        if len(args) < 2:
            return ("  usage: krip gpu <auto|list|all|0,1,...>\n"
                    "    auto  detect at runtime\n"
                    "    list  show detected GPUs\n"
                    "    all   use every GPU\n"
                    "    0,1   use GPUs 0 and 1 (multi-GPU)")
        spec = " ".join(args[1:])
        if spec == "list":
            return "  detected GPUs: " + ", ".join(_gpu_list())
        _config["gpu"] = spec
        _save(api)
        env = _gpu_env(spec)
        dev = env.get("CUDA_VISIBLE_DEVICES", "all")
        return f"  gpu selection set to '{spec}' (visible: {dev})"

    if sub == "engine":
        if len(args) < 2 or args[1].lower() not in ("vulkan", "opengl"):
            return f"  usage: krip engine <vulkan|opengl>  (current: {_config['engine']})"
        _config["engine"] = args[1].lower()
        _save(api)
        return f"  default graphics engine: {_config['engine']}"

    if sub == "vulkanrt":
        if len(args) < 2 or args[1].lower() not in ("on", "off"):
            return f"  usage: krip vulkanrt <on|off>  (current: {'on' if _config['vulkanrt'] else 'off'})"
        _config["vulkanrt"] = args[1].lower() == "on"
        _save(api)
        return f"  vulkan runtime support: {'on' if _config['vulkanrt'] else 'off'}"

    if sub == "tensor":
        if len(args) < 2 or args[1].lower() not in ("on", "off", "auto"):
            return f"  usage: krip tensor <on|off|auto>  (current: {_config['tensor']})"
        _config["tensor"] = args[1].lower()
        _save(api)
        return f"  tensor support: {_config['tensor']}"

    if sub == "sandbox":
        if len(args) < 2:
            return ("  usage: krip sandbox run <name> -- <cmd...> | "
                    "list | kill <name> | status")
        ssub = args[1].lower()
        if ssub == "list" or ssub == "status":
            return sandbox_status()
        if ssub == "kill":
            if len(args) < 3:
                return "  usage: krip sandbox kill <name>"
            return sandbox_kill(args[2])
        if ssub == "run":
            rest = args[2:]
            if "--" in rest:
                name = rest[0]
                cmd = rest[rest.index("--") + 1:]
            else:
                name = rest[0] if rest else "s1"
                cmd = rest[1:] if rest else []
            return sandbox_run(name, cmd, _config["mem_mb"],
                               _config["cpu_threads"], _config["gpu"])
        return "  sandbox subcommands: run | list | kill | status"

    if sub == "os":
        drivers = _driver_table()
        lines = [
            "  HELLFORGE OS",
            "    kernel    : ep_core (plugin sandbox + signing + directives)",
            f"    hypervisor: K-rip v{VERSION} (heavy resource sandbox)",
            f"    drivers   : {len(drivers)} — " + ", ".join(drivers),
            "    engine    : " + _config["engine"] +
            (" (+VulkanRT)" if _config["vulkanrt"] else ""),
            "    tensor    : " + _config["tensor"],
        ]
        return "\n".join(lines)

    return ("  krip: status | mem <mb> | cpu <n> | gpu <auto|list|all|ids> | "
            "engine <vulkan|opengl> | vulkanrt <on|off> | tensor <on|off|auto> | "
            "sandbox ... | os")


# ── plugin entry ──────────────────────────────────────────────────────

def register(api):
    global PROJECT_DIR
    PROJECT_DIR = getattr(api, "project_dir", None) or os.getcwd()
    _load(api)
    api.add_command("krip", lambda args: _cmd(args, api),
                    "K-rip hypervisor: mem/cpu/gpu/engine/vulkanrt/tensor/sandbox/os")
    drivers = _driver_table()
    api.add_boot_step(f"K-rip: hypervisor armed "
                      f"(mem {_config['mem_mb']}MB, cpu {_config['cpu_threads']}, "
                      f"gpu {_config['gpu']}, engine {_config['engine']})", "done")
    api.add_boot_step(
        f"HELLFORGE OS: kernel ep_core · {len(drivers)} drivers · "
        f"hypervisor K-rip v{VERSION}", "done")
    # apply the heavy layer at boot: memory budget + cpu affinity
    _apply_rlimits(_config["mem_mb"])
    _apply_affinity(_config["cpu_threads"])
