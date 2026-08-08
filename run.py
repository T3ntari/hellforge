#!/usr/bin/env python3
"""HELLFORGE Launcher — launch player, compiler, or a new shell in separate windows.

Usage:
    run.py play <file> [--gui] [--window] [--detach]
    run.py compile <file> -o <out> [--window] [--detach] [--human|--machine]
    run.py shell

Modes:
    --window   Open a dedicated console window (CREATE_NEW_CONSOLE on Windows)
    --detach   Run in background, log output to logs/, return immediately
    --gui      Use the pygame glassmorphism player (EPlayer)
"""

import os
import sys
import subprocess
import time
import shutil

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_DIR)
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"

EP_PATH = os.path.join(PROJECT_DIR, "ep.py")
PLAYER_PATH = os.path.join(PROJECT_DIR, "player.py")
ESHELL_PATH = os.path.join(PROJECT_DIR, "eshell.py")
LOG_DIR = os.path.join(PROJECT_DIR, "logs")


def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def launch(cmd, window=False, detach=False, cwd=None):
    """Launch a subprocess. Returns (Popen|None, log_path|None).
    window=True  → dedicated console window
    detach=True  → background process with log file
    Neither      → blocking run (inherits this console)
    """
    cwd = cwd or PROJECT_DIR
    creationflags = 0
    if os.name == "nt":
        if window:
            creationflags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NEW_PROCESS_GROUP
        elif detach:
            creationflags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NO_WINDOW

    log_path = None
    if detach:
        ensure_log_dir()
        ts = time.strftime("%Y%m%d_%H%M%S")
        name = os.path.basename(cmd[-1]) if cmd else "run"
        log_path = os.path.join(LOG_DIR, f"run_{ts}_{name}.log")
        log_file = open(log_path, "w", encoding="utf-8")
        proc = subprocess.Popen(
            cmd, cwd=cwd, creationflags=creationflags,
            stdin=subprocess.DEVNULL, stdout=log_file, stderr=subprocess.STDOUT,
            start_new_session=(os.name != "nt"),
        )
        return proc, log_path

    if window:
        return subprocess.Popen(cmd, cwd=cwd, creationflags=creationflags), None

    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=7200)
    if r.stdout:
        print(r.stdout, end="")
    if r.stderr:
        print(r.stderr, end="", file=sys.stderr)
    return None, None


def cmd_play(args):
    if not args:
        print("  Usage: run.py play <file> [--gui] [--window] [--detach]")
        return 1
    flags = [a for a in args if a.startswith("--")]
    file = next((a for a in args if not a.startswith("--")), None)
    if not file or not os.path.exists(file):
        print(f"  Not found: {file}")
        return 1
    cmd = [sys.executable, PLAYER_PATH, file]
    if "--gui" in flags or "-g" in flags:
        cmd.append("--gui")
    proc, log = launch(cmd, window="--window" in flags, detach="--detach" in flags)
    if log:
        print(f"  Detached (pid {proc.pid}). Log: {log}")
        print(f"  View: launcher log {os.path.basename(log)}")
    elif proc:
        print(f"  Launched in new window (pid {proc.pid}).")
    return 0


def cmd_compile(args):
    if not args:
        print("  Usage: run.py compile <spec> [-o <out>] [--to v1|v2|v3|v4] [--recursive]")
        print("         --to <ver>  convert syntax instead of exporting MIDI (portbaby)")
        print("         --strict    fail fast on any syntax/diagnostic error")
        print("         --mem       print memory estimate after compiling")
        print("         <spec>: file | dir | / (all) | glob | multiple specs")
        return 1

    flags = [a for a in args if a.startswith("--")]

    # Syntax conversion mode: --to v1|v2|v3|v4
    if "--to" in args:
        idx = args.index("--to")
        if idx + 1 >= len(args):
            print("  --to requires a version: v1 | v2 | v3 | v4 | v5 (v5 = canonical, converts to v4 superset)")
            return 1
        target = args[idx + 1].lower()
        rest = [a for a in args if a.startswith("--") or a == args[idx + 1]]
        specs = [a for a in args if not a.startswith("--") and a != args[idx + 1]]
        cmd = [sys.executable, EP_PATH, "compile"]
        # Fall through to ep compile which handles .ei/.enx via cli
        recursive = "--recursive" in flags
        from ep_compiler.paths import resolve_inputs
        files = resolve_inputs(specs if specs else ["/"], recursive=recursive)
        if not files:
            print("  No matching files found.")
            return 1
        for f in files:
            _convert_syntax(f, target)
        return 0

    cmd = [sys.executable, EP_PATH, "compile"]
    out_path = None
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args):
            out_path = args[idx + 1]
    specs = [a for a in args if not a.startswith("--") and a != "-o" and a != out_path]
    from ep_compiler.paths import resolve_inputs
    files = resolve_inputs(specs if specs else ["/"], recursive="--recursive" in flags)
    if not files:
        print("  No matching files found.")
        return 1

    extra = []
    if "--human" in flags:
        extra.append("--human")
    if "--machine" in flags:
        extra.append("--machine")
    if "--strict" in flags:
        extra.append("--strict")

    use_window = "--window" in flags
    use_detach = "--detach" in flags
    if out_path and len(files) > 1:
        print(f"  -o {out_path} ignored for {len(files)} files — outputs written next to sources")

    for f in files:
        fcmd = cmd + [f]
        if out_path and len(files) == 1:
            fcmd += ["-o", out_path]
        fcmd += extra
        proc, log = launch(fcmd, window=use_window, detach=use_detach)
        if log:
            print(f"  Detached (pid {proc.pid}). Log: {log}")
            print(f"  View: launcher log {os.path.basename(log)}")
        elif proc:
            print(f"  Compiling in new window (pid {proc.pid}).")

    if not use_window and not use_detach:
        if len(files) == 1:
            out_path = out_path or os.path.splitext(files[0])[0] + ".mid"
            if out_path and os.path.exists(out_path):
                try:
                    import mido
                    m = mido.MidiFile(out_path)
                    notes = sum(1 for msg in m if msg.type == "note_on" and msg.velocity > 0)
                    mins, secs = divmod(int(m.length), 60)
                    size = os.path.getsize(out_path)
                    print(f"  ✓ {out_path} — {notes} notes, {mins}:{secs:02d}, {size//1024}KB (MIDI is compact; size is normal)")
                except Exception:
                    pass
        else:
            print(f"  ✓ Compiled {len(files)} file(s) — outputs next to sources")
        if "--mem" in args:
            _print_mem_report(specs if specs else ["/"])
    return 0


def _print_mem_report(specs):
    """Estimate event memory usage for the compiled output."""
    try:
        from ep_compiler.paths import resolve_inputs
        from ep_compiler.compile import compile_source
        import sys as _sys
        files = resolve_inputs(specs)
        total = 0
        bytes_per = 0
        for f in files:
            try:
                with open(f, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
                ev, bp = compile_source(text)
                total += len(ev)
                if ev and bytes_per == 0:
                    bytes_per = _sys.getsizeof(ev[0])
            except Exception as e:
                print(f"  --mem: {f}: {e}")
        est_kb = (total * bytes_per) / 1024 if bytes_per else 0
        print(f"  --mem: {total} events × ~{bytes_per}B ≈ {est_kb:.0f}KB ({est_kb/1024:.2f}MB) in-memory")
    except Exception as e:
        print(f"  --mem report failed: {e}")


def _convert_syntax(path, target):
    """Convert a source file to a target syntax version via portbaby."""
    try:
        from plugins.portbaby.converter import convert_file
    except ImportError:
        print(f"  portbaby not available — cannot convert {path}")
        return
    ver_map = {"v1": "v1_machine", "v2": "v2", "v3": "v3", "v4": "v4", "v5": "v4"}
    conv = ver_map.get(target, target)
    try:
        result = convert_file(path, conv, make_project=False, show_report=False)
        out = (result or {}).get("output")
        if out:
            print(f"  ✓ {path} → {out} ({target})")
        else:
            print(f"  ✓ {path} → {target} (output written next to source)")
    except Exception as e:
        print(f"  ✗ {path}: {e}")


def cmd_check(args):
    """Lint E files: run.py check <spec> [--recursive] [--max <N>]"""
    if not args:
        print("  Usage: run.py check <spec> [--recursive] [--max <N>]")
        print("         <spec>: file | dir | / (all) | glob | multiple specs")
        return 1
    from ep_compiler.paths import resolve_inputs
    from ep_compiler.lint import lint_source, format_diags, catalog_stats
    recursive = "--recursive" in args
    max_show = 30
    if "--max" in args:
        idx = args.index("--max")
        if idx + 1 < len(args):
            try:
                max_show = int(args[idx + 1])
            except ValueError:
                pass
    rest = [a for a in args if not a.startswith("--")]
    specs = rest if rest else ["/"]
    files = resolve_inputs(specs, recursive=recursive)
    if not files:
        print("  No matching files found.")
        return 1
    stats = catalog_stats()
    print(f"  HELLFORGE linter — catalog: {stats['errors']} errors, {stats['warnings']} warnings, {stats['info']} info")
    total = 0
    bad = 0
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception as e:
            print(f"  Cannot read {f}: {e}")
            continue
        diags = lint_source(text, path=f)
        total += len(diags)
        errors = sum(1 for d in diags if d["severity"] in (0, 1))
        warnings = sum(1 for d in diags if d["severity"] == 2)
        if errors:
            bad += 1
        print(f"\n  {f} — {len(diags)} diagnostics ({errors} errors, {warnings} warnings)")
        print(format_diags(diags, max_show=max_show))
    print(f"\n  Scanned {len(files)} file(s), {total} diagnostics total.")
    return 1 if bad else 0


def cmd_shell(args):
    cmd = [sys.executable, ESHELL_PATH]
    # Forward --project <root> so the shell starts in the right directory
    if "--project" in args:
        idx = args.index("--project")
        if idx + 1 < len(args):
            cmd += ["--project", args[idx + 1]]
    proc, log = launch(cmd, window=True)
    if proc:
        print(f"  HELLFORGE shell launched in new window (pid {proc.pid}).")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    mode = sys.argv[1]
    args = sys.argv[2:]
    if mode in ("play", "player", "p"):
        return cmd_play(args)
    if mode in ("compile", "c"):
        return cmd_compile(args)
    if mode in ("check", "lint", "lintfile"):
        return cmd_check(args)
    if mode in ("shell", "s"):
        return cmd_shell(args)
    if mode in ("--help", "-h", "help"):
        print(__doc__)
        return 0
    print(f"  Unknown mode: {mode}")
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())
