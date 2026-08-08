"""HELLFORGE launch helper — per-OS subprocess flags, detach logging.
Used by eshell (play/run/compile --window/--detach) and plugins."""

import os
import sys
import subprocess
import time

LOG_DIR = None  # set by caller


def set_log_dir(path):
    global LOG_DIR
    LOG_DIR = path


def get_creation_flags(window=False, detach=False):
    """Return OS-appropriate creation flags for subprocess.Popen."""
    if os.name != "nt":
        return 0
    flags = 0
    if window:
        flags |= getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
        flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    elif detach:
        flags |= getattr(subprocess, "DETACHED_PROCESS", 0)
        flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return flags


def launch(cmd, window=False, detach=False, cwd=None, env=None):
    """Launch a subprocess.
    window=True  → dedicated console window
    detach=True  → background with log file (returns immediately)
    Neither      → blocking subprocess.run (captured)
    Returns (proc_or_None, log_path_or_None)."""
    import os as _os
    cwd = cwd or _os.getcwd()
    flags = get_creation_flags(window, detach)

    log_path = None
    if detach:
        log_dir = LOG_DIR or _os.path.join(cwd, "logs")
        _os.makedirs(log_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        name = _os.path.basename(cmd[-1]) if cmd else "run"
        log_path = _os.path.join(log_dir, f"run_{ts}_{name}.log")
        log_file = open(log_path, "w", encoding="utf-8")
        proc = subprocess.Popen(
            cmd, cwd=cwd, env=env, creationflags=flags,
            stdin=subprocess.DEVNULL, stdout=log_file, stderr=subprocess.STDOUT,
            start_new_session=(_os.name != "nt"),
        )
        return proc, log_path

    if window:
        return subprocess.Popen(cmd, cwd=cwd, env=env, creationflags=flags), None

    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=7200)
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    return None, None


def open_with_default(path):
    """Open a file with the OS default application."""
    path = os.path.abspath(path)
    if os.name == "nt":
        os.startfile(path)  # noqa
        return True
    if sys.platform == "darwin":
        subprocess.Popen(["open", path])
        return True
    subprocess.Popen(["xdg-open", path])
    return True


def list_hellforge_processes():
    """List running HELLFORGE processes (player.py, ep.py, eshell.py, run.py).
    Returns list of dicts with pid and cmdline."""
    procs = []
    if os.name == "nt":
        try:
            out = subprocess.run(
                ["wmic", "process", "where", "name='python.exe'",
                 "get", "ProcessId,CommandLine", "/format:csv"],
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
            )
            for line in out.stdout.split("\n"):
                if any(m in line for m in ("player.py", "ep.py", "eshell.py", "run.py")):
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 2:
                        try:
                            procs.append({"pid": int(parts[-1]), "cmdline": ",".join(parts[1:-1])})
                        except ValueError:
                            pass
        except Exception:
            pass
        return procs
    try:
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        for line in out.stdout.split("\n"):
            if any(m in line for m in ("player.py", "ep.py", "eshell.py", "run.py")):
                parts = line.strip().split(None, 1)
                if len(parts) == 2:
                    try:
                        procs.append({"pid": int(parts[0]), "cmdline": parts[1]})
                    except ValueError:
                        pass
    except Exception:
        pass
    return procs


def kill_process(pid):
    """Terminate a process by PID. Returns True on success."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=10)
        else:
            os.kill(pid, 9)
        return True
    except Exception:
        return False
