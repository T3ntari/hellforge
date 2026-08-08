"""LAUNCHER v1.0.0 — New window launching & process management for HELLFORGE.
Opens players, compilers, files, and shells in dedicated windows.
Manages running HELLFORGE processes.

Usage: launcher open|player|compile|shell|log|ps|kill

Made by Tentari. Signed: REGAS."""

VERSION = "1.0.0"
author = "Tentari"
description = "New window launching & process management — open, player, shell, log, ps, kill"

import os
import sys
import subprocess
import glob


def register(api):
    api.add_boot_step(f"LAUNCHER v{VERSION}", "loading")
    api.add_command("launcher", _cmd, "LAUNCHER: launcher open|player|compile|shell|log|ps|kill")
    api.add_command("launch", _cmd, "LAUNCHER: alias for launcher")
    try:
        from _launch import set_log_dir
        set_log_dir(os.path.join(api.project_dir, "logs"))
    except Exception:
        pass
    api.add_boot_step("LAUNCHER: window launching ready", "done")


def _cmd(args):
    if not args:
        print(f"  Usage: launcher open <file> | player <f> [--gui] | compile <f> -o <out> | shell | log <name> | ps | kill <pid>")
        return
    sub = args[0]
    rest = args[1:]

    if sub == "open":
        _cmd_open(rest)
    elif sub == "player":
        _cmd_player(rest)
    elif sub == "compile":
        _cmd_compile(rest)
    elif sub == "shell":
        _cmd_shell(rest)
    elif sub == "log":
        _cmd_log(rest)
    elif sub == "ps":
        _cmd_ps()
    elif sub == "kill":
        _cmd_kill(rest)
    else:
        print(f"  Unknown launcher subcommand: {sub}")


def _project_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cmd_open(args):
    if not args:
        print(f"  Usage: launcher open <file>")
        return
    path = os.path.abspath(args[0])
    if not os.path.exists(path):
        print(f"  Not found: {path}")
        return
    try:
        from _launch import open_with_default
        open_with_default(path)
        print(f"  Opened: {path}")
    except Exception as e:
        print(f"  Open error: {e}")


def _cmd_player(args):
    from _launch import launch
    if not args:
        print(f"  Usage: launcher player <file> [--gui]")
        return
    flags = [a for a in args if a.startswith("--")]
    file = next((a for a in args if not a.startswith("--")), None)
    if not file or not os.path.exists(file):
        print(f"  Not found: {file}")
        return
    root = _project_root()
    cmd = [sys.executable, os.path.join(root, "player.py"), file]
    if "--gui" in flags:
        cmd.append("--gui")
    proc, log = launch(cmd, window=True)
    if proc:
        print(f"  Player launched in new window (pid {proc.pid}).")
    elif log:
        print(f"  Player detached (pid {proc.pid}). Log: {log}")


def _cmd_compile(args):
    from _launch import launch
    if not args:
        print(f"  Usage: launcher compile <file> -o <out>")
        return
    root = _project_root()
    cmd = [sys.executable, os.path.join(root, "ep.py"), "compile"] + [a for a in args if not a.startswith("--")]
    if "--human" in args:
        cmd.append("--human")
    if "--machine" in args:
        cmd.append("--machine")
    proc, log = launch(cmd, window=True)
    if proc:
        print(f"  Compiler launched in new window (pid {proc.pid}).")


def _cmd_shell(args=None):
    from _launch import launch
    root = _project_root()
    cmd = [sys.executable, os.path.join(root, "eshell.py")]
    # Optional --project <dir> to start the shell in a specific directory
    if args and "--project" in args:
        idx = args.index("--project")
        if idx + 1 < len(args):
            cmd += ["--project", args[idx + 1]]
    proc, log = launch(cmd, window=True)
    if proc:
        print(f"  HELLFORGE shell launched in new window (pid {proc.pid}).")


def _cmd_log(args):
    root = _project_root()
    log_dir = os.path.join(root, "logs")
    if not args:
        logs = sorted(glob.glob(os.path.join(log_dir, "*.log")), reverse=True)[:10]
        if not logs:
            print(f"  No logs found.")
            return
        print(f"  Recent logs:")
        for l in logs:
            print(f"    {os.path.basename(l)} ({os.path.getsize(l)} bytes)")
        return
    name = args[0]
    path = os.path.join(log_dir, name)
    if not os.path.exists(path):
        # Try partial match
        matches = glob.glob(os.path.join(log_dir, f"*{name}*"))
        if not matches:
            print(f"  Log not found: {name}")
            return
        path = matches[0]
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    lines = content.split("\n")
    # Show last 40 lines
    for line in lines[-40:]:
        print(f"  {line}")
    print(f"\n  ({len(lines)} lines, {os.path.getsize(path)} bytes)")


def _cmd_ps():
    from _launch import list_hellforge_processes
    procs = list_hellforge_processes()
    if not procs:
        print(f"  No running HELLFORGE processes.")
        return
    print(f"  Running HELLFORGE processes ({len(procs)}):")
    for p in procs:
        print(f"    [{p['pid']}] {p['cmdline'][:80]}")


def _cmd_kill(args):
    from _launch import kill_process
    if not args:
        print(f"  Usage: launcher kill <pid>")
        return
    try:
        pid = int(args[0])
    except ValueError:
        print(f"  Invalid PID: {args[0]}")
        return
    if kill_process(pid):
        print(f"  Killed process {pid}.")
    else:
        print(f"  Failed to kill process {pid}.")
