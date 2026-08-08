"""Safe command execution for the copilot agent — the model may request
commands, but only harmless ones: simple executables with arguments, run
inside the project root, with a timeout and capped output. Destructive
commands, shell metacharacters and anything that escapes the project are
rejected before execution."""

import re
import shlex
import subprocess
import sys
import time

FORBIDDEN = {
    "rm", "rmdir", "unlink", "del", "erase", "trash", "mv", "move",
    "shutdown", "reboot", "poweroff", "mkfs", "format", "dd", "fdisk",
    "chmod", "chown", "mount", "umount", "sudo", "su", "passwd",
    "curl", "wget", "nc", "ncat", "telnet", "scp", "sftp", "rsync",
    # "git" is allowlisted per-subcommand below
}
FORBIDDEN_GIT = {"push", "pull", "fetch", "clone", "reset", "rebase",
                 "merge", "checkout", "switch", "clean", "gc", "prune",
                 "remote", "submodule", "filter-branch"}
FORBIDDEN_PY = {"os", "os.system", "sys", "subprocess", "eval", "exec",
                "open", "shutil", "pathlib", "glob", "shlex", "ctypes",
                "socket", "http", "ftplib", "telnetlib", "pickle", "marshal"}
METACHARS = re.compile(r'[;&|`$()<>]')
DOTDOT = re.compile(r'(^|\s)\.\.(\s|$)|\.\./')
MAX_OUTPUT = 4000
TIMEOUT = 30


def validate_command(cmd):
    """Validate a command string. Returns (ok, reason)."""
    if not cmd or not cmd.strip():
        return False, "empty command"
    if METACHARS.search(cmd):
        return False, "shell metacharacters not allowed (;, &, |, `, $(), <, >)"
    if DOTDOT.search(cmd):
        return False, "'..' not allowed — commands stay inside the project"
    try:
        parts = shlex.split(cmd)
    except ValueError as e:
        return False, f"bad quoting: {e}"
    if not parts:
        return False, "empty command"
    prog = parts[0]
    if prog in FORBIDDEN:
        return False, f"'{prog}' is not allowed (destructive/system-level)"
    if prog == "git":
        if len(parts) < 2 or parts[1] in FORBIDDEN_GIT:
            return False, f"'git {parts[1] if len(parts) > 1 else ''}' is not allowed"
    if prog == "python" or prog.endswith("python3") or prog == "py":
        if len(parts) >= 2:
            arg1 = parts[1]
            if arg1 == "-c":
                return False, "python -c (inline code) not allowed"
            if arg1 == "-m" and len(parts) >= 3:
                mod = parts[2]
                if mod.split(".")[0] in FORBIDDEN_PY or mod in ("this", "antigravity"):
                    return False, f"python -m {mod} not allowed"
            if arg1 in FORBIDDEN_PY:
                return False, f"python {arg1} not allowed"
    if prog == "pip":
        return False, "'pip' is not allowed (use 'ai plugin' instead)"
    return True, None


def run_command(cmd, project_dir, timeout=TIMEOUT):
    """Execute a validated command inside project_dir.
    Returns dict: {ok, output, exit_code, duration_s, error}."""
    ok, reason = validate_command(cmd)
    if not ok:
        return {"ok": False, "output": "", "exit_code": None,
                "duration_s": 0.0, "error": reason, "blocked": True}
    parts = shlex.split(cmd)
    t0 = time.time()
    try:
        r = subprocess.run(parts, cwd=project_dir, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        out = (r.stdout or "") + (r.stderr or "")
        if len(out) > MAX_OUTPUT:
            out = out[:MAX_OUTPUT] + f"\n... (output truncated at {MAX_OUTPUT} chars)"
        return {"ok": r.returncode == 0, "output": out.strip(),
                "exit_code": r.returncode,
                "duration_s": round(time.time() - t0, 2), "error": None,
                "blocked": False}
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": "", "exit_code": None,
                "duration_s": timeout, "error": f"timed out after {timeout}s",
                "blocked": False}
    except FileNotFoundError:
        return {"ok": False, "output": "", "exit_code": None,
                "duration_s": round(time.time() - t0, 2),
                "error": f"command not found: {parts[0]}", "blocked": False}
    except Exception as e:
        return {"ok": False, "output": "", "exit_code": None,
                "duration_s": round(time.time() - t0, 2), "error": str(e),
                "blocked": False}


def chat_line(result):
    """One-line chat summary: 'command executed - "cmd" (ok, 0.1s)'."""
    if result.get("blocked"):
        return f"command blocked - \"{result.get('error', '')}\""
    status = "ok" if result.get("ok") else f"exit {result.get('exit_code')}"
    return (f"command executed - \"{result.get('cmd', '')}\" "
            f"({status}, {result.get('duration_s', 0)}s)")
