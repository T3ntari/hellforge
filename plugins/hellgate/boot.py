"""HellGate boot — the welcome page and the loading screen.

Renders the HellCode banner + version, runs REAL initialization steps
(imports, compile checks, quick self-tests, knowledge prep, config gen)
and animates a dots spinner with a x/1024 counter below the loader.
"""

import os
import subprocess
import sys
import threading
import time

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(HELLGATE_DIR))
TOTAL = 1024

BANNER = r"""
  ██░ ██  ▄████▄  ██▓     ██▓     ▄████▄ ▓█████  ██▓ ▒█████
 ▓██░ ██▒▒██▀ ▀█ ▓██▒    ▓██▒    ▒██▀ ▀█ ▓█   ▀ ▓██▒▒██▒  ██▒
 ▒██▀▀██░▒▓█    ▄▒██░    ▒██░    ▒▓█    ▄▒███   ▒██░▒██░  ██▒
 ░▓█ ░██ ▒▓▓▄ ▄██▒██░    ▒██░    ▒▓▓▄ ▄██▒▓█  ▄ ░██░░██   ██░
 ░▓█▒░██▓▒ ▓███▀ ░██████▒░██████▒▒ ▓███▀ ░▒████▒░██░░ ████▓▒░
  ▒ ░░▒░▒░ ░▒ ▒  ░ ▒░▓  ░░ ▒░▓  ░░ ░▒ ▒  ░░ ▒░ ░░▓  ░ ▒░▒░▒░
  ▒ ░▒░ ░  ░  ▒   ░ ░ ▒  ░░ ░ ▒  ░  ░  ▒   ░ ░  ░ ▒ ░ ░ ▒ ▒░
  ░  ░░ ░░        ░ ░     ░ ░    ░        ░  ░  ░ ░ ░ ░ ░ ▒
  ░  ░  ░░ ░       ░  ░    ░  ░  ░ ░ ░     ░  ░    ░ ░ ░ ░
             ░                         ░              ░
"""


def _clear():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def _out(line):
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def _tiny(line):
    _out("\033[90m" + line + "\033[0m")


def _steps(project_dir):
    """Real init steps: (label, callable). Return True when all passed."""
    ok = True

    def _imports():
        import ep_core  # noqa: F401
        from plugins import hellgate  # noqa: F401
        from plugins.hellgate import knowledge, providers, summarizer  # noqa: F401

    def _compile_check():
        r = subprocess.run([sys.executable, "-m", "compileall", "-q",
                            os.path.join(HELLGATE_DIR),
                            os.path.join(project_dir, "ep_core.py")],
                           capture_output=True)
        return r.returncode == 0

    def _self_tests():
        r = subprocess.run([sys.executable,
                            os.path.join(HELLGATE_DIR, "tests", "test_summarizer.py")],
                           capture_output=True)
        return r.returncode == 0

    def _knowledge():
        from plugins.hellgate import session as S
        return bool(S.prepare_knowledge(print))

    def _providers():
        from plugins.hellgate import providers as P
        return P.installed_models() is not None

    def _opencode_bin():
        import shutil
        return bool(shutil.which("opencode"))

    def _version():
        from plugins.hellgate import HELLGATE_VERSION
        return HELLGATE_VERSION

    def _config():
        from plugins.hellgate import providers as P
        from plugins.hellgate.tools import opencode as OC
        p = P.by_id("ollama")
        return bool(OC.detect())

    steps = [
        ("initializing hellcode core", _imports),
        ("compile checks", _compile_check),
        ("running self-tests", _self_tests),
        ("building knowledge pack", _knowledge),
        ("probing providers", _providers),
        ("locating opencode", _opencode_bin),
        ("preparing opencode config", _config),
    ]
    for label, fn in steps:
        try:
            if fn() is False:
                ok = False
        except Exception:
            ok = False
        finally:
            pass
    return ok


def run_boot(project_dir, version, stream_out=print):
    """Welcome page + loading screen. Returns the number of completed units
    (of TOTAL)."""
    _clear()
    _out(BANNER)
    _out("\033[1m                 HellGate v%s\033[0m" % version)
    _out("")
    _tiny("                         - T3ntari")
    _out("")

    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    done = threading.Event()
    progress = {"units": 0}
    lock = threading.Lock()

    def animate():
        i = 0
        cur = 0
        last = 0
        while not done.is_set():
            i += 1
            with lock:
                cur = progress["units"]
            if cur != last:
                last = cur
                _clear()
                _out(BANNER)
                _out("\033[1m                 HellGate v%s\033[0m" % version)
                _out("")
                _tiny("                         - T3ntari")
                _out("")
            bar = spinner[i % len(spinner)]
            _out("")
            _out("  \033[1m" + bar + " initializing hellcode — running tests…\033[0m")
            _out("")
            _tiny("                          %d/%d" % (min(cur, TOTAL), TOTAL))
            time.sleep(0.06)

    th = threading.Thread(target=animate, daemon=True)
    th.start()

    # Real work, mapped onto the 1024-unit counter.
    ok = True
    try:
        import ep_core  # noqa
        from plugins.hellgate import knowledge, providers, summarizer  # noqa
    except Exception:
        ok = False
    with lock:
        progress["units"] = 128

    r = subprocess.run([sys.executable, "-m", "compileall", "-q",
                        HELLGATE_DIR, os.path.join(project_dir, "ep_core.py")],
                       capture_output=True)
    if r.returncode != 0:
        ok = False
    with lock:
        progress["units"] = 256

    r = subprocess.run([sys.executable,
                        os.path.join(HELLGATE_DIR, "tests", "test_summarizer.py")],
                       capture_output=True)
    if r.returncode != 0:
        ok = False
    with lock:
        progress["units"] = 512

    from plugins.hellgate import session as S
    try:
        S.prepare_knowledge(print)
    except Exception:
        ok = False
    with lock:
        progress["units"] = 640

    from ep_compiler.security_hash import verify as _sec_verify
    try:
        _sec = _sec_verify()
        if not _sec["ok"]:
            ok = False
    except Exception:
        pass
    with lock:
        progress["units"] = 768

    try:
        providers.installed_models()
        import shutil
        opencode_ok = bool(shutil.which("opencode"))
    except Exception:
        opencode_ok = False
    if not opencode_ok:
        ok = False
    with lock:
        progress["units"] = 896

    try:
        from plugins.hellgate.tools import opencode as OC
        cfg_ok = OC.detect()
    except Exception:
        cfg_ok = False
    if not cfg_ok:
        ok = False
    with lock:
        progress["units"] = TOTAL

    done.set()
    th.join(timeout=1)
    _clear()
    _out(BANNER)
    _out("\033[1m                 HellGate v%s\033[0m" % version)
    _out("")
    _tiny("                         - T3ntari")
    _out("")
    _out("  \033[32m✔ ready — %d/%d\033[0m" % (TOTAL, TOTAL))
    if not ok:
        _out("  \033[33m⚠ some checks failed — continuing anyway\033[0m")
    time.sleep(0.5)
    return progress["units"]
