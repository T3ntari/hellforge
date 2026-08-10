"""HELLFORGE SAFE MODE — entered when the integrity checks fail.

Isolates the core: plugins are not loaded, only a minimal restricted shell
runs. The user can:
  status                  what failed and why
  reinstall               re-install the current version from GitHub
                          (configs/plugins/mods preserved) with a progress
                          bar; on success: "installation successful,
                          exiting safe mode"
  /safemode exit force    leave anyway — warned first that this is highly
                          risky
  quit                    stay in safe mode (default, safe)
"""

import sys
import threading
import time

from . import update as U
from . import security_hash as SH


def _progress_bar(stream_out, done_event, total=100):
    """Animated progress bar while the updater reports steps."""
    bar = "█"
    width = 40
    cur = 0
    while not done_event.is_set():
        stream_out("\r  [%s] %3d%%" % ("█" * (cur * width // 100) +
                                       "░" * (width - cur * width // 100), cur),
                   end="", flush=True)
        time.sleep(0.15)
    stream_out("\r  [%s] %3d%%" % ("█" * width, 100), flush=True)
    stream_out("")


def _run_reinstall(stream_out, progress):
    """Reinstall the current version with a live progress bar."""
    done = threading.Event()

    def animate():
        _progress_bar(stream_out, done)

    th = threading.Thread(target=animate, daemon=True)
    th.start()
    try:
        tag = U.current_target()
        code = U.safe_update(tag, progress=progress, stream_out=stream_out)
    except Exception as e:
        code = 1
        stream_out(f"\n  reinstall error: {e}")
    finally:
        done.set()
        th.join(timeout=1)
    stream_out("")
    if code == 0:
        stream_out("  \033[32minstallation successful, exiting safe mode\033[0m")
        return True
    stream_out("  \033[31mreinstall failed — staying in safe mode\033[0m")
    return False


def enter_safemode(reason, detail, stream_out=print, input_fn=input,
                   manual=False):
    """Run the restricted safe-mode shell. Returns True when exiting (either
    via successful reinstall or forced exit).

    manual=True: the user picked the safemode kernel themselves — the alarm
    box and the 'highly risky' exit lecture are for REAL verification
    failures only, not for a deliberate choice."""
    stream_out("")
    if manual:
        stream_out("  \033[36msafe mode\033[0m \033[2m(manually selected kernel — "
                   "core untouched; exit with /safemode exit force)\033[0m")
    else:
        stream_out("  \033[31m╔══════════════════════════════════════════════════╗\033[0m")
        stream_out("  \033[31m║           HELLFORGE SAFE MODE                    ║\033[0m")
        stream_out("  \033[31m╚══════════════════════════════════════════════════╝\033[0m")
    stream_out(f"  reason : {reason}")
    stream_out(f"  detail : {detail}")
    stream_out("  plugins are isolated; only safe-mode commands run.")
    stream_out("  commands: status | reinstall | /safemode exit force | quit")
    stream_out("")

    # A tiny progress callback that moves the animated bar
    progress_state = {"n": 0}

    def progress(n):
        progress_state["n"] = n

    while True:
        try:
            raw = input_fn("SAFEMODE> ").strip()
        except (EOFError, KeyboardInterrupt):
            stream_out("\n  staying in safe mode. quit to leave this session.")
            continue
        low = raw.lower()
        if low in ("quit", "exit"):
            stream_out("  staying in safe mode (the core stays isolated).")
            continue
        if low == "status":
            r = SH.verify()
            x_ok, x_detail = SH.x_verify()
            stream_out(f"  core digest : {'OK' if r['ok'] else 'FLAGGED'} "
                       f"({r['detail']})")
            stream_out(f"  technique X : {'OK' if x_ok else 'FLAGGED'} ({x_detail})")
            tag, y = SH.load_version_key()
            stream_out(f"  version key : {tag or '(none)'} "
                       f"{'present' if y else 'MISSING'}")
            continue
        if low in ("reinstall", "net", "network"):
            stream_out("  internet access granted for the reinstall.")
            stream_out(f"  re-installing {U.current_target()} — nothing is lost: "
                       "custom plugins, mods, configs and identity are backed up "
                       "and restored automatically.")
            try:
                ok_ = input_fn("  proceed with reinstall? (Y/N) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ok_ = "n"
            if ok_ in ("y", "yes"):
                stream_out("")
                if _run_reinstall(stream_out, progress):
                    return True
            else:
                stream_out("  reinstall declined — staying in safe mode.")
            continue
        if low in ("/safemode exit force", "exit force", "force"):
            if manual:
                # user chose this kernel — the core is fine, no lecture
                stream_out("  leaving safe mode.")
                return True
            stream_out("  \033[31mWARNING: this is highly risky.\033[0m")
            stream_out("  \033[31mThe core digest does not verify — leaving safe")
            stream_out("  \033[31mmode means running with an unverified core.")
            stream_out("  \033[31mYou will be exposed to whatever was tampered.")
            stream_out("  \033[31mYour choice.\033[0m")
            try:
                ok_ = input_fn("  force-exit safe mode? (Y/N) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ok_ = "n"
            if ok_ in ("y", "yes"):
                stream_out("  exiting safe mode by force.")
                return True
            stream_out("  staying in safe mode.")
            continue
        stream_out("  try: status | reinstall | /safemode exit force | quit")

def safe_boot(stream_out=print, input_fn=input, ask_update=True):
    """The init-time security sequence:

    1. Technique X first (local, offline) — the rotating hidden digest.
       Fail -> SAFE MODE (isolates the core).
    2. Then the network probe. Offline -> X alone is the proof (done).
    3. Online -> Technique Y (per-version key from GitHub) + version check;
       a newer version is offered with a safe update (no data loss).

    Returns: "ok" | "offline-ok" | "safemode-force" | "safemode-reinstalled"
    """
    from . import security_hash as SH

    # 1) X — the local offline proof, checked FIRST
    x_ok, x_detail = SH.x_verify()
    if not x_ok:
        stream_out("  \033[31m[security] technique X FAILED\033[0m")
        stream_out(f"  \033[90m{x_detail}\033[0m")
        forced = enter_safemode("technique X failed", x_detail, stream_out, input_fn)
        return "safemode-force" if forced else "safemode-stay"

    stream_out("  \033[32m[security] X verified (hidden digest matches core)\033[0m")
    # 2+3) network probe and technique Y run CONCURRENTLY (cached probe
    #       means the menu check is instant; Y is capped at 6s)
    import threading as _th
    _results = {}

    def _probe():
        _results["online"] = SH.remote_version(timeout=2) is not None

    def _ycheck():
        _results["y"] = SH.y_verify_online(timeout=6)

    _t1 = _th.Thread(target=_probe, daemon=True)
    _t2 = _th.Thread(target=_ycheck, daemon=True)
    _t1.start(); _t2.start()
    _t1.join(timeout=3); _t2.join(timeout=7)

    online = _results.get("online", False)
    # a slow network must never send the machine to SAFE MODE: if the
    # probe or Y check does not finish in time, X alone is the proof
    if not online or "y" not in _results:
        stream_out("  \033[90m[security] offline — X is the proof, skipping Y\033[0m")
        # X is the proof offline; rotate the hidden layout for next init
        SH.x_rotate()
        return "offline-ok"

    # 3) online: technique Y + version sync
    y_ok, y_detail = _results["y"]
    if not y_ok:
        stream_out("  \033[31m[security] technique Y FAILED\033[0m")
        stream_out(f"  \033[90m{y_detail}\033[0m")
        forced = enter_safemode("technique Y failed", y_detail, stream_out, input_fn)
        return "safemode-force" if forced else "safemode-stay"
    stream_out("  \033[32m[security] integrity verified (X + Y)\033[0m")

    SH.x_rotate()
    if ask_update:
        latest = SH.remote_version()
        local = SH.local_version()
        if latest and latest != local:
            stream_out(f"  new version detected: {latest} (local: {local})")
            try:
                ans = input_fn("  update now? (Y/N) ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                ans = "n"
            if ans in ("y", "yes"):
                from . import update as U
                done = threading.Event()
                def animate():
                    _progress_bar(stream_out, done)
                th = threading.Thread(target=animate, daemon=True)
                th.start()
                try:
                    U.safe_update(latest, progress=lambda n: None,
                                  stream_out=stream_out)
                finally:
                    done.set()
                    th.join(timeout=1)
                stream_out("")
                stream_out("  \033[32mupdate complete — restart to continue\033[0m")
    return "ok"
