"""hellgate.util — shared helpers (path confinement, run, logging)."""

import os
import shutil
import subprocess
import sys

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(HELLGATE_DIR))


def run(cmd, cwd, stream_out=print, env=None, timeout=None):
    """Run a command with output streamed to stream_out. Never a shell."""
    base = dict(os.environ)
    if env:
        base.update(env)
    p = subprocess.Popen(cmd, cwd=cwd, env=base, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True)
    for line in p.stdout:
        stream_out(line.rstrip("\n"))
    p.wait(timeout=timeout)
    return p.returncode


def which(name):
    return shutil.which(name) or (os.path.exists(name) and name) or None


def confine(path, root):
    """True when path stays inside root (or equals it)."""
    rp = os.path.realpath(path)
    rr = os.path.realpath(root)
    return rp == rr or rp.startswith(rr + os.sep)


def pick_agent(agents, agent_name):
    """Map agent name → config; agent_name None/'default' → None (default)."""
    if agent_name in (None, "", "default", "Default"):
        return None
    for a in agents:
        if a["name"].lower() == str(agent_name).lower():
            return a
    return None


def say(msg, out=print):
    out(f"\033[90mhellgate\033[0m {msg}")
