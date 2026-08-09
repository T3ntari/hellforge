#!/usr/bin/env python3
"""
HELLFORGE v1.0.0.0 ALPHA — Futuristic CLI for E Language operations.
CORE-EXPANSION: REGAS | Signed: TENTARI
Supports compiling to .mid, .wav, .mp3, .mp4, .ec, .eic, .ee, .ecc
"""

import os
import json
import urllib.request
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
EP_PATH = PROJECT_DIR / "ep.py"
PLAYER_PATH = PROJECT_DIR / "player.py"
PKG = None  # Lazy import

# ── System Resource Limits ──
_SYS_MEM_GB = 2        # default 2GB memory limit
_SYS_THREADS = 4        # default 4 thread limit
_SYS_THREAD_SEM = None  # initialized on first use

R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
CYAN = "\033[96m"; GREY = "\033[90m"; PINK = "\033[38;2;255;105;180m"
MAGENTA = "\033[95m"

def c(text, color=""):
    return f"{color}{text}{R}" if color and sys.stdout.isatty() else text


# ── System Resource Helpers ──

def _get_thread_semaphore():
    """Lazy-init thread semaphore for controlling concurrency."""
    global _SYS_THREAD_SEM
    if _SYS_THREAD_SEM is None:
        import threading
        _SYS_THREAD_SEM = threading.BoundedSemaphore(_SYS_THREADS)
    return _SYS_THREAD_SEM


def _parse_mem(value):
    """Parse memory value like '2G', '512M', '128K', '1024B' or plain number (default GB).
    Returns size in GB as float. Minimum 0.125 GB (128MB)."""
    try:
        val = str(value).strip().upper()
        if val.endswith("G"):
            return max(0.125, float(val[:-1]))
        elif val.endswith("M"):
            return max(0.125, float(val[:-1]) / 1024)
        elif val.endswith("K"):
            return max(0.125, float(val[:-1]) / (1024 * 1024))
        elif val.endswith("B"):
            return max(0.125, float(val[:-1]) / (1024 * 1024 * 1024))
        else:
            return max(0.125, float(val))
    except (ValueError, TypeError):
        return None


def _format_mem(gb):
    """Format GB value to human-readable string."""
    if gb >= 1.0:
        return f"{gb:.1f}G" if gb != int(gb) else f"{int(gb)}G"
    elif gb >= 0.001:
        return f"{int(gb * 1024)}M"
    else:
        return f"{int(gb * 1024 * 1024)}K"


def _set_mem_limit(raw):
    """Set memory limit. Accepts '2G', '512M', '128K', '1024B' or number (GB)."""
    global _SYS_MEM_GB
    gb = _parse_mem(raw)
    if gb is None:
        return False
    _SYS_MEM_GB = min(64.0, gb)
    try:
        from ep_core import (
            _plugin_configs,
            _save_plugin_configs,
        )
        _plugin_configs["_sys_mem_gb"] = _SYS_MEM_GB
        _save_plugin_configs()
    except Exception:
        pass
    return True


def _set_thread_limit(n):
    """Set thread limit. Persists to config."""
    global _SYS_THREADS, _SYS_THREAD_SEM
    _SYS_THREADS = max(1, min(64, int(n)))
    # Recreate semaphore with new limit
    import threading
    _SYS_THREAD_SEM = threading.BoundedSemaphore(_SYS_THREADS)
    try:
        from ep_core import (
            _plugin_configs,
            _save_plugin_configs,
        )
        _plugin_configs["_sys_threads"] = _SYS_THREADS
        _save_plugin_configs()
    except Exception:
        pass


def _load_sys_limits():
    """Load saved limits from config."""
    global _SYS_MEM_GB, _SYS_THREADS, _SYS_THREAD_SEM
    try:
        from ep_core import _plugin_configs
        saved_mem = _plugin_configs.get("_sys_mem_gb")
        saved_threads = _plugin_configs.get("_sys_threads")
        if saved_mem:
            _SYS_MEM_GB = max(1, min(64, int(saved_mem)))
        if saved_threads:
            _SYS_THREADS = max(1, min(64, int(saved_threads)))
            import threading
            _SYS_THREAD_SEM = threading.BoundedSemaphore(_SYS_THREADS)
    except Exception:
        pass

def banner():
    RED_ = RED
    print(f"\n  {c('███████████████████████████████████████', RED_)}")
    print(f"  {c('█', RED_)}     {c('H E L L F O R G E', B)}     {c('█', RED_)}")
    print(f"  {c('█', RED_)}   {c('v1.0.0.0 ALPHA', D)}   {c('█', RED_)}")
    print(f"  {c('███████████████████████████████████████', RED_)}")
    print(f"  {c('CORE-EXPANSION: REGAS', RED_)}  {c('| Signed: TENTARI', D)}")
    print(f"  {c('Type help for commands  |  Run sign --setup to register', D)}\n")

def strip_path(p):
    return p.strip("\"'")

def run_ep(cmd, desc="Compiling"):
    print(f"  {c(f'⚙ {desc}...', YELLOW)}")
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    if r.returncode == 0:
        out = cmd[cmd.index("-o") + 1] if "-o" in cmd else "?"
        full = os.path.abspath(out)
        sz = os.path.getsize(full) // 1024 if os.path.exists(full) else 0
        print(f"  {c('✓', GREEN)} {full} ({sz}KB)")
        return True
    else:
        print(f"  {c('✗', RED)} {r.stderr.strip()[:250]}")
        return False

def do_cd(args):
    target = os.path.expanduser(" ".join(args)) if args else str(PROJECT_DIR)
    try:
        os.chdir(target)
        print(f"  {c('→', CYAN)} {os.getcwd()}")
    except Exception as e:
        print(f"  {c('✗', RED)} {e}")

def do_ls(args):
    path = " ".join(args) if args else "."
    try:
        items = sorted(os.listdir(path))
    except Exception as e:
        print(f"  {c('✗', RED)} {e}"); return
    for item in items:
        full = os.path.join(path, item)
        ext = os.path.splitext(item)[1].lower()
        color = CYAN if os.path.isdir(full) else GREY
        if ext in (".e",".ei",".eic"): color = GREEN
        elif ext in (".mid",".wav",".mp3",".mp4"): color = YELLOW
        elif ext in (".ee",".ec",".ecc"): color = RED
        elif ext == ".py": color = MAGENTA
        sz = os.path.getsize(full) if os.path.isfile(full) else 0
        s = f"{sz//1024}KB" if sz > 1024 else f"{sz}B" if sz else ""
        print(f"  {c(item, color)}{c(f' {s}', D)}")

def do_compile(args):
    if not args:
        help = f"  {c('Usage: compile <spec> [-o <out>] [--human] [--async] [--recursive]', D)}"
        print(help)
        print(f"  {c('  <spec>: file | dir | / (all) | glob | multiple specs', GREY)}")
        print(f"  {c('  Input: .e .ei .eci .enx .eic', GREY)}")
        print(f"  {c('  Output: .mid .wav .mp3 .mp4 .ec .eic .ee .ecc', GREY)}")
        return
    use_human = "--human" in args
    use_machine = "--machine" in args
    use_async = "--async" in args
    recursive = "--recursive" in args
    vol_override = None
    if "--volume" in args:
        idx = args.index("--volume")
        if idx + 1 < len(args):
            vol_override = args[idx + 1]

    from ep_compiler.paths import resolve_inputs
    rest = [a for a in args if not a.startswith("--")]
    specs = rest if rest else ["/"]
    files = resolve_inputs(specs, recursive=recursive)
    if not files:
        print(f"  {c('No matching files found.', RED)}")
        return

    out = None
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args):
            out = args[idx + 1]

    for inp in files:
        ext = os.path.splitext(inp)[1].lower()
        file_out = out
        if len(files) > 1 and not out:
            file_out = inp.rsplit(".", 1)[0] + ".mid"
        elif not file_out:
            file_out = inp.rsplit(".", 1)[0] + ".mid"
        _compile_one(inp, file_out, ext, use_human, use_machine, use_async, vol_override)


def _compile_one(inp, out, ext, use_human, use_machine, use_async, vol_override):
    if ext in (".enx", ".ei", ".eci"):
        from ep_compiler.cli import compile_file as cf
        cf(inp, out, volume=float(vol_override) if vol_override else None, bpm_override=None)
        return
    if use_async:
        try:
            import asyncio
            from ep_compiler.async_compile import async_compile_file
            result = asyncio.run(async_compile_file(inp))
            if result:
                ev, bp = result
                print(f"  Async compiled: {len(ev)} events @ {bp}bpm")
                if out:
                    from ep_compiler.formats import export_midi
                    export_midi(ev, bp, out)
            return
        except Exception as e:
            print(f"  Async compile failed, falling back to sync: {e}")
    cmd = [sys.executable, str(EP_PATH), "compile", inp, "-o", out]
    if use_human:
        cmd.append("--human")
    if use_machine:
        cmd.append("--machine")
    if vol_override:
        cmd.extend(["--volume", vol_override])
    run_ep(cmd)

def do_play(args):
    if not args:
        print(f"  {c('Usage: play <spec> [--gui] [--window] [--detach] [--recursive]', D)}"); return
    use_gui = "--gui" in args
    use_window = "--window" in args
    use_detach = "--detach" in args
    recursive = "--recursive" in args

    from ep_compiler.paths import resolve_inputs
    rest = [a for a in args if not a.startswith("--")]
    specs = rest if rest else ["/"]
    files = resolve_inputs(specs, recursive=recursive)
    if not files:
        print(f"  {c('No matching files found.', RED)}")
        return

    for file in files:
        cmd = [sys.executable, str(PLAYER_PATH), file]
        if use_gui: cmd.append("--gui")
        print(f"  {c(f'♫ Playing: {os.path.basename(file)}', GREEN)}")
        sys.stdout.flush()
        try:
            if use_window or use_detach:
                from _launch import launch, set_log_dir
                set_log_dir(os.path.join(str(PROJECT_DIR), "logs"))
                proc, log = launch(cmd, window=use_window, detach=use_detach)
                if log:
                    print(f"  {c(f'Detached (pid {proc.pid}). Log: {log}', D)}")
                    print(f"  {c('View: launcher log ' + os.path.basename(log), D)}")
                elif proc:
                    print(f"  {c(f'Launched in new window (pid {proc.pid}).', D)}")
            else:
                subprocess.run(cmd, timeout=7200)
        except Exception:
            print(f"\n  {c('stopped', YELLOW)}")

def do_run(args):
    """run <file> [--gui] — launch the player in a dedicated console window."""
    if not args:
        print(f"  {c('Usage: run <file> [--gui] [--detach]', D)}"); return
    do_play(args + ["--window"])

def do_shell(args):
    """shell — open a second HELLFORGE shell in a new window."""
    from _launch import (
        launch,
        set_log_dir,
    )
    set_log_dir(os.path.join(str(PROJECT_DIR), "logs"))
    cmd = [sys.executable, str(PROJECT_DIR / "eshell.py")]
    proc, log = launch(cmd, window=True)
    if proc:
        print(f"  {c(f'HELLFORGE shell launched in new window (pid {proc.pid}).', GREEN)}")

def do_gui(args):
    do_play((args or ["--gui"]) if args else ["--gui"])

def do_info(args):
    if not args: print(f"  {c('Usage: info <file>', D)}"); return
    r = subprocess.run([sys.executable, str(EP_PATH), "info", strip_path(args[0])],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if r.stdout:
        for line in r.stdout.strip().split("\n"):
            print(f"  {line}")
    if r.stderr:
        print(f"  {c(r.stderr.strip()[:200], RED)}")

def _print_report(report):
    """Print a cli_cmds report: header in cyan, ✓ lines green, rest plain."""
    for i, line in enumerate(report.splitlines()):
        col = CYAN if i == 0 else (GREEN if line.lstrip().startswith("✓") else "")
        print(f"  {c(line, col)}")


def _out_flag(args):
    for i, a in enumerate(args):
        if a in ("-o", "--output") and i + 1 < len(args):
            return args[i + 1]
    return None


def do_stats(args):
    """stats <file> — notes, duration, note range, velocity, polyphony, density, channels."""
    if not args:
        print(f"  {c('Usage: stats <file>', D)}"); return
    from ep_compiler.cli_cmds import CLIError, stats_report
    try:
        _print_report(stats_report(strip_path(args[0])))
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_tracks(args):
    """tracks <file> — per-channel table (+ per-track when TRK metadata present)."""
    if not args:
        print(f"  {c('Usage: tracks <file>', D)}"); return
    from ep_compiler.cli_cmds import CLIError, tracks_report
    try:
        _print_report(tracks_report(strip_path(args[0])))
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_inspect(args):
    """inspect <file> [N] — show the first N events (default 12)."""
    if not args:
        print(f"  {c('Usage: inspect <file> [N]', D)}"); return
    n = 12
    if len(args) > 1:
        try:
            n = int(args[1])
        except ValueError:
            pass
    from ep_compiler.cli_cmds import CLIError, inspect_lines
    try:
        lines = inspect_lines(strip_path(args[0]), n)
        for line in lines:
            print(f"  {c(line, CYAN if line.startswith('HELLFORGE') else '')}")
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_new(args):
    """new <name> [-o <dir>] — scaffold a v5 project directory."""
    if not args:
        print(f"  {c('Usage: new <name> [-o <dir>]', D)}"); return
    name = strip_path(args[0])
    out_dir = _out_flag(args)
    from ep_compiler.cli_cmds import CLIError, scaffold_project
    try:
        root = scaffold_project(name, out_dir)
        for rel in ("index.ei", "parts/main.e", "README.md"):
            print(f"  {c('✓', GREEN)} {os.path.join(root, rel)}")
        print(f"  {c('v5 project scaffolded:', CYAN)} {root}")
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_transpose(args):
    """transpose <file> <semitones> [-o out] — shift all notes, write .mid (or .e with -o *.e)."""
    if len(args) < 2:
        print(f"  {c('Usage: transpose <file> <semitones> [-o out]', D)}"); return
    from ep_compiler.cli_cmds import CLIError, transpose_file
    try:
        _print_report(transpose_file(strip_path(args[0]), args[1], _out_flag(args)))
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_tempo(args):
    """tempo <file> <bpm> [-o out] — recompile at a new tempo, write .mid (or .e with -o *.e)."""
    if len(args) < 2:
        print(f"  {c('Usage: tempo <file> <bpm> [-o out]', D)}"); return
    from ep_compiler.cli_cmds import CLIError, tempo_file
    try:
        _print_report(tempo_file(strip_path(args[0]), args[1], _out_flag(args)))
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_merge(args):
    """merge <a> <b> [-o out] — concatenate two files, offset b after a, write .mid."""
    if len(args) < 2:
        print(f"  {c('Usage: merge <a> <b> [-o out]', D)}"); return
    from ep_compiler.cli_cmds import CLIError, merge_files
    try:
        _print_report(merge_files(strip_path(args[0]), strip_path(args[1]), _out_flag(args)))
    except CLIError as e:
        print(f"  {c(f'✗ {e}', RED)}")

def do_lint(args):
    """lint <spec> [--recursive] [--max <N>] — check E files for errors/warnings."""
    if not args:
        print(f"  {c('Usage: lint <spec> [--recursive] [--max <N>]', D)}")
        print(f"  {c('  <spec>: file | dir | / (all) | glob | multiple specs', GREY)}")
        return
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
        print(f"  {c('No matching files found.', RED)}")
        return

    stats = catalog_stats()
    stat_line = (f"HELLFORGE linter — catalog: {stats['errors']} errors, "
                 f"{stats['warnings']} warnings, {stats['info']} info")
    print(f"  {c(stat_line, D)}")
    total = 0
    for f in files:
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except Exception as e:
            print(f"  {c(f'Cannot read {f}: {e}', RED)}")
            continue
        diags = lint_source(text, path=f)
        total += len(diags)
        errors = sum(1 for d in diags if d["severity"] in (0, 1))
        warnings = sum(1 for d in diags if d["severity"] == 2)
        icon = c("✗", RED) if errors else (c("⚠", YELLOW) if warnings else c("✓", GREEN))
        print(f"\n  {icon} {f} — {len(diags)} diagnostics ({errors} errors, {warnings} warnings)")
        print(format_diags(diags, max_show=max_show))
    print(f"\n  {c(f'Scanned {len(files)} file(s), {total} diagnostics total.', D)}")


def do_generate(args):
    """generate index [v1|v2|v3|v4] | generate doc [-o <dir>]
    index: builds index.ei inheriting every .e file in cwd (default v4)
    doc:   copies the shipped docs (doc/, samples/, examples/, SYNTAX.md) into hdoc/"""
    if not args:
        print(f"  {c('Usage: generate index [v1|v2|v3|v4] [--recursive] [-o <name>]', D)}")
        print(f"  {c('       generate doc [-o <dir>]', D)}")
        return
    sub = args[0].lower()
    rest = args[1:]
    if sub == "index":
        _generate_index(rest)
    elif sub == "doc":
        _generate_doc(rest)
    else:
        print(f"  {c(f'Unknown generate target: {sub}', RED)} (use: index | doc)")


def _generate_index(args):
    """Build an index.ei that inherits all .e files in the current directory."""
    from ep_compiler.paths import resolve_inputs
    target = "v4"
    for v in ("v1", "v2", "v3", "v4"):
        if v in args:
            target = v
            break
    recursive = "--recursive" in args
    out_name = "index.ei"
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args):
            out_name = args[idx + 1]
    if not out_name.endswith(".ei"):
        out_name += ".ei"

    files = resolve_inputs([os.getcwd()], recursive=recursive)
    e_files = [f for f in files if f.endswith(".e") and os.path.dirname(f) == os.getcwd()]
    if not e_files:
        e_files = [f for f in files if f.endswith(".e")]
    if not e_files:
        print(f"  {c('No .e files found to index.', YELLOW)}")
        return
    e_files.sort()

    # Non-v4 target: convert parts via portbaby into parts/
    inherit_targets = []
    if target == "v4":
        for f in e_files:
            inherit_targets.append((os.path.basename(f), f))
    else:
        os.makedirs("parts", exist_ok=True)
        try:
            from plugins.portbaby.converter import convert_file
        except ImportError:
            print(f"  {c('portbaby not available — building v4 index instead.', YELLOW)}")
            for f in e_files:
                inherit_targets.append((os.path.basename(f), f))
        else:
            ver_map = {"v1": "v1_machine", "v2": "v2", "v3": "v3"}
            conv_ver = ver_map.get(target, "v4")
            for f in e_files:
                out_part = os.path.join("parts", os.path.basename(f))
                result = convert_file(f, conv_ver, make_project=False, show_report=False)
                if result and result.get("output"):
                    out_part = result["output"]
                inherit_targets.append((os.path.basename(out_part), out_part))

    lines = [
        f"/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */",
        f"// Generated index — {target} ({len(inherit_targets)} parts)",
        f"@bpm 120",
        "",
    ]
    for name, _path in inherit_targets:
        lines.append(f'inherit "{name}"')
    lines.append("")

    with open(out_name, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  {c('✓', GREEN)} {out_name} ({target}) — {len(inherit_targets)} parts")
    if target != "v4":
        print(f"  {c('  Parts converted to ' + target + ' in parts/', D)}")


def _generate_doc(args):
    """Copy the shipped docs into hdoc/ (doc/, samples/, examples/, SYNTAX.md)."""
    import shutil
    out_dir = "hdoc"
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args):
            out_dir = args[idx + 1]
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    srcs = [
        ("doc", "doc"),
        ("samples", "samples"),
        ("examples", "examples"),
        ("SYNTAX.md", "SYNTAX.md"),
    ]
    copied = 0
    for src_rel, dest_rel in srcs:
        src = os.path.join(str(PROJECT_DIR), src_rel)
        dest = os.path.join(out_dir, dest_rel)
        if not os.path.exists(src):
            print(f"  {c(f'Skipping (missing): {src_rel}', YELLOW)}")
            continue
        if os.path.isdir(src):
            if os.path.exists(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
        else:
            os.makedirs(os.path.dirname(dest) or out_dir, exist_ok=True)
            shutil.copy2(src, dest)
        copied += 1
    total_files = sum(len(files) for _, _, files in os.walk(out_dir))
    print(f"  {c('✓', GREEN)} Generated docs -> {out_dir} ({total_files} files)")
    print(f"  {c('  Includes: doc/, samples/, examples/, SYNTAX.md', D)}")


def do_convert(args):
    if not args:
        print(f"  {c('Usage: convert <spec> [--to v1|v2|v3|v4] [-o <out>] [--project] [--recursive]', D)}")
        print(f"  {c('  <spec>: file | dir | / (all) | glob | multiple specs', GREY)}")
        print(f"  {c('  --to:   syntax conversion (portbaby). Batch supported.', GREY)}")
        print(f"  {c('  Inputs: .e .ei .eci .enx .eic .mid .midi .ec .wav .mp3 .mp4 .mov .flac .ogg .aac .m4a', GREY)}")
        return

    from ep_compiler.paths import resolve_inputs, batch_suffix

    # Extract flags
    rest = [a for a in args if not a.startswith("--")]
    flags = set(a for a in args if a.startswith("--"))
    recursive = "--recursive" in flags
    project_mode = "--project" in flags
    target_ver = None
    if "--to" in args:
        idx = args.index("--to")
        if idx + 1 < len(args):
            target_ver = args[idx + 1].lower()
    out = None
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args):
            out = args[idx + 1]

    specs = rest if rest else ["/"]
    files = resolve_inputs(specs, recursive=recursive)
    if not files:
        print(f"  {c('No matching files found.', RED)}")
        return
    if len(files) > 1:
        print(f"  {c(f'♫ {len(files)} file(s) matched.', YELLOW)}")

    audio_exts = {".wav", ".mp3", ".mp4", ".m4a", ".mov", ".avi", ".flac", ".ogg", ".aac", ".wma", ".aiff"}
    project_formats = {".ei", ".enx", ".eci", ".eic"}

    for inp in files:
        ext = os.path.splitext(inp)[1].lower()

        # Syntax conversion (portbaby) — batch, outputs as <name>_v<ver>.e
        if target_ver:
            if ext not in (".e", ".ei", ".eic", ".enx", ".eci", ".machine", ".human"):
                print(f"  {c(f'Skipping (not E source): {inp}', YELLOW)}")
                continue
            try:
                from plugins.portbaby.converter import convert_file
            except ImportError:
                print(f"  {c('portbaby not available', RED)}")
                return
            ver_map = {"v1": "v1_machine", "v2": "v2", "v3": "v3", "v4": "v4"}
            conv_ver = ver_map.get(target_ver, target_ver)
            result = convert_file(inp, conv_ver, make_project=project_mode, show_report=False)
            if result and result.get("output"):
                print(f"  {c('✓', GREEN)} {inp} → {result['output']}")
            else:
                # Fallback output naming
                fallback = batch_suffix(inp, f"v{target_ver[-1]}")
                print(f"  {c(f'Converted: {inp} → {fallback}', D)}")
            continue

        # Format conversion (existing behavior)
        if ext in (".e",) or ext in project_formats:
            out_file = out or inp.rsplit(".", 1)[0] + ".mid"
            from ep_compiler.cli import compile_file as cf
            cf(inp, out_file)
        elif ext in (".mid", ".midi", ".ec"):
            if project_mode:
                from ep_compiler.cli import import_file
                out_dir = out or inp.rsplit(".", 1)[0] + "_project"
                import_file(inp, out_dir, project=True)
                continue
            out_file = out or inp.rsplit(".", 1)[0] + ".e"
            print(f"  {c('♫ Importing...', YELLOW)}")
            from ep_compiler.cli import import_file
            import_file(inp, out_file)
        elif ext in audio_exts:
            out_file = out or inp.rsplit(".", 1)[0] + ".e"
            print(f"  {c('♫ Transcribing audio (FFT-based)...', YELLOW)}")
            from ep_compiler.cli import import_file
            import_file(inp, out_file)
        else:
            print(f"  {c(f'Unknown format: {ext}', RED)}")

def do_encrypt(args):
    if not args:
        print(f"  {c('Usage: encrypt <file> [-o <out.ee>]', D)}"); return
    inp = strip_path(args[0])
    if not os.path.exists(inp):
        print(f"  {c(f'Not found: {inp}', RED)}"); return
    out = None
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args): out = args[idx + 1]
    if not out:
        out = inp.rsplit(".", 1)[0] + ".ee"
    # For .ei projects, bundle everything
    if inp.endswith(".ei"):
        cmd = [sys.executable, str(EP_PATH), "compile", inp, "-o", out]
    else:
        cmd = [sys.executable, str(EP_PATH), "compile", inp, "-o", out]
    run_ep(cmd, "Encrypting")

def do_ecc(args):
    """Compile + encrypt in one step: .e → .ecc (encrypted compiled)"""
    if not args:
        print(f"  {c('Usage: ecc <file> [-o <out.ecc>]', D)}"); return
    inp = strip_path(args[0])
    if not os.path.exists(inp):
        print(f"  {c(f'Not found: {inp}', RED)}"); return
    out = None
    if "-o" in args:
        idx = args.index("-o")
        if idx + 1 < len(args): out = args[idx + 1]
    if not out:
        out = inp.rsplit(".", 1)[0] + ".ecc"
    # Compile to .ec first, then encrypt to .ecc
    temp_ec = out.rsplit(".", 1)[0] + ".tmp.ec"
    subprocess.run([sys.executable, str(EP_PATH), "compile", inp, "-o", temp_ec],
                   capture_output=True, timeout=300)
    if os.path.exists(temp_ec):
        from ep_core import encrypt_e
        encrypt_e(temp_ec, out, method="aes-gcm")
        os.remove(temp_ec)
        sz = os.path.getsize(out) // 1024
        print(f"  {c('✓', GREEN)} {out} ({sz}KB)")
    else:
        print(f"  {c('✗ Compile step failed', RED)}")

def _get_pkg():
    global PKG
    if PKG is None:
        import ep_pkg
        PKG = ep_pkg
        PKG.init()
    return PKG


def _pkg_dispatch(pkg_type, args):
    """Generic dispatcher for mod/plugin commands."""
    pkg = _get_pkg()
    label = "Mods" if pkg_type == "mods" else "Plugins"

    if not args or args[0] in ("help", "--help"):
        print(f"  {c(f'{pkg_type} commands:', B)}")
        print(f"    {c('list', CYAN)}                 List installed")
        print(f"    {c('list-avail', CYAN)}            List available from pkglist")
        print(f"    {c('avail', CYAN)}                 Alias for list-avail")
        print(f"    {c('scan', CYAN)}                  Security scan all")
        print(f"    {c('update', CYAN)} <name>         Update specific")
        print(f"    {c('update-all', CYAN)}            Update all (with update_url)")
        print(f"    {c('install', CYAN)} <name>        Install from pkglist (local or registry)")
        print(f"    {c('fetch', CYAN)} <name>          Alias for install")
        print(f"    {c('remove', CYAN)} <name>         Uninstall")
        print(f"    {c('sign', CYAN)} <name>           Sign with author metadata")
        print(f"    {c('disable', CYAN)} <name>        Disable (skip on next boot)")
        print(f"    {c('enable', CYAN)} <name>         Enable (load on next boot)")
        print(f"    {c('version', CYAN)}               Check versions")
        return

    sub = args[0].lower()
    rest = args[1:]

    if sub == "list":
        pkg.list_installed(pkg_type)
    elif sub in ("list-avail", "avail"):
        pkg.list_available(pkg_type, detail="--detail" in rest or "-d" in rest)
    elif sub == "scan":
        d = pkg.MODS_DIR if pkg_type == "mods" else pkg.PLUGINS_DIR
        pkg.scan_directory(d, label)
    elif sub == "update":
        name = rest[0] if rest else ""
        if name:
            pkg.update(name, pkg_type)
        else:
            print(f"  {c('Usage: {pkg_type} update <name>', D)}")
    elif sub == "update-all":
        pkg.update("", pkg_type, all_flag=True)
    elif sub in ("install", "fetch"):
        name = rest[0] if rest else ""
        if name:
            pkg.fetch(name, pkg_type)
        else:
            print(f"  {c(f'Usage: {pkg_type} {sub} <name>', D)}")
    elif sub in ("remove", "uninstall", "rm", "delete"):
        name = rest[0] if rest else ""
        if name:
            confirm = input(f"  {c(f'Remove {name}?', YELLOW)} [{c('y/N',B)}] ").strip().lower()
            if confirm == "y":
                pkg.uninstall(name, pkg_type)
            else:
                print(f"  {c('skipped', D)}")
        else:
            print(f"  {c(f'Usage: {pkg_type} remove <name>', D)}")
    elif sub == "sign":
        name = rest[0] if rest else ""
        if name:
            from ep_core import sign_file
            target = pkg.MODS_DIR if pkg_type == "mods" else pkg.PLUGINS_DIR
            from ep_pkg import _resolve_package
            path = _resolve_package(name, target)
            if not path:
                print(f"  {c(f'Not found: {name}', RED)}")
            else:
                author = input(f"  {c('Author', CYAN)}> ").strip() or name
                social = {}
                i = input(f"  {c('Instagram', CYAN)}> ").strip()
                if i: social["Instagram"] = i
                d = input(f"  {c('Discord', CYAN)}> ").strip()
                if d: social["Discord"] = d
                try:
                    embed = path.is_dir()
                    if path.is_dir():
                        init_file = path / "__init__.py"
                        if init_file.exists():
                            sign_file(str(init_file), embed=True, author=author, social=social)
                            print(f"  {c('✓', GREEN)} {name} signed")
                        else:
                            print(f"  {c(f'No __init__.py in {name}', RED)}")
                    else:
                        sign_file(str(path), embed=True, author=author, social=social)
                        print(f"  {c('✓', GREEN)} {name} signed")
                except Exception as e:
                    print(f"  {c(f'Sign error: {e}', RED)}")
        else:
            print(f"  {c(f'Usage: {pkg_type} sign <name>', D)}")
    elif sub == "version":
        pkg.check_versions(pkg_type)
    elif sub == "disable":
        name = rest[0] if rest else ""
        if name:
            from ep_core import (
                _disabled_plugins,
                _disabled_mods,
                _save_disabled_state,
            )
            target = _disabled_mods if pkg_type == "mods" else _disabled_plugins
            target.add(name)
            _save_disabled_state()
            print(f"  {c('✓', GREEN)} {name} disabled (restart to take effect)")
        else:
            print(f"  {c(f'Usage: {pkg_type} disable <name>', D)}")
    elif sub == "enable":
        name = rest[0] if rest else ""
        if name:
            from ep_core import (
                _disabled_plugins,
                _disabled_mods,
                _save_disabled_state,
            )
            target = _disabled_mods if pkg_type == "mods" else _disabled_plugins
            target.discard(name)
            _save_disabled_state()
            print(f"  {c('✓', GREEN)} {name} enabled (restart to take effect)")
        else:
            print(f"  {c(f'Usage: {pkg_type} enable <name>', D)}")
    else:
        print(f"  {c(f'unknown {pkg_type} command: {sub}', RED)}")


def do_mod(args):
    _pkg_dispatch("mods", args)


def do_plugin(args):
    _pkg_dispatch("plugins", args)


def do_pkglist(args):
    pkg = _get_pkg()
    if not args or args[0] in ("help", "--help"):
        print(f"  {c('pkglist commands:', B)}")
        print(f"    {c('show', CYAN)}                   Show pkglist summary")
        print(f"    {c('detail', CYAN)}                  List all packages with details")
        print(f"    {c('install <name>', CYAN)}          Install package from pkglist")
        print(f"    {c('update', CYAN)}                 Fetch pkglist from the registry (HF_REGISTRY)")
        print(f"    {c('update file <path>', CYAN)}      Load pkglist from local file")
        print(f"    {c('update url <url>', CYAN)}        Sync pkglist from any URL")
        print(f"    {c('search <query>', CYAN)}          Search available packages")
        print(f"    {c('version', CYAN)}                 Check all versions")
        return

    sub = args[0].lower()
    rest = args[1:]

    if sub == "show":
        pl = pkg.load()
        m = len(pl.get("mods", {}))
        plg = len(pl.get("plugins", {}))
        ver = pl.get("version", "?")
        upd = pl.get("updated", "?")[:10]
        url = pl.get("url", "")
        print(f"  {c('📦 Package List', B)}  {c(f'v{ver}', D)}")
        print(f"    {c(f'{m} mods, {plg} plugins', CYAN)}  {c(f'(updated: {upd})', D)}")
        if url:
            print(f"    {c('sync:', D)} {c(url, GREY)}")
    elif sub == "detail":
        pkg.list_available("mods", detail=True)
        print()
        pkg.list_available("plugins", detail=True)
    elif sub == "update":
        if len(args) == 1:
            # pkglist update (no args) — fetch from the default registry URL
            if not pkg.REGISTRY_BASE:
                return print(f"  {c('⚠', YELLOW)} no default registry (set"
                             " HF_REGISTRY) — use: pkglist update url <url>")
            default_url = f"{pkg.REGISTRY_BASE}/pkglist.json"
            print(f"  {c('⟳', YELLOW)} fetching default pkglist from {c(default_url, D)}")
            pkg.sync_from_url(default_url)
            return
        if len(args) < 3:
            return print(f"  {c('Usage: pkglist update [file <path> | url <url>]', D)}")
        st = args[1].lower()
        src = " ".join(args[2:])
        if st == "file":
            pkg.sync_from_file(src)
        elif st == "url":
            pkg.sync_from_url(src)
        else:
            print(f"  {c('use: file or url', RED)}")
    elif sub == "search":
        q = " ".join(rest) if rest else ""
        pkg.search(q) if q else print(f"  {c('Usage: pkglist search <query>', D)}")
    elif sub == "install":
        name = " ".join(rest) if rest else ""
        if name:
            # Try plugins first, then mods
            found = False
            if name in pkg.load().get("plugins", {}):
                pkg.fetch(name, "plugins")
                found = True
            elif name in pkg.load().get("mods", {}):
                pkg.fetch(name, "mods")
                found = True
            if not found:
                print(f"  {c(f'Not found in pkglist: {name}', RED)}")
        else:
            print(f"  {c('Usage: pkglist install <name>', D)}")
    elif sub == "version":
        pkg.check_versions()
    elif sub == "reload":
        pkg.load(force_reload=True)
        print(f"  {c('pkglist reloaded from disk', GREEN)}")
    elif sub == "reset":
        confirm = input(f"  {c('Reset pkglist to default?', YELLOW)} [{c('y/N',B)}] ").strip().lower()
        if confirm == "y":
            default_path = Path(__file__).parent / "pkglist.default.json"
            if default_path.exists():
                import shutil
                shutil.copy(default_path, pkg.PKGLIST_PATH)
                pkg.load(force_reload=True)
                print(f"  {c('pkglist reset to default', GREEN)}")
            else:
                print(f"  {c('default pkglist not found at pkglist.default.json', YELLOW)}")
    elif sub == "clean":
        data = pkg.load()
        removed = {"mods": 0, "plugins": 0}
        for ptype in ("mods", "plugins"):
            keys = list(data.get(ptype, {}).keys())
            for k in keys:
                entry = data[ptype][k]
                if not k or not entry.get("version"):
                    del data[ptype][k]
                    removed[ptype] += 1
        pkg.save(data)
        total = removed["mods"] + removed["plugins"]
        print(f"  {c(f'pkglist cleaned: {total} entries removed', GREEN)}")
    elif sub == "check":
        data = pkg.load()
        issues = 0
        for ptype in ("mods", "plugins"):
            for name, entry in data.get(ptype, {}).items():
                if not entry.get("version"):
                    print(f"  {c(f'⚠ {ptype}/{name}: missing version', YELLOW)}")
                    issues += 1
                if not entry.get("description"):
                    print(f"  {c(f'⚠ {ptype}/{name}: missing description', YELLOW)}")
                    issues += 1
        if issues == 0:
            print(f"  {c('pkglist check: all entries valid', GREEN)}")
        else:
            print(f"  {c(f'pkglist check: {issues} issue(s) found', YELLOW)}")
    else:
        print(f"  {c(f'unknown pkglist command: {sub}', RED)}")


def do_audio(args):
    """Audio driver management: devices, renderer, config"""
    from ep_audio import (
        list_devices_table,
        set_device,
        audio_config,
        detect_devices,
    )
    if not args or args[0] in ("help", "--help"):
        print(f"  {c('audio commands:', B)}")
        print(f"    {c('devices', CYAN)}             List audio devices")
        print(f"    {c('set-device', CYAN)} <id>     Set active MIDI device")
        print(f"    {c('set-driver', CYAN)} <name>   Set audio renderer (fluidsynth/microsoft/numpy/ffmpeg)")
        print(f"    {c('set-sr', CYAN)} <hz>         Set sample rate (44100/48000/96000)")
        print(f"    {c('set-bit', CYAN)} <depth>     Set bit depth (16/24/32)")
        print(f"    {c('set-ch', CYAN)} <n>          Set channels (1/2)")
        print(f"    {c('config', CYAN)}              Show current audio config")
        return
    sub = args[0].lower()
    rest = args[1:]
    if sub == "devices":
        list_devices_table()
    elif sub == "set-device":
        if rest:
            set_device(int(rest[0]))
        else:
            print(f"  {c('Usage: audio set-device <id>', D)}")
    elif sub == "set-driver":
        if rest:
            driver = rest[0].lower()
            valid = {"fluidsynth", "microsoft", "numpy", "ffmpeg", "wasapi", "directsound"}
            if driver in valid:
                # Save to piano_synth config (persistent)
                import json
                synth_config = {"driver": driver}
                try:
                    with open(str(Path(__file__).parent / ".synth_config.json"), "w") as f:
                        json.dump(synth_config, f)
                except Exception:
                    pass
                print(f"  {c('Audio renderer set to', GREEN)} {driver}")
                if driver == "fluidsynth":
                    print(f"  {c('  Uses FluidSynth + generated SoundFont (best quality)', D)}")
                elif driver == "microsoft":
                    print(f"  {c('  Uses Microsoft GS Wavetable Synth (system default)', D)}")
                elif driver == "numpy":
                    print(f"  {c('  Uses Python numpy software synth (portable)', D)}")
                elif driver == "ffmpeg":
                    print(f"  {c('  Uses ffmpeg (lowest quality, always works)', D)}")
            else:
                print(f"  {c('Invalid driver. Choose: ' + ', '.join(sorted(valid)), RED)}")
        else:
            print(f"  {c('Usage: audio set-driver <name>', D)}")
    elif sub == "set-sr":
        if rest:
            audio_config.set("sample_rate", int(rest[0]))
            print(f"  {c('Sample rate set to', GREEN)} {rest[0]}Hz")
    elif sub == "set-bit":
        if rest:
            audio_config.set("bit_depth", int(rest[0]))
            print(f"  {c('Bit depth set to', GREEN)} {rest[0]}bit")
    elif sub == "set-ch":
        if rest:
            audio_config.set("channels", int(rest[0]))
            print(f"  {c('Channels set to', GREEN)} {rest[0]}")
    elif sub == "config":
        import json as _json
        driver = "fluidsynth"
        try:
            sp = Path(__file__).parent / ".synth_config.json"
            if sp.exists():
                with open(sp) as f:
                    driver = _json.load(f).get("driver", "fluidsynth")
        except Exception:
            pass
        print(f"  {c('Audio Config:', B)}")
        print(f"    Renderer: {c(driver, CYAN)}")
        print(f"    {audio_config.format_summary()}")
    else:
        print(f"  {c(f'unknown audio command: {sub}', RED)}")


def do_ezip(args):
    """EZip package management: install, list, info"""
    if not args:
        print(f"  {c('Usage: ezip <install|list|info> <file>', D)}")
        return
    sub = args[0].lower()
    rest = args[1:]
    try:
        from ep_core import (
            install_ezip,
            list_ezip_contents as lsc,
        )
        if sub == "install":
            f = " ".join(rest) if rest else ""
            ptype = "plugin" if "--plugin" in args else "mod"
            install_ezip(f, ptype) if f else print(f"  {c('Usage: ezip install <file.ezip>', D)}")
        elif sub in ("list", "info"):
            f = " ".join(rest) if rest else ""
            lsc(f) if f else print(f"  {c('Usage: ezip list <file.ezip>', D)}")
    except Exception as e:
        print(f"  {c(f'error: {e}', RED)}")


def do_gc(args):
    """Garbage collection: manage strategy, flush, clean, enable/disable"""
    from ep_core import (
        run_gc,
        _gc_strategies,
        _gc_enabled as _gc_flag,
        _last_compiled_events,
    )

    if not args:
        print(f"  {c('GC Commands:', B)}")
        print(f"    {c('gc enable', CYAN)}              Enable garbage collection")
        print(f"    {c('gc disable', CYAN)}             Disable garbage collection")
        print(f"    {c('gc status', CYAN)}              Show GC status")
        print(f"    {c('gc flush', CYAN)}               Run GC on last compiled events NOW")
        print(f"    {c('gc clean', CYAN)}               Run aggressive GC + purge")
        print(f"    {c('gc <strategy>', CYAN)}          Set strategy (default/aggressive)")
        return

    sub = args[0].lower()
    if sub == "enable":
        import ep_core as _ecore
        _ecore._gc_enabled = True
        print(f"  {c('GC enabled', GREEN)}")
    elif sub == "disable":
        import ep_core as _ecore
        _ecore._gc_enabled = False
        print(f"  {c('GC disabled', YELLOW)}")
    elif sub == "status":
        s = "enabled" if _gc_flag else "disabled"
        print(f"  {c('GC Status:', B)}")
        print(f"    State: {c(s, GREEN if _gc_flag else YELLOW)}")
        print(f"    Strategy: {c('default', CYAN)}")
        print(f"    Strategies: {c(', '.join(_gc_strategies.keys()), D)}")
        if _last_compiled_events:
            print(f"    Last compile: {len(_last_compiled_events)} events")
    elif sub == "flush":
        if not _last_compiled_events:
            print(f"  {c('No compiled events to GC', YELLOW)}")
            return
        ev = run_gc(_last_compiled_events, "default" if _gc_flag else "off")
        print(f"  {c('GC flush complete', GREEN)}")
    elif sub == "clean":
        if not _last_compiled_events:
            print(f"  {c('No compiled events to clean', YELLOW)}")
            return
        ev = run_gc(_last_compiled_events, "aggressive" if _gc_flag else "off")
        print(f"  {c('GC clean complete', GREEN)}")
    elif sub in _gc_strategies:
        print(f"  {c(f'GC strategy: {sub}', GREEN)}")
    else:
        print(f"  {c(f'Available: enable, disable, status, flush, clean, {list(_gc_strategies.keys())}', D)}")


def do_sys(args):
    """System management: status, deps, check, scan, reload, reset, panic"""
    from ep_core import (
        _plugins,
        _mods,
        _eshell_commands,
        _compilation_count,
        _plugin_configs,
        _gc_enabled as _gc_flag,
    )
    import time

    if not args:
        print(f"  {c('System Commands:', B)}")
        print(f"    {c('sys status', CYAN)}              Show system health + diagnostics")
        print(f"    {c('sys mem <N>', CYAN)}             Set memory limit in GB (default 2, range 1-64)")
        print(f"    {c('sys threads <N>', CYAN)}          Set thread limit (default 4, range 1-64)")
        print(f"    {c('sys deps', CYAN)}                Show plugin dependencies status")
        print(f"    {c('sys check', CYAN)}               Run full system diagnostic")
        print(f"    {c('sys scan', CYAN)}                Security scan plugins and mods")
        print(f"    {c('sys reload', CYAN)}              Reload all systems without restart")
        print(f"    {c('sys reset', CYAN)}               Factory reset (plugins, mods, configs)")
        print(f"    {c('sys strict <0|1|2>', CYAN)}      Signing enforcement: 0=off, 1=warn, 2=block")
        print(f"    {c('sys panic', CYAN)}               Emergency stop + safe mode")
        return

    sub = args[0].lower()

    if sub == "status":
        import platform
        impl = platform.python_implementation()
        uptime = time.time() - _eshell_start_time
        mem_usage = "<unknown>"
        try:
            import psutil
            mem_usage = f"{psutil.Process().memory_info().rss / 1024 / 1024:.0f} MB"
        except Exception:
            pass
        from ep_core import (
            _disabled_plugins,
            _disabled_mods,
        )
        disabled_plugins = len(_disabled_plugins)
        disabled_mods = len(_disabled_mods)
        e_files = len(list(PROJECT_DIR.glob("**/*.e")))
        mid_files = len(list(PROJECT_DIR.glob("**/*.mid")))
        py_files = len(list(PROJECT_DIR.glob("**/*.py")))
        # Resource limit display
        mem_str = _format_mem(_SYS_MEM_GB)
        thread_str = f"{_SYS_THREADS}T"
        heat = "🟢" if _SYS_MEM_GB >= 4 else "🟡" if _SYS_MEM_GB >= 2 else "🔴"
        print(f"  {c('System Status:', B)}")
        print(f"    {c('Uptime:', D)} {int(uptime//3600)}h {int((uptime%3600)//60)}m")
        print(f"    {c('Memory:', D)} {mem_usage} used / {mem_str} limit {heat}")
        print(f"    {c('Threads:', D)} {thread_str} max concurrent")
        print(f"    {c('Python:', D)} {impl} {platform.python_version()}")
        print(f"    {c('Plugins:', D)} {len(_plugins)} active, {disabled_plugins} disabled")
        print(f"    {c('Mods:', D)} {len(_mods)} active, {disabled_mods} disabled")
        print(f"    {c('Commands:', D)} {len(_eshell_commands)} plugin-registered")
        print(f"    {c('GC:', D)} {c('ON', GREEN) if _gc_flag else c('OFF', YELLOW)}")
        print(f"    {c('Compilations:', D)} {_compilation_count}")
        print(f"    {c('Files:', D)} {e_files} .e, {mid_files} .mid, {py_files} .py")

    elif sub == "mem":
        if len(args) < 2:
            fmt = _format_mem(_SYS_MEM_GB)
            print(f"  Memory limit: {fmt}  ({c('sys mem <N>', CYAN)} to change, e.g. 2G 512M 128K)")
            return
        old = _SYS_MEM_GB
        if _set_mem_limit(args[1]):
            fmt_old = _format_mem(old)
            fmt_new = _format_mem(_SYS_MEM_GB)
            heat = "HIGH" if _SYS_MEM_GB >= 4 else "MED" if _SYS_MEM_GB >= 2 else "LOW"
            print(f"  Memory limit: {fmt_old} → {c(fmt_new, GREEN)} {heat}")
            if _SYS_MEM_GB < 2:
                print(f"  {c('⚠ Low memory mode: expect reduced performance', YELLOW)}")
        else:
            print(f"  {c('Usage: sys mem <N>', D)}  e.g. 2G, 512M, 128K, 1024B")

    elif sub in ("threads", "thread", "cpu"):
        if len(args) < 2:
            print(f"  Thread limit: {_SYS_THREADS}  ({c('sys threads <N>', CYAN)} to change)")
            return
        try:
            val = int(args[1])
            old = _SYS_THREADS
            _set_thread_limit(val)
            print(f"  {c('Thread limit:', B)} {old} → {c(f'{_SYS_THREADS}', GREEN)} max concurrent")
        except ValueError:
            print(f"  {c('Usage: sys threads <N>', D)}  where N = 1-64")

    elif sub == "deps":
        print(f"  {c('Plugin Dependencies:', B)}")
        from ep_core import _plugin_dependencies
        if not _plugin_dependencies:
            print(f"    {c('No plugin dependencies registered', D)}")
        for plugin, deps in sorted(_plugin_dependencies.items()):
            for dep in deps:
                try:
                    __import__(dep.replace("-", "_"))
                    status = c("INSTALLED", GREEN)
                except ImportError:
                    status = c("MISSING", RED)
                print(f"    [{status}] {plugin} -> {dep}")
        # Also show pkglist deps
        try:
            with open(PROJECT_DIR / "pkglist.json") as f:
                pkgs = json.load(f)
            for ptype in ("plugins", "mods"):
                for name, info in pkgs.get(ptype, {}).items():
                    deps = info.get("dependencies", [])
                    if deps:
                        for dep in deps:
                            try:
                                __import__(dep.replace("-", "_"))
                                status = c("INSTALLED", GREEN)
                            except ImportError:
                                status = c("MISSING", RED)
                            print(f"    [{status}] (pkglist) {name} -> {dep}")
        except Exception:
            pass
        print(f"    {c('Run sys check for full diagnostic', D)}")

    elif sub == "check":
        print(f"  {c('System Diagnostic:', B)}")
        issues = 0
        checks_passed = 0

        # Check eshell start time
        checks_passed += 1
        print(f"  {c('✓', GREEN)} Shell running ({int(time.time() - _eshell_start_time)}s)")

        # Check plugin dirs exist
        for dir_name in ["plugins", "mods", "ep_compiler", "embedded_plugins"]:
            d = PROJECT_DIR / dir_name
            if d.exists():
                checks_passed += 1
            else:
                print(f"  {c('⚠', YELLOW)} Missing directory: {dir_name}")
                issues += 1

        # Check plugins loadable
        for name in ["lure", "portbaby"]:
            try:
                mod = __import__(f"plugins.{name}", fromlist=[""])
                if hasattr(mod, "register"):
                    checks_passed += 1
                else:
                    print(f"  {c('⚠', YELLOW)} Plugin {name}: no register()")
                    issues += 1
            except Exception as e:
                print(f"  {c('⚠', YELLOW)} Plugin {name}: {e}")
                issues += 1

        # Check pkglist integrity
        try:
            with open(PROJECT_DIR / "pkglist.json") as f:
                pkgs = json.load(f)
            for name in ["lure", "portbaby"]:
                if name in pkgs.get("plugins", {}):
                    checks_passed += 1
                else:
                    print(f"  {c('⚠', YELLOW)} {name} missing from pkglist")
                    issues += 1
        except Exception as e:
            print(f"  {c('⚠', YELLOW)} pkglist.json: {e}")
            issues += 1

        # Check remote API
        try:
            base = os.environ.get("HF_REGISTRY", "")
            if not base:
                print(f"  {c('⚠', YELLOW)} no remote registry configured"
                      " (set HF_REGISTRY) — skipping remote check")
            else:
                req = urllib.request.Request(
                    base + "/verify.json",
                    headers={"User-Agent": "E-Lang/Check/1.0"}
                )
                resp = urllib.request.urlopen(req, timeout=10)
                codes = json.loads(resp.read())
                expected = {"lure", "portbaby"}
                found = set(codes.keys())
                if expected.issubset(found):
                    checks_passed += 1
                else:
                    print(f"  {c('⚠', YELLOW)} Remote verification: missing {expected - found}")
                    issues += 1
        except Exception as e:
            print(f"  {c('⚠', YELLOW)} Remote API: {e}")

        # Check identity
        from ep_core import (
            identity_exists,
            load_identity,
        )
        if identity_exists():
            id = load_identity()
            print(f"  {c('✓', GREEN)} Identity: {id.get('name', '?')} (ED25519)")
            checks_passed += 1
        else:
            print(f"  {c('ℹ', CYAN)} No signing identity (run 'sign --setup')")

        # Check dependencies are installed
        import importlib
        for pkg in ["cryptography", "pygame", "mido"]:
            try:
                importlib.import_module(pkg)
                checks_passed += 1
            except ImportError:
                print(f"  {c('⚠', YELLOW)} Missing dependency: {pkg} (pip install {pkg})")
                issues += 1

        print(f"  {c(f'{checks_passed} checks passed', GREEN)}, {c(f'{issues} issues', RED if issues else GREEN)}")

    elif sub == "scan":
        print(f"  {c('Full System Scan', B)}")
        issues = 0
        from ep_core import ast_scan
        for pname, mod in list(_plugins.items()):
            try:
                fpath = getattr(mod, '__file__', None)
                if fpath and os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        content = f.read()
                    iss = ast_scan(content)
                    if iss:
                        print(f"  {c(f'⚠ Plugin {pname}: {len(iss)} issue(s)', YELLOW)}")
                        for line, desc in iss[:3]:
                            print(f"    line {line}: {desc}")
                        issues += len(iss)
                    else:
                        print(f"  {c(f'✓ Plugin {pname}: clean', GREEN)}")
            except Exception as e:
                print(f"  {c(f'⚠ Plugin {pname}: scan error: {e}', YELLOW)}")
                issues += 1
        for mname, mod in list(_mods.items()):
            try:
                fpath = getattr(mod, '__file__', None)
                if fpath and os.path.exists(fpath):
                    with open(fpath, 'rb') as f:
                        content = f.read()
                    iss = ast_scan(content)
                    if iss:
                        print(f"  {c(f'⚠ Mod {mname}: {len(iss)} issue(s)', YELLOW)}")
                        for line, desc in iss[:3]:
                            print(f"    line {line}: {desc}")
                        issues += len(iss)
                    else:
                        print(f"  {c(f'✓ Mod {mname}: clean', GREEN)}")
            except Exception as e:
                print(f"  {c(f'⚠ Mod {mname}: scan error: {e}', YELLOW)}")
                issues += 1
        if issues == 0:
            print(f"  {c('✓ System scan: clean', GREEN)}")
        else:
            print(f"  {c(f'⚠ System scan: {issues} issue(s)', YELLOW)}")

    elif sub == "reload":
        confirm = input(f"  {c('Reload all systems?', YELLOW)} [{c('y/N',B)}] ").strip().lower()
        if confirm != "y":
            print(f"  {c('Cancelled', D)}"); return
        _plugins.clear()
        _mods.clear()
        from ep_core import (
            _event_hooks,
            _gc_strategies,
            _plugin_directives,
            _boot_steps,
        )
        from ep_core import (
            _plugin_help_texts,
            _variable_handlers,
            _syntax_handlers,
        )
        for hl in _event_hooks.values():
            hl.clear()
        _plugin_directives.clear()
        _boot_steps.clear()
        _plugin_help_texts.clear()
        _variable_handlers.clear()
        _syntax_handlers.clear()
        _eshell_commands.clear()
        removed = 0
        for name in list(sys.modules.keys()):
            if name == "ep_core" or name.startswith("plugins.") or name.startswith("mods.") or name.startswith("encryption."):
                del sys.modules[name]
                removed += 1
        from ep_core import init as core_init
        core_init()
        try:
            from ep_core import _eshell_commands as new_cmds
            for name, (handler, help_text) in new_cmds.items():
                if name not in cmds:
                    cmds[name] = handler
        except Exception:
            pass
        print(f"  {c('✓ System reloaded', GREEN)}")

    elif sub == "reset":
        print(f"  {c('⚠ WARNING: This will DELETE all plugins, mods, and configs!', RED)}")
        confirm = input(f"  Type {c('RESET', B)} to confirm: ").strip()
        if confirm != "RESET":
            print(f"  {c('Cancelled', D)}"); return
        import shutil
        backup_dir = PROJECT_DIR / ".backup"
        backup_dir.mkdir(exist_ok=True)
        for d in ["plugins", "mods"]:
            src = PROJECT_DIR / d
            if src.exists():
                shutil.copytree(src, backup_dir / d, dirs_exist_ok=True)
        for f in [".plugin_config.json", ".fent_theme.json", ".ai_config.json"]:
            fp = PROJECT_DIR / f
            if fp.exists():
                shutil.copy(fp, backup_dir / f)
        for d in ["plugins", "mods"]:
            target = PROJECT_DIR / d
            if target.exists():
                for item in target.iterdir():
                    if item.name.startswith("_"):
                        continue
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
        for f in [".plugin_config.json", ".fent_theme.json", ".ai_config.json"]:
            fp = PROJECT_DIR / f
            if fp.exists():
                fp.unlink()
        print(f"  {c('✓ System reset to factory defaults', GREEN)}")
        print(f"  {c(f'  Backup saved to: {backup_dir}', D)}")

    elif sub in ("strict", "signing"):
        from ep_core import (
            get_strict_signing,
            set_strict_signing,
        )
        if not rest:
            level = get_strict_signing()
            labels = {0: "OFF — unsigned plugins load freely",
                      1: "WARN — unsigned plugins show warning",
                      2: "BLOCK — unsigned plugins rejected"}
            print(f"  Signing enforcement: {c(f'Level {level}', GREEN if level == 2 else YELLOW if level == 1 else RED)}")
            print(f"    {labels.get(level, '?')}")
            print(f"  Set: sys strict <0|1|2>")
            return
        try:
            val = int(rest[0])
            if set_strict_signing(val):
                labels = {0: "OFF", 1: "WARN", 2: "BLOCK"}
                color = GREEN if val == 2 else YELLOW if val == 1 else RED
                print(f"  Signing enforcement: {c(labels.get(val, '?'), color)}")
            else:
                print(f"  Invalid level. Use 0 (off), 1 (warn), or 2 (block)")
        except ValueError:
            print(f"  Usage: sys strict <0|1|2>")

    elif sub == "strict" and rest and rest[0] == "compile":
        """sys strict compile <file> — fail-fast compile surfacing every problem."""
        specs = rest[1:] or ["."]
        try:
            from ep_compiler.paths import resolve_inputs
            from ep_compiler.compile import compile_source
            from ep_compiler.mode_v1_machine import last_problems as _mlp
            from ep_compiler.mode_v1_human import last_problems as _hlp
            files = resolve_inputs(specs)
            for f in files:
                _mlp.clear(); _hlp.clear()
                try:
                    with open(f, encoding="utf-8", errors="replace") as fh:
                        text = fh.read()
                    ev, bp = compile_source(text, strict=True)
                    print(f"  {c('✓', GREEN)} {f} — strict compile OK, {len(ev)} events, {bp} BPM")
                except Exception as e:
                    print(f"  {c('✗', RED)} {f}:")
                    for ln in str(e).splitlines():
                        print(f"      {ln}")
        except Exception as e:
            print(f"  {c('✗', RED)} strict compile failed: {e}")

    elif sub == "panic":
        print(f"  {c('⚠ PANIC MODE', RED)}")
        confirm = input(f"  Type {c('PANIC', B)} to confirm emergency stop: ").strip()
        if confirm != "PANIC":
            print(f"  {c('Cancelled', D)}"); return
        try:
            import player as pl
            if hasattr(pl, 'stop_all'):
                pl.stop_all()
        except Exception:
            pass
        cache_dir = PROJECT_DIR / ".fent_cache"
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
        from ep_core import _gc_enabled as _gcflag
        _gcflag = False
        from ep_core import _plugin_configs as pc
        pc["_safe_mode"] = True
        from ep_core import _save_plugin_configs
        _save_plugin_configs()
        print(f"  {c('⚠ Panic mode active. Restart to recover.', YELLOW)}")
        print(f"  {c('  All plugins disabled. Caches cleared. GC disabled.', D)}")


def do_clear(args):
    os.system("cls" if os.name == "nt" else "clear")
    banner()

def do_help(args):
    lines = []
    lines.append(f"\n  {c('Commands:', B)}")
    lines.append(f"  {c('cd', CYAN)} <dir>       Change directory")
    lines.append(f"  {c('ls', CYAN)}            List files")
    lines.append(f"  {c('compile', CYAN)} <f>    Compile .e/.ei/.eci/.enx -> .mid/.wav/.ec/.eic")
    lines.append(f"  {c('', D)}  --human     Convert MACHINE -> HUMAN in .eic")
    lines.append(f"  {c('', D)}  --machine   Convert HUMAN -> MACHINE in .eic")
    lines.append(f"  {c('convert', CYAN)} <f>    Import MIDI/audio -> .e; --project for .ei project")
    lines.append(f"  {c('play', CYAN)} <f>       Play file")
    lines.append(f"  {c('gui', CYAN)} <f>        Play in glassmorphism window")
    lines.append(f"  {c('info', CYAN)} <f>       Show file stats")
    lines.append(f"  {c('stats', CYAN)} <f>       Notes, duration, range, velocity, polyphony, channels")
    lines.append(f"  {c('tracks', CYAN)} <f>      Per-channel table (+ per-track when TRK metadata present)")
    lines.append(f"  {c('inspect', CYAN)} <f> [N] Show first N events (default 12)")
    lines.append(f"  {c('new', CYAN)} <name>      Scaffold a v5 project directory ([-o <dir>])")
    lines.append(f"  {c('transpose', CYAN)} <f> <n>  Shift notes by semitones ([-o out])")
    lines.append(f"  {c('tempo', CYAN)} <f> <bpm> Recompile at a new tempo ([-o out])")
    lines.append(f"  {c('merge', CYAN)} <a> <b>   Concatenate two files into one MIDI ([-o out])")
    lines.append(f"  {c('sign', CYAN)} <f>       Sign file — local ED25519 signing")
    lines.append(f"  {c('encrypt', CYAN)} <f>    Encrypt to .ee")
    lines.append(f"  {c('ecc', CYAN)} <f>        Compile + encrypt to .ecc")
    lines.append(f"  {c('mod', CYAN)} <cmd>      Manage mods (list/avail/scan/update/fetch/remove/version)")
    lines.append(f"  {c('plugin', CYAN)} <cmd>   Manage plugins (list/avail/scan/update/fetch/remove/version)")
    lines.append(f"  {c('pkglist', CYAN)} <cmd>  Package registry (show/update/search/version/detail)")
    lines.append(f"  {c('ezip', CYAN)} <cmd>    Install .ezip packages (install/list)")
    lines.append(f"  {c('gc', CYAN)} <cmd>      Garbage collection (enable/disable/flush/clean/status)")
    lines.append(f"  {c('sys', CYAN)} <cmd>     System management (status/scan/reload/reset/panic)")
    lines.append(f"  {c('audio', CYAN)} <cmd>   Audio devices & config (devices/set-device/config)")
    lines.append(f"  {c('clear', CYAN)}          Clear screen")
    lines.append(f"  {c('exit', CYAN)}           Quit")

    # Append plugin help sections dynamically
    try:
        from ep_core import _plugin_help_texts
        for title, helplines in _plugin_help_texts:
            lines.append(f"")
            lines.append(f"  {c(title, B)}")
            for cmd, desc in helplines:
                lines.append(f"  {c(cmd, CYAN)}  {desc}")
    except Exception:
        pass

    lines.append(f"")
    lines.append(f"  {c('Built-in examples:', D)}")
    lines.append(f"    mod list             List installed mods")
    lines.append(f"    mod scan             Security scan all mods")
    lines.append(f"    plugin list-avail    List available plugins")
    lines.append(f"    pkglist search rush  Search packages")
    lines.append(f"    fetch cool-plugin    Download from registry")

    print("\n".join(lines))

# Track eshell start time for uptime
_eshell_start_time = 0
def main():
    global _eshell_start_time
    import time
    import threading as _threading

    # ── Core integrity digest — recomputed on every CLI start ──
    try:
        from ep_compiler.security_hash import boot_check
        boot_check(print)
    except Exception:
        pass

    # ── Project directory resolution: --project flag > HELLFORGE_PROJECT env > cwd ──
    project_dir = None
    if "--project" in sys.argv:
        idx = sys.argv.index("--project")
        if idx + 1 < len(sys.argv):
            project_dir = strip_path(sys.argv[idx + 1])
    if not project_dir:
        project_dir = os.environ.get("HELLFORGE_PROJECT", "")
    if project_dir:
        project_dir = os.path.abspath(project_dir)
        if os.path.isdir(project_dir):
            try:
                os.chdir(project_dir)
            except Exception:
                pass

    _eshell_start_time = time.time()
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    _load_sys_limits()  # load saved memory/thread limits
    try:
        from ep_core import (
            restore_all,
            init as core_init,
            show_boot_progress,
        )
        restore_all()
        core_init()
        show_boot_progress()
    except Exception:
        pass
    banner()

    # Auto-update check: compare installed vs pkglist versions
    try:
        from ep_pkg import (
            load as _pkg_load,
            _find_packages as _find_pkgs,
            get_installed_meta as _get_meta,
        )
        from ep_core import (
            PLUGINS_DIR,
            MODS_DIR,
        )
        _pkg_data = _pkg_load()
        _updates = []
        for _ptype, _dir in [("plugins", PLUGINS_DIR), ("mods", MODS_DIR)]:
            if not os.path.isdir(_dir):
                continue
            for _name, _path in _find_pkgs(_dir):
                _installed = _get_meta(_path)
                _avail = _pkg_data.get(_ptype, {}).get(_name, {})
                if _installed and _avail:
                    _iv = _installed.get("version", "?")
                    _av = _avail.get("version", "?")
                    if _iv != "?" and _av != "?" and _iv != _av:
                        _updates.append((_name, _iv, _av))
        if _updates:
            _parts = ", ".join(f"{_n} v{_i} → v{_a}" for _n, _i, _a in _updates)
            print(f"  {c('⬆', YELLOW)} {len(_updates)} update(s) available: {_parts}")
    except Exception:
        pass

    # Auto-login: check saved session
    try:
        from ep_core import (
            load_session,
            check_session_ip,
            clear_session,
            save_session,
        )
        from ep_core import (
            identity_exists,
            load_identity,
        )
        session = load_session()
        if session:
            username = session.get("username", "?")
            session, ip_changed, old_ip = check_session_ip()
            if ip_changed:
                print(f"  {YELLOW}ℹ IP changed since last login{R}")
                print(f"  {YELLOW}  Was: {old_ip}{R}")
                print(f"  {YELLOW}  Current session user: {username}{R}")
            print(f"  {GREEN}✓ Logged in as: {username}{R}")
        else:
            if sys.stdin.isatty():
                print(f"  {RED}HELLFORGE> No active login session.{R}")
                if identity_exists():
                    id = load_identity()
                    id_name = id.get("name", "?") if id else "?"
                    print(f"  {D}  Local identity: {id_name} (not logged in){R}")
                    print(f"  {D}  Run 'sign --login' to sign in{R}")
                else:
                    print(f"  {D}  First time? Run 'sign --setup' to create an account{R}")
                    print(f"  {D}  Already registered? Run 'sign --login'{R}")
                r = input(f"  Login? [{c('y/N',B)}] ").strip().lower()
                if r == "y":
                    print(f"  {D}  Remote identity login is not part of the"
                          " open-source release (registry auth removed)."
                          f"  Local signing works: {GREEN}sign <file>{R}")
                else:
                    print(f"  {D}  Local signing works: 'sign <file>' — no"
                          " remote account needed.{R}")
    except Exception:
        pass

    cmds = {
        "cd": do_cd, "chdir": do_cd,
        "ls": do_ls, "dir": do_ls,
        "compile": do_compile, "build": do_compile,
        "play": do_play,
        "run": do_run,
        "shell": do_shell,
        "gui": do_gui, "glass": do_gui,
        "info": do_info,
        "stats": do_stats,
        "tracks": do_tracks,
        "inspect": do_inspect,
        "new": do_new,
        "transpose": do_transpose,
        "tempo": do_tempo,
        "merge": do_merge,
        "convert": do_convert,
        "lint": do_lint, "check": do_lint, "lintfile": do_lint,
        "generate": do_generate, "gen": do_generate,
        "encrypt": do_encrypt,
        "ecc": do_ecc,
        "mod": do_mod,
        "plugin": do_plugin, "plugins": do_plugin,
        "audio": do_audio,
        "ezip": do_ezip,
        "gc": do_gc,
        "sys": do_sys,
        "pkglist": do_pkglist,
        "clear": do_clear, "cls": do_clear,
        "help": do_help, "?": do_help,
    }

    # Load plugin commands dynamically
    try:
        from ep_core import _eshell_commands
        for name, (handler, help_text) in _eshell_commands.items():
            if name not in cmds:
                cmds[name] = handler
    except Exception:
        pass

    # Start hot-reload file watcher
    def _start_plugin_watcher():
        """Background thread watching plugins/, mods/, ep_compiler/, and root .py files for changes."""
        watched_dirs = [
            PROJECT_DIR / "plugins",
            PROJECT_DIR / "mods",
            PROJECT_DIR / "ep_compiler",
            PROJECT_DIR / "tools",
        ]
        # Also watch root .py files
        root_extra = list(PROJECT_DIR.glob("*.py")) + list(PROJECT_DIR.glob("*.lua"))

        def _snapshot():
            snap = {}
            for d in watched_dirs:
                if not d.exists():
                    continue
                try:
                    for f in d.rglob("*"):
                        if f.is_file() and f.suffix in (".py", ".lua", ".json", ".e", ".ei", ".enx"):
                            try:
                                snap[str(f.resolve())] = f.stat().st_mtime
                            except Exception:
                                pass
                except Exception:
                    pass
            for f in root_extra:
                if f.exists():
                    try:
                        snap[str(f.resolve())] = f.stat().st_mtime
                    except Exception:
                        pass
            return snap

        last_snap = _snapshot()
        _debounce_until = 0.0

        def _watcher_loop():
            nonlocal last_snap, _debounce_until
            while True:
                time.sleep(1)
                try:
                    now = time.time()
                    if now < _debounce_until:
                        last_snap = _snapshot()
                        continue
                    # Skip if _auto_reload() was just called by fetch/install
                    try:
                        from ep_pkg import _last_manual_reload
                        if now - _last_manual_reload < 3.0:
                            last_snap = _snapshot()
                            continue
                    except Exception:
                        pass
                    new_snap = _snapshot()
                    if new_snap == last_snap:
                        continue
                    changed = []
                    for path, mtime in new_snap.items():
                        if path not in last_snap:
                            changed.append(f"+{os.path.basename(path)[:30]}")
                        elif last_snap[path] != mtime:
                            changed.append(f"~{os.path.basename(path)[:30]}")
                    for path in last_snap:
                        if path not in new_snap:
                            changed.append(f"-{os.path.basename(path)[:30]}")
                    if not changed:
                        last_snap = new_snap
                        continue
                    last_snap = new_snap
                    change_str = ", ".join(changed[:5])
                    if len(changed) > 5:
                        change_str += f" ... (+{len(changed)-5} more)"
                    try:
                        # Forcefully reload ep_core from disk (not cached)
                        for name in list(sys.modules.keys()):
                            if name == "ep_core" or name.startswith("plugins.") or name.startswith("mods.") or name.startswith("encryption.") or name.startswith("ep_compiler."):
                                del sys.modules[name]
                        import ep_core as _ecore
                        _ecore._plugins.clear(); _ecore._mods.clear()
                        for hl in _ecore._event_hooks.values(): hl.clear()
                        _ecore._plugin_directives.clear(); _ecore._boot_steps.clear()
                        _ecore._plugin_help_texts.clear(); _ecore._variable_handlers.clear()
                        _ecore._syntax_handlers.clear()
                        _ecore._eshell_commands.clear()
                        _ecore.init()
                        _ecore.show_boot_progress()
                        for name, (handler, help_text) in _ecore._eshell_commands.items():
                            if name not in cmds:
                                cmds[name] = handler
                        _debounce_until = time.time() + 3.0
                        print(f"  {c('↻', CYAN)} hot-reloaded: {change_str}")
                    except Exception as e:
                        print(f"\r  {c('↻', YELLOW)} hot-reload error: {e}{' '*40}", flush=True)
                except Exception as e:
                    print(f"\r  {c('↻', RED)} watcher error: {e}{' '*40}", flush=True)

        t = _threading.Thread(target=_watcher_loop, daemon=True, name="plugin-watcher")
        t.start()
        print(f"  {c('Watcher active:', D)} monitoring {len(last_snap)} files every 1s")

    _start_plugin_watcher()

    while True:
        try:
            cwd = os.getcwd()
            if len(cwd) > 50: cwd = "..." + cwd[-47:]
            user = input(f"  {c('HELLFORGE', RED)} {c(cwd, GREY)} {c('>', RED)} ").strip()
        except EOFError:
            print(f"\n  {c('bye', GREY)}"); break
        except KeyboardInterrupt:
            print(f"\n  {c('^C', D)}"); continue
        if not user: continue
        if user.lower() in ("exit", "quit"):
            print(f"  {c('bye', CYAN)}"); break
        parts = user.split()
        cmd = parts[0].lower()
        args = parts[1:]
        if cmd in cmds:
            try: cmds[cmd](args)
            except Exception as e: print(f"  {c(f'error: {e}', RED)}")
        else:
            print(f"  {c(f'unknown: {cmd}', RED)} {c('try help', D)}")

if __name__ == "__main__":
    main()
