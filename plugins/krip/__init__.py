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
import time

VERSION = "1.0.0"
author = "Tentari"
description = "Hypervisor layer — heavy sandboxing, memory/CPU/GPU allocation, graphics engine default, VulkanRT + Tensor"

_lock = threading.Lock()
_sandboxes = {}       # name -> Popen
CONFIG_FILE_NAME = "krip.json"  # at the project root — the real config file
_config = {
    "mem_mb": 0,          # 0 = unlimited
    "cpu_threads": 0,     # 0 = all
    "gpu": "auto",        # auto | list | all | "0,1" (multi-GPU)
    "engine": "vulkan",   # vulkan (default) | opengl
    "vulkanrt": False,
    "tensor": "auto",     # on | off | auto
}

PROJECT_DIR = None
_last_api = None


# ── helpers ───────────────────────────────────────────────────────────

def _cfg(api, key, default):
    try:
        v = api.get_config(key)
        return default if v is None else v
    except Exception:
        return default


def _config_path():
    return os.path.join(PROJECT_DIR or os.getcwd(), CONFIG_FILE_NAME)


def load_config_file():
    """Read krip.json (the real config file). Returns {} when missing."""
    try:
        with open(_config_path()) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config_file():
    """Persist the current allocation to krip.json."""
    data = {
        "version": 1,
        "mem_mb": _config["mem_mb"],
        "cpu_threads": _config["cpu_threads"],
        "gpu": _config["gpu"],
        "engine": _config["engine"],
        "vulkanrt": _config["vulkanrt"],
        "tensor": _config["tensor"],
        "sandboxes": {},
    }
    try:
        with open(_config_path(), "w") as f:
            json.dump(data, f, indent=2)
        return _config_path()
    except Exception as e:
        return f"error: {e}"


def _save(api):
    try:
        for k, v in _config.items():
            api.set_config(f"krip_{k}", v)
    except Exception:
        pass


_DEFAULTS = {"mem_mb": 0, "cpu_threads": 0, "gpu": "auto",
             "engine": "vulkan", "vulkanrt": False, "tensor": "auto"}


def _load(api):
    """Initialization: built-in defaults, then krip.json (the real config
    file) wins, then runtime-saved state."""
    _config.update(_DEFAULTS)
    file_cfg = load_config_file()
    for k in _config:
        if k in file_cfg and file_cfg[k] is not None:
            _config[k] = file_cfg[k]
        else:
            _config[k] = _cfg(api, f"krip_{k}", _config[k])


def _apply_rlimits(mem_mb):
    """Apply the memory budget to the CURRENT process (RLIMIT_AS)."""
    if mem_mb <= 0:
        return "unlimited"
    try:
        import resource
        limit = mem_mb * 1024 * 1024
        # soft-only: the hard limit stays infinite so it can be raised back
        resource.setrlimit(resource.RLIMIT_AS, (limit, resource.RLIM_INFINITY))
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


def _edit_config(stream_out=print, input_fn=input):
    """Open krip.json in nano; AUTO-RELOAD the config the moment it is
    saved (a watcher polls the file and re-applies memory/cpu/engine/gpu
    live while the editor is open)."""
    path = _config_path()
    if not os.path.isfile(path):
        save_config_file()
    editor = os.environ.get("KRIP_EDITOR") or "nano"
    editor_cmd = shlex.split(editor)
    stream_out(f"  editing {path} with {editor} — saving the file "
               "auto-reloads K-rip live")
    stopped = threading.Event()

    def watch():
        last = None
        try:
            last = os.path.getmtime(path)
        except Exception:
            pass
        while not stopped.is_set():
            time.sleep(0.8)
            try:
                m = os.path.getmtime(path)
            except Exception:
                continue
            if m != last:
                last = m
                try:
                    _load(_last_api)
                    _save(_last_api)
                    _apply_rlimits(_config["mem_mb"])
                    _apply_affinity(_config["cpu_threads"])
                    stream_out(f"  [krip] krip.json saved — reloaded live "
                               f"(mem {_config['mem_mb']}MB, cpu "
                               f"{_config['cpu_threads']}, gpu {_config['gpu']}, "
                               f"engine {_config['engine']})")
                except Exception as e:
                    stream_out(f"  reload error: {e}")

    import time as _t
    th = threading.Thread(target=watch, daemon=True)
    th.start()
    try:
        code = subprocess.call(editor_cmd + [path])
        if code != 0:
            stream_out(f"  editor exited with {code}")
    finally:
        stopped.set()
        th.join(timeout=1)
    _load(_last_api)
    _save(_last_api)
    _apply_rlimits(_config["mem_mb"])
    _apply_affinity(_config["cpu_threads"])
    return f"  config edit done — applied from {path}"


# ── the krip command ──────────────────────────────────────────────────

def _cmd(args, api=None):
    global PROJECT_DIR, _last_api
    if api is not None:
        PROJECT_DIR = getattr(api, "project_dir", None) or PROJECT_DIR
        _last_api = api
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

    if sub == "edit":
        return _edit_config(stream_out=print, input_fn=input)

    if sub == "boot":
        from . import boot_menu
        result = boot_menu()
        if result[0] == "boot":
            boot_entry(result[1])
        return "  boot menu finished (console)"

    if sub == "kernels":
        entries = load_kernels()
        if not entries:
            return "  no kernels registered"
        lines = ["  HELLFORGE OS — installed kernels:"]
        for e in entries:
            cur = " *" if e.get("current") else ""
            lines.append(f"    {e['id']:<18} v{e.get('version', '?')}"
                         f"  [{e.get('mode', 'normal')}]{cur}")
        return "\n".join(lines)

    if sub == "config":
        lines = [
            f"  krip config file: {_config_path()}",
            "    " + json.dumps({k: _config[k] for k in (
                "mem_mb", "cpu_threads", "gpu", "engine",
                "vulkanrt", "tensor")}, indent=4).replace("\n", "\n    "),
        ]
        return "\n".join(lines)

    if sub == "save":
        path = save_config_file()
        return f"  krip config saved: {path}"

    if sub == "reload":
        _load(api)
        _save(api)
        _apply_rlimits(_config["mem_mb"])
        _apply_affinity(_config["cpu_threads"])
        return ("  krip config reloaded from " + _config_path() +
                "\n" + _cmd(["status"], api))

    if sub == "reset":
        _config.update(_DEFAULTS)
        _save(api)
        save_config_file()
        return "  krip config reset to defaults (saved)"

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




# ──────────────────────────────────────────────────────────────────────
# K-rip boot manager — GRUB-like kernel menu for HELLFORGE OS.
# Entries: ep_core (normal/safemode) for the current kernel and the
# previous kernel versions (rolled forward on every update). 3-second
# countdown auto-boots the default; any key stops it; arrow up/down
# selects; Enter boots; Ctrl+C drops to the console.
# ──────────────────────────────────────────────────────────────────────

def _kernels_path():
    return os.path.join(PROJECT_DIR or os.getcwd(), ".e_identity", "kernels.json")


def _dedup_kernels(entries):
    """One pair (normal + safemode) per version, newest first."""
    by_ver = {}
    for e in entries:
        key = e.get("version", "?")
        by_ver.setdefault(key, {})
        by_ver[key][e.get("mode", "normal")] = e
    out = []
    for ver in sorted(by_ver, reverse=True):
        pair = by_ver[ver]
        for mode in ("normal", "safemode"):
            if mode in pair:
                out.append(pair[mode])
    return out


def load_kernels():
    """Kernel registry: list of entry dicts (deduped, newest first)."""
    try:
        with open(_kernels_path()) as f:
            data = json.load(f)
        entries = data.get("entries", [])
        return _dedup_kernels(entries) if isinstance(entries, list) else []
    except Exception:
        return []


def _save_kernels(entries):
    try:
        os.makedirs(os.path.dirname(_kernels_path()), exist_ok=True)
        with open(_kernels_path(), "w") as f:
            json.dump({"entries": entries}, f, indent=2)
    except Exception:
        pass


def _kernel_meta():
    """Version + details for the current kernel."""
    ver = "dev"
    try:
        from ep_compiler.security_hash import local_version
        ver = local_version().lstrip("v")
    except Exception:
        pass
    model = "(none)"
    try:
        import json as _j
        cfg = _j.load(open(os.path.join(PROJECT_DIR or os.getcwd(),
                                        ".plugin_config.json")))
        model = cfg.get("llm_model") or cfg.get("llm_agent_model") or "(none)"
    except Exception:
        pass
    return ver, model


def _prev_tag(ver):
    """The release tag immediately before ver (git tags, version-sorted)."""
    try:
        import subprocess as _sp
        r = _sp.run(["git", "tag", "--sort=-version:refname"],
                    capture_output=True, text=True, timeout=5,
                    cwd=PROJECT_DIR or os.getcwd())
        tags = [t.strip() for t in r.stdout.splitlines()
                if t.strip().startswith("v")]
        base = ver if ver.startswith("v") else "v" + ver
        seen = False
        for t in tags:
            if t == base:
                seen = True
                continue
            if seen:
                return t
    except Exception:
        pass
    return None


def record_current_kernel():
    """Ensure the current version is registered (normal + safemode entries).
    If the version changed, the old current becomes a previous kernel."""
    ver, model = _kernel_meta()
    entries = load_kernels()
    import time as _t
    stamp = _t.strftime("%Y-%m-%d %H:%M")
    # guarantee the true previous release is registered (from git tags), so
    # the menu always shows current + the actual prior kernel — even when
    # the current version was already registered on an earlier boot
    prev = _prev_tag(ver)
    if prev and not any(e.get("version") == prev.lstrip("v") for e in entries):
        pv = prev.lstrip("v")
        entries.append({"id": "ep_core", "version": pv, "mode": "normal",
                        "tag": prev, "current": False, "when": stamp,
                        "model": model, "detail": "HELLFORGE OS kernel — previous"})
        entries.append({"id": "ep_core:safemode", "version": pv, "mode": "safemode",
                        "tag": prev, "current": False, "when": stamp,
                        "model": model, "detail": "HELLFORGE OS kernel — previous (safe)"})
    current = [e for e in entries if e.get("current")]
    if any(e.get("version") == ver and e.get("mode") == "normal" for e in current):
        _save_kernels(entries)
        return entries
    # version changed -> demote old current to previous
    for e in entries:
        if e.get("current"):
            e["current"] = False
    # one pair per version: drop stale entries of this version
    entries = [e for e in entries if e.get("version") != ver]
    entries.append({"id": "ep_core", "version": ver, "mode": "normal",
                    "tag": f"v{ver}" if not ver.startswith("v") else ver,
                    "current": True, "when": stamp, "model": model,
                    "detail": "HELLFORGE OS kernel"})
    entries.append({"id": "ep_core:safemode", "version": ver, "mode": "safemode",
                    "tag": f"v{ver}" if not ver.startswith("v") else ver,
                    "current": True, "when": stamp, "model": model,
                    "detail": "HELLFORGE OS kernel — safe mode"})
    _save_kernels(entries)
    return entries


def snapshot_previous_kernel():
    """Called by the updater BEFORE switching versions: the current kernel
    becomes a bootable previous entry (rollback target). The current entry
    stays current — demotion happens in record_current_kernel once the
    version actually changes."""
    ver, model = _kernel_meta()
    entries = load_kernels()
    modes = [e.get("mode") for e in entries
             if e.get("version") == ver and not e.get("current")]
    if "normal" in modes and "safemode" in modes:
        return entries
    # drop stale same-version entries so each version keeps one pair
    entries = [e for e in entries if e.get("version") != ver or e.get("current")]
    import time as _t
    stamp = _t.strftime("%Y-%m-%d %H:%M")
    if "normal" not in modes:
        entries.append({"id": "ep_core", "version": ver, "mode": "normal",
                        "tag": f"v{ver}" if not ver.startswith("v") else ver,
                        "current": False, "when": stamp, "model": model,
                        "detail": "HELLFORGE OS kernel — previous"})
    if "safemode" not in modes:
        entries.append({"id": "ep_core:safemode", "version": ver, "mode": "safemode",
                        "tag": f"v{ver}" if not ver.startswith("v") else ver,
                        "current": False, "when": stamp, "model": model,
                        "detail": "HELLFORGE OS kernel — previous (safe)"})
    _save_kernels(entries)
    return entries


def boot_entry(entry, stream_out=print):
    """Boot a kernel entry. Returns exit code."""
    from ep_compiler import security_hash as SH
    ver, _m = _kernel_meta()
    if entry.get("version") != ver and entry.get("tag"):
        stream_out(f"  booting previous kernel {entry['tag']} "
                   "(safe update — nothing lost)...")
        from ep_compiler.update import safe_update
        code = safe_update(entry["tag"], stream_out=stream_out)
        if code != 0:
            stream_out("  failed to boot previous kernel")
            return code
    if entry.get("mode") == "safemode":
        stream_out("  entering SAFE MODE")
        from ep_compiler.safemode import enter_safemode
        enter_safemode("manual — kernel " + entry.get("version", ""),
                       "user selected ep_core:safemode", stream_out)
    return 0


_S = {
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "cyan": "\033[36m",
    "white": "\033[37m",
    "sel": "\033[1;37;44m",      # selected entry: white on blue
    "bar": "\033[1;30;46m",      # footer bar: black on cyan
    "hdr": "\033[1;36;44m",      # header band: bold cyan on blue
}


def _banner():
    """HELLFORGE OS banner."""
    return (
        "\n"
        "   ██░ ██ ███████  ██▓     ██▓     ▄████▄  ██████  ▄████▄  ███████ ███████\n"
        "  ▓██░ ██▒██  ██  ▓██▒    ▓██▒    ▒██▀ ▀█ ▒██    ▒ ▒██▀ ▀█ ██     ██  ██\n"
        "  ▒██▀▀██░██ ░██  ▒██░    ▒██░    ▒▓█    ▄░ ▓██▄   ▒▓█    ▄▒██████ ██  ██\n"
        "  ░▓█ ░██ ██ ░██  ▒██░    ▒██░    ▒▓▓▄ ▄██▒ ▒   ██▒▒▓▓▄ ▄██░▓█  ██ ██  ██\n"
        "  ░▓█▒░██▓███████ ░██████▒░██████▒▒ ▓███▀ ░▒██████▒▒▒ ▓███▀ ▒██████ ███████\n"
        "   ▒ ░░▒░▒░ ▒░▓  ░ ░ ▒░▓  ░ ░ ▒░▓  ░░ ░▒ ▒  ░░ ▒░▓  ░  ░ ▒ ▒  ░ ▒░▓  ░░ ▒░▓  ░\n"
        "   ▒ ░▒░ ░░ ░ ▒  ░ ░ ░ ▒  ░ ░ ░ ▒  ░  ░  ▒   ░ ▒ ▒░  ░ ░ ▒   ░ ▒ ▒░  ░ ▒  ░\n"
        "   ░  ░░ ░  ░ ░     ░ ░     ░ ░    ░        ░ ░ ░ ▒   ░ ░ ░ ░   ░ ░ ▒    ░ ░\n"
        "   ░  ░  ░    ░  ░    ░  ░    ░  ░  ░ ░      ░ ░   ░  ░   ░ ░ ░    ░  ░   ░  ░\n"
    )


def _draw_menu(entries, sel, countdown, stream_out, new_ver=None):
    """Styled GRUB-like frame: banner, highlight-bar selection, footer bar."""
    S = _S
    lines = []
    lines.append(S["hdr"] + "  HELLFORGE OS — K-rip boot manager  " + S["reset"])
    lines.append(_banner().rstrip("\n"))
    w = max((len(f"  {e['id']} v{e.get('version', '?')} [{e.get('mode', 'normal')}]"
             + (f"  · {e['when']}" if e.get("when") else "")) for e in entries), default=40)
    for i, e in enumerate(entries):
        mode = e.get("mode", "normal")
        chip = (S["green"] + "[normal]" + S["reset"] if mode == "normal"
                else S["yellow"] + "[safemode]" + S["reset"])
        when = f"  · {e['when']}" if e.get("when") else ""
        base = f"{e['id']}  v{e.get('version', '?')}  {chip}{when}"
        pad = " " * max(1, w - len(base))
        if i == sel:
            lines.append(S["sel"] + "  ▸ " + base + pad + "  " + S["reset"])
        else:
            lines.append(S["dim"] + "    " + base + pad + S["reset"])
    lines.append("")
    if countdown is not None:
        lines.append(S["yellow"] + f"  booting {entries[sel]['id']} in "
                     f"{countdown:.2f}s — press any key to interrupt" + S["reset"])
    if new_ver:
        lines.append(S["red"] + f"  NEW KERNEL AVAILABLE: {new_ver} — "
                     "press u to update (nothing is lost)" + S["reset"])
    lines.append("")
    lines.append(S["bar"] + "  ↑/↓ select   Enter boot   c console   "
                 "u update   g game   Esc exit   Ctrl+C console  " + S["reset"])
    stream_out("\n".join(lines))


def _read_key_raw(timeout):
    """Blocking key read with timeout (termios raw + os.read — buffered
    stdin breaks arrow keys). Returns key name or None."""
    import select
    import termios
    import tty
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        r, _, _ = select.select([fd], [], [], timeout)
        if not r:
            return None
        ch = os.read(fd, 1)
        if ch == b"\x1b":
            r2, _, _ = select.select([fd], [], [], 0.05)
            if r2:
                seq = os.read(fd, 2)
                if seq == b"[A":
                    return "up"
                if seq == b"[B":
                    return "down"
            return "escape"
        if ch in (b"\x03", b"\x1a"):
            return "ctrl-c"
        if ch in (b"\r", b"\n"):
            return "enter"
        if ch.lower() == b"c":
            return "console"
        return "key"
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def boot_menu(stream_out=print, input_fn=input, timeout=3.0, interactive=None):
    """GRUB-like menu. Returns ("boot", entry) or ("console", None)."""
    record_current_kernel()
    entries = load_kernels()
    if not entries:
        record_current_kernel()
        entries = load_kernels()
    if not entries:
        return "console", None
    sel = 0
    for i, e in enumerate(entries):
        if e.get("current") and e.get("mode") == "normal":
            sel = i
            break
    if interactive is None:
        interactive = sys.stdin.isatty()

    # only the present kernel and the one before it
    vers = []
    for e in entries:
        if e["version"] not in vers:
            vers.append(e["version"])
        if len(vers) == 2:
            break
    entries = [e for e in entries if e["version"] in vers]
    sel = 0
    for i, e in enumerate(entries):
        if e.get("current") and e.get("mode") == "normal":
            sel = i
            break

    # new version available? (checked once, cached for the frame)
    new_ver = None
    local_ver = None
    try:
        from ep_compiler.security_hash import remote_version, local_version
        local_ver = local_version()
        rv = remote_version(timeout=4)
        if rv and rv != local_ver:
            new_ver = rv
    except Exception:
        pass

    if not interactive:
        _draw_menu(entries, sel, None, stream_out, new_ver=new_ver)
        stream_out("  (non-interactive — Enter to boot the default, "
                   "'console' for console, 'update' to update, "
                   "or an entry number)")
        raw = input_fn("boot> ").strip().lower()
        if raw == "console":
            return "console", None
        if raw == "game":
            os.environ["KRIP_BOOT_CMD"] = "ninja"
            return "boot", entries[sel]
        if raw == "update":
            if new_ver:
                return "update", new_ver
            return "boot", entries[sel]
        if raw.isdigit():
            i = int(raw)
            if 0 <= i < len(entries):
                return "boot", entries[i]
        return "boot", entries[sel]
        stream_out("  (non-interactive — Enter to boot the default, "
                   "'console' for console, or an entry number)")
        raw = input_fn("boot> ").strip().lower()
        if raw == "console":
            return "console", None
        if raw.isdigit():
            i = int(raw)
            if 0 <= i < len(entries):
                return "boot", entries[i]
        return "boot", entries[sel]

    # single-frame redraw: clear the screen before every frame so the menu
    # updates in place like a real bootloader (no stacked copies)
    clear = "\033[2J\033[H"

    countdown = timeout
    stopped = False
    while True:
        stream_out(clear)
        _draw_menu(entries, sel, None if stopped else countdown, stream_out,
                   new_ver=new_ver)
        if not stopped and countdown is not None:
            key = _read_key_raw(0.25)
            if key is None:
                countdown -= 0.25
                if countdown <= 0:
                    stream_out(clear)
                    _draw_menu(entries, sel, None, stream_out, new_ver=new_ver)
                    return "boot", entries[sel]
                continue
            stopped = True
        else:
            key = _read_key_raw(None)
        if key == "u" and new_ver:
            stream_out(f"\n  → updating to {new_ver}...")
            return "update", new_ver
        if key == "up":
            sel = (sel - 1) % len(entries)
        elif key == "down":
            sel = (sel + 1) % len(entries)
        elif key == "g":
            os.environ["KRIP_BOOT_CMD"] = "ninja"
            stream_out("\n  → ninja game (weather on)")
            return "boot", entries[sel]
        elif key == "enter":
            return "boot", entries[sel]
        elif key in ("ctrl-c", "console"):
            stream_out("\n  → console")
            return "console", None
        elif key == "escape":
            stream_out("\n  → krip exited — back to the terminal")
            return "exit", None



# ──────────────────────────────────────────────────────────────────────
# K-rip is THE main thing: every launch path re-enters through here.
#   krip                  GRUB menu -> boot kernel -> console (eshell)
#   krip run <cmd...>     run anything inside the sandbox
#   krip eshell|shell     the OS console inside the sandbox
#   krip hellgate         HellGate inside the sandbox
#   krip player <file>    the player inside the sandbox
#   krip status|help
# Children get KRIP_INNER=1 (no re-wrap), the GPU/engine/tensor env, the
# memory budget, cpu affinity and project-root confinement.
# ──────────────────────────────────────────────────────────────────────

def _spawn(cmd, name="default", stream_out=print):
    """THE krip sandbox spawn: every child of the OS runs through this."""
    if not cmd:
        return 1
    base = dict(os.environ)
    base.update(_gpu_env(_config["gpu"]))
    base["KRIP_INNER"] = "1"
    base["KRIP_SANDBOX"] = name
    base["KRIP_ENGINE"] = _config["engine"]
    base["KRIP_VULKANRT"] = "1" if _config["vulkanrt"] else "0"
    base["KRIP_TENSOR"] = _config["tensor"]
    stream_out(f"  [krip] sandbox '{name}': mem {_config['mem_mb']}MB, "
               f"cpu {_config['cpu_threads']}, gpu {_config['gpu']}, "
               f"engine {_config['engine']}")
    try:
        p = subprocess.Popen(cmd, cwd=PROJECT_DIR or os.getcwd(), env=base,
                             preexec_fn=_preexec_limits(_config["mem_mb"],
                                                        _config["cpu_threads"], 0))
    except Exception as e:
        stream_out(f"  [krip] failed to launch: {e}")
        return 1
    try:
        return p.wait()
    except KeyboardInterrupt:
        p.terminate()
        try:
            p.wait(timeout=5)
        except Exception:
            p.kill()
        return 130


def _run_update(tag, stream_out=print):
    """Safe update with an animated progress bar. Nothing is lost."""
    done = threading.Event()

    def animate():
        bar = "█"
        width = 40
        cur = 0
        while not done.is_set():
            stream_out("\r  [%s] %3d%%" % (bar * (cur * width // 100) +
                       "░" * (width - cur * width // 100), cur), end="",
                       flush=True)
            time.sleep(0.15)
        stream_out("\r  [%s] %3d%%" % (bar * width, 100), flush=True)
        stream_out("")

    th = threading.Thread(target=animate, daemon=True)
    th.start()
    try:
        from ep_compiler.update import safe_update
        code = safe_update(tag, progress=lambda n: None,
                           stream_out=stream_out)
    except Exception as e:
        code = 1
        stream_out(f"\n  update error: {e}")
    finally:
        done.set()
        th.join(timeout=1)
    stream_out("")
    return code


def _spawn_eshell(stream_out=print):
    path = os.path.join(PROJECT_DIR or os.getcwd(), "eshell.py")
    return _spawn([sys.executable, path], name="console", stream_out=stream_out)


def _exec_eshell(stream_out=print):
    """Become the OS console in-place: same TTY, one boot, no child
    process. krip keeps no console surface of its own — the sandbox
    configuration is not editable from inside the machine."""
    path = os.path.join(PROJECT_DIR or os.getcwd(), "eshell.py")
    os.environ["KRIP_INNER"] = "1"
    os.environ["KRIP_NO_MENU"] = "1"
    try:
        os.execv(sys.executable, [sys.executable, path])
    except Exception as e:
        stream_out(f"  krip: failed to enter console ({e})")
        return 1
    return 0


def hypervisor_entry(argv, stream_out=print, input_fn=input):
    """The hypervisor entry — krip launches everything else."""
    record_current_kernel()
    if not argv:
        # GRUB menu -> boot / update / exit -> the console
        # (KRIP_NO_MENU=1 boots straight to the console)
        if os.environ.get("KRIP_NO_MENU") != "1":
            for _round in range(4):  # a few update rounds, then boot
                r = boot_menu(stream_out, input_fn)
                if r[0] == "boot":
                    boot_entry(r[1], stream_out)
                    break
                if r[0] == "exit":
                    stream_out("  krip exited — back to the terminal")
                    return 0
                if r[0] == "update":
                    rc = _run_update(r[1], stream_out)
                    if rc != 0:
                        stream_out("  update failed — staying on the menu")
                    else:
                        stream_out("  update complete — kernels refreshed")
                    continue  # re-show the menu with the new kernel
                if r[0] == "console":
                    # the console IS the OS shell — become it in-place
                    # (no sandbox re-spawn, no extra boot layer; krip itself
                    # stays locked: no config/mutation surface from inside)
                    return _exec_eshell(stream_out)
                break
        return _spawn_eshell(stream_out)
    a = argv[0].lower()
    if a in ("run", "exec"):
        if len(argv) < 2:
            stream_out("  usage: krip run <cmd...>")
            return 1
        return _spawn(argv[1:], name="cmd", stream_out=stream_out)
    if a in ("eshell", "shell", "console"):
        return _exec_eshell(stream_out)
    if a in ("game", "ninja"):
        os.environ["KRIP_BOOT_CMD"] = "ninja"
        return _exec_eshell(stream_out)
    if a in ("hellgate", "gate", "hg"):
        run_py = os.path.join(PROJECT_DIR or os.getcwd(), "run.py")
        return _spawn([sys.executable, run_py, "hellgate"], name="hellgate",
                      stream_out=stream_out)
    if a in ("player", "play", "gui"):
        run_py = os.path.join(PROJECT_DIR or os.getcwd(), "run.py")
        return _spawn([sys.executable, run_py, "play"] + argv[1:],
                      name="player", stream_out=stream_out)
    if a in ("status", "info"):
        stream_out(_cmd(["status"]))
        return 0
    if a in ("help", "-h", "--help"):
        stream_out("  krip [run <cmd...>] [eshell|shell] [hellgate] "
                   "[player <file>] [status] [help]")
        return 0
    stream_out(f"  unknown: {a} — try 'krip help'")
    return 1

# ── plugin entry ──────────────────────────────────────────────────────

def register(api):
    global PROJECT_DIR
    PROJECT_DIR = getattr(api, "project_dir", None) or os.getcwd()
    _load(api)
    api.add_command("krip", lambda args: _cmd(args, api),
                    "K-rip hypervisor: mem/cpu/gpu/engine/vulkanrt/tensor/sandbox/os")
    record_current_kernel()
    drivers = _driver_table()
    api.add_boot_step(f"K-rip: hypervisor armed from {CONFIG_FILE_NAME} "
                      f"(mem {_config['mem_mb']}MB, cpu {_config['cpu_threads']}, "
                      f"gpu {_config['gpu']}, engine {_config['engine']})", "done")
    api.add_boot_step(
        f"HELLFORGE OS: kernel ep_core · {len(drivers)} drivers · "
        f"hypervisor K-rip v{VERSION}", "done")
    # apply the heavy layer at boot: memory budget + cpu affinity
    _apply_rlimits(_config["mem_mb"])
    _apply_affinity(_config["cpu_threads"])
