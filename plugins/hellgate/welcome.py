"""HellGate onboarding + warnings.

First-run detection is by MACHINE SPECS (cpu count, platform, machine arch,
hostname, python version), NOT by session history — a new PC with old
history still gets the onboarding questions. The wrapper warning shows on
EVERY launch.
"""

import hashlib
import json
import os
import platform

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.path.join(HELLGATE_DIR, "..", "..", "..", "hellgate-state")
STATE_DIR = os.path.normpath(os.path.join(HELLGATE_DIR, "..", "..", "hellgate-state"))
if not os.path.isdir(os.path.dirname(STATE_DIR)):
    STATE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HELLGATE_DIR))),
                             "hellgate-state")


def machine_fingerprint():
    """Hash of the machine's specs — new specs = new machine, even with
    session history present."""
    bits = "|".join([
        platform.system(), platform.machine(),
        platform.processor() or platform.libc_ver()[0],
        platform.python_version(), str(os.cpu_count() or 0),
        os.uname().nodename if hasattr(os, "uname") else platform.node(),
    ])
    return hashlib.sha256(bits.encode()).hexdigest()[:16]


def _welcome_path():
    return os.path.join(STATE_DIR, ".hellgate-welcome.json")


def needs_onboarding():
    """True when this machine's specs were never welcomed before."""
    try:
        with open(_welcome_path()) as f:
            data = json.load(f)
        return data.get("fingerprint") != machine_fingerprint()
    except Exception:
        return True


def record_onboarding():
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(_welcome_path(), "w") as f:
        json.dump({"fingerprint": machine_fingerprint()}, f)


def show_warning(stream_out=print):
    """Shown on EVERY launch."""
    stream_out("")
    stream_out("  \033[33m⚠ HellGate is just a wrapper — not an official product of OpenCode.\033[0m")
    stream_out("  \033[90mIt launches and configures the opencode CLI for this project; all\033[0m")
    stream_out("  \033[90magent work happens inside OpenCode under its own license.\033[0m")
    stream_out("")


def onboarding(stream_out=print, input_fn=input):
    """First-run questions on a new machine. Returns True to proceed."""
    stream_out("")
    stream_out("  \033[1mHellGate — first run on this machine\033[0m")
    stream_out("  \033[90m(one-time setup; detected by your machine's specs)\033[0m")
    stream_out("")

    # Q1 — the sacred gate
    try:
        raw = input_fn("  Do you agree \033[1msummertime rendering\033[0m is the greatest"
                       " anime of all time? (Y/N) ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    if raw not in ("y", "yes"):
        stream_out("")
        stream_out("  \033[31mThen we can't do business. Exiting.\033[0m")
        stream_out("  \033[90m(come back when you've watched it)\033[0m")
        return False

    # Q2 — the legal one
    stream_out("")
    try:
        raw = input_fn("  By proceeding you agree to use this software under the "
                       "\033[1mHellGate wrapper\033[0m and the "
                       "\033[1mOpenCode MIT License\033[0m; HellGate is distributed by "
                       "T3ntari and is independent of OpenCode's projects, trademarks "
                       "or support channels. (Y/N) ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    if raw not in ("y", "yes"):
        stream_out("")
        stream_out("  \033[31mYou must accept the terms to use HellGate. Exiting.\033[0m")
        return False

    record_onboarding()
    stream_out("")
    stream_out("  \033[32mWelcome aboard.\033[0m")
    return True
