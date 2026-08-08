"""All E Language tool implementations: project, write, edit, delete, read, ls, compile, play, grep, rename, validate, undo, batch, git."""

import os
import re
import subprocess
import sys
from datetime import datetime

from .config import (
    c, D, B, R, GREEN, YELLOW, RED, CYAN,
    PROJECT_DIR, GENERATED_DIR, EP_PATH, CURRENT_PROJECT, DELETE_PERM, VERSIONS
)


def tool_project(name):
    from .config import CURRENT_PROJECT as cp
    import ai.session as s

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe = re.sub(r'[^a-zA-Z0-9]+', '_', name)[:30].strip("_") or "project"
    proj = os.path.join(GENERATED_DIR, f"{safe}_{ts}")
    os.makedirs(os.path.join(proj, "parts"), exist_ok=True)
    os.makedirs(os.path.join(proj, "output"), exist_ok=True)

    import ai.config as cfg
    cfg.CURRENT_PROJECT = proj

    rel = os.path.relpath(proj, PROJECT_DIR)
    print(f"  > {c('Project created:', CYAN)} {c(rel, D)}")
    s.save_project_list()
    s.save_session_snapshot("project_" + safe)
    with open(os.path.join(proj, "index.ei"), "w") as f:
        f.write(f'// {name}\nproject "{name}"\ntempo 120\n\ninclude "parts/main.e" as main\n\nsection "Main" {{\n    play main\n}}\n')
    with open(os.path.join(proj, "parts", "main.e"), "w") as f:
        f.write("#MACHINE\n// Main theme\n@bpm 120\n\nT0 N60 D500 V0.8\n")
    return f"Created project {rel}"


def tool_write(path, content):
    from .config import CURRENT_PROJECT
    if not CURRENT_PROJECT:
        print(f"  > {c('No project — create one first with: project <name>', RED)}")
        return "No project"
    path = path.strip().strip('"').strip("'")
    full = os.path.join(CURRENT_PROJECT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    old_content = ""
    if os.path.exists(full):
        with open(full, "r") as f:
            old_content = f.read()
    content = content.strip() + "\n"
    with open(full, "w") as f:
        f.write(content)
    rel = os.path.relpath(full, PROJECT_DIR)
    old_lines = len(old_content.split("\n")) if old_content else 0
    new_lines = len(content.split("\n"))
    added = max(0, new_lines - old_lines)
    removed = max(0, old_lines - new_lines)
    delta = ""
    if added:
        delta += c(f" +{added}", GREEN)
    if removed:
        delta += c(f" -{removed}", RED)
    if not delta:
        delta = c(" +new", D)
    print(f"  > {c('Wrote', CYAN)} {c(rel, D)}{delta}")
    return f"Written {rel} (+{added}/-{removed})"


def tool_edit(path, old_text, new_text):
    from .config import CURRENT_PROJECT
    path = path.strip().strip('"').strip("'")
    full = os.path.join(CURRENT_PROJECT, path)
    if not os.path.exists(full):
        return f"File not found: {path}"
    with open(full, "r") as f:
        content = f.read()
    if old_text not in content:
        return f"Text not found in {path}"
    new_content = content.replace(old_text, new_text, 1)
    old_l = len(content.split("\n"))
    new_l = len(new_content.split("\n"))
    with open(full, "w") as f:
        f.write(new_content)
    rel = os.path.relpath(full, PROJECT_DIR)
    added = max(0, new_l - old_l)
    removed = max(0, old_l - new_l)
    delta = ""
    if added:
        delta += c(f" +{added}", GREEN)
    if removed:
        delta += c(f" -{removed}", RED)
    print(f"  > {c('Edited', YELLOW)} {c(rel, D)}{delta}")
    return f"Edited {rel}"


def tool_delete(path):
    from .config import (
        CURRENT_PROJECT,
        DELETE_PERM as dp,
    )
    import ai.config as cfg

    path = path.strip().strip('"').strip("'")
    full = os.path.join(CURRENT_PROJECT, path)
    if not os.path.exists(full):
        return f"File not found: {path}"
    rel = os.path.relpath(full, PROJECT_DIR)
    if cfg.DELETE_PERM == "prompt":
        ans = input(f"  > {c('Delete', RED)} {c(rel, D)}? [{c('all',B)}/{c('1',B)}/{c('n',B)}] ").strip().lower()
        if ans in ("all", "a"):
            cfg.DELETE_PERM = "all"
        elif ans in ("n", "no", ""):
            return "Skipped"
    elif cfg.DELETE_PERM == "once":
        cfg.DELETE_PERM = "prompt"
    os.remove(full)
    print(f"  > {c('Deleted', RED)} {c(rel, D)}")
    return f"Deleted {rel}"


def tool_read(path):
    from .config import CURRENT_PROJECT
    path = path.strip().strip('"').strip("'")
    full = os.path.join(CURRENT_PROJECT, path)
    if not os.path.exists(full):
        return f"File not found: {path}"
    with open(full, "r") as f:
        content = f.read()
    lines = content.split("\n")
    rel = os.path.relpath(full, PROJECT_DIR)
    print(f"  > {c('Read', CYAN)} {c(rel, D)} ({len(lines)} lines)")
    for i, line in enumerate(lines[:5], 1):
        print(f"    {c(f'{i}:', D)} {line[:90]}")
    if len(lines) > 5:
        print(f"    {c(f'... {len(lines)-5} more lines', D)}")
    return f"Read {rel}"


def tool_ls(subdir=""):
    from .config import CURRENT_PROJECT
    base = os.path.join(CURRENT_PROJECT, subdir) if subdir else CURRENT_PROJECT
    total = 0
    files = 0
    items = []
    for root, dirs, fnames in sorted(os.walk(base)):
        for f in sorted(fnames):
            if f.endswith((".e", ".ei", ".ec")):
                fp = os.path.join(root, f)
                with open(fp) as fh:
                    lc = len(fh.readlines())
                total += lc
                files += 1
                items.append((lc, os.path.relpath(fp, PROJECT_DIR)))
    print(f"  > {c(f'{files} files, {total} lines', CYAN)}")
    for lc, rel_path in items:
        print(f"    {c(f'{lc:4d}', D)} {rel_path}")
    return f"{files} files, {total} lines"


def tool_compile(path=None):
    from .config import CURRENT_PROJECT
    if not CURRENT_PROJECT:
        return "No project"
    if not path:
        for f in os.listdir(CURRENT_PROJECT):
            if f.endswith(".ei"):
                path = f
                break
        if not path:
            for f in os.listdir(CURRENT_PROJECT):
                if f.endswith(".e"):
                    path = f
                    break
    if not path:
        return "No .ei or .e file found"
    full = os.path.join(CURRENT_PROJECT, path)
    out = re.sub(r'\.(ei?)$', '.mid', full)
    r = subprocess.run(
        [sys.executable, EP_PATH, "compile", full, "-o", out],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300,
    )
    if r.returncode == 0:
        rel = os.path.relpath(out, PROJECT_DIR)
        sz = os.path.getsize(out) / 1024
        print(f"  > {c('Compiled:', YELLOW)} {c(rel, D)} ({sz:.0f} KB)")
        return f"Compiled to {rel}"
    else:
        err = r.stderr.strip()[:200]
        print(f"  > {c('Compile error:', RED)} {err}")
        return f"Error: {err}"


def tool_play(path=None):
    from .config import CURRENT_PROJECT
    if not CURRENT_PROJECT:
        print(f"  > {c('No project — use project <name> first', RED)}")
        return "No project"
    if not path:
        for f in os.listdir(CURRENT_PROJECT):
            if f.endswith((".e", ".ei")):
                path = f
                break
    full = os.path.join(CURRENT_PROJECT, path)
    print(f"  > {c('Playing:', GREEN)} {c(os.path.relpath(full, PROJECT_DIR), D)}")
    try:
        subprocess.run([sys.executable, EP_PATH, "play", full], timeout=600)
    except KeyboardInterrupt:
        print(f"  {c('Stopped.', YELLOW)}")
    return "Playback complete"


def tool_plan(prompt):
    return None, f"""You are a piano composer and music theorist. Output ONLY a structured musical plan.
Cover: key signature, tempo, time signature, structure/sections, chord progressions for each section,
left hand pattern, right hand character, dynamics arc. Be specific with chords (i, IV, V etc) and structure.

Plan: {prompt}"""


def tool_undo(path=None):
    from .config import (
        CURRENT_PROJECT,
        VERSIONS as v,
    )
    import ai.config as cfg

    if not path:
        undoable = [k for k, val in cfg.VERSIONS.items() if val]
        if not undoable:
            return "Nothing to undo."
        print(f"  > {c('Files with history:', YELLOW)}")
        for f in undoable:
            rel = os.path.relpath(f, PROJECT_DIR)
            print(f"    {c(rel, D)} ({len(cfg.VERSIONS[f])} versions)")
        return f"{len(undoable)} files with history"
    full = os.path.join(CURRENT_PROJECT, path) if not os.path.isabs(path) else path
    if full not in cfg.VERSIONS or not cfg.VERSIONS[full]:
        return f"No history for {path}"
    old = cfg.VERSIONS[full].pop()
    with open(full, "r") as f:
        curr = f.read()
    with open(full, "w") as f:
        f.write(old)
    rel = os.path.relpath(full, PROJECT_DIR)
    print(f"  > {c('Restored:', YELLOW)} {c(rel, D)}")
    return f"Undone {rel}"


def tool_grep(pattern, glob="*.e"):
    from .config import CURRENT_PROJECT
    import fnmatch
    if not CURRENT_PROJECT:
        return "No project"
    matches = []
    for root, _, fnames in os.walk(CURRENT_PROJECT):
        for f in fnames:
            if not fnmatch.fnmatch(f, glob):
                continue
            fp = os.path.join(root, f)
            with open(fp, "r", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        rel = os.path.relpath(fp, PROJECT_DIR)
                        matches.append((rel, i, line.rstrip()))
    if not matches:
        print(f"  > {c('No matches for:', YELLOW)} {pattern}")
        return "0 matches"
    print(f"  > {c('Grep:', CYAN)} {pattern} ({len(matches)} matches)")
    for rel, ln, line in matches[:20]:
        print(f"    {c(f'{rel}:{ln}', D)} {line[:80]}")
    if len(matches) > 20:
        print(f"    {c(f'... {len(matches)-20} more', D)}")
    return f"{len(matches)} matches"


def tool_rename(old_path, new_path):
    from .config import CURRENT_PROJECT
    old_path = old_path.strip().strip('"').strip("'")
    new_path = new_path.strip().strip('"').strip("'")
    old_full = os.path.join(CURRENT_PROJECT, old_path)
    new_full = os.path.join(CURRENT_PROJECT, new_path)
    if not os.path.exists(old_full):
        return f"Not found: {old_path}"
    os.makedirs(os.path.dirname(new_full), exist_ok=True)
    _save_version(old_path)
    os.rename(old_full, new_full)
    old_rel = os.path.relpath(old_full, PROJECT_DIR)
    new_rel = os.path.relpath(new_full, PROJECT_DIR)
    print(f"  > {c('Renamed:', CYAN)} {c(old_rel, D)} -> {c(new_rel, D)}")
    for root, _, fnames in os.walk(CURRENT_PROJECT):
        for f in fnames:
            if f.endswith(".ei"):
                fp = os.path.join(root, f)
                with open(fp, "r") as fh:
                    content = fh.read()
                old_ref = old_path.replace("\\", "/")
                if old_ref in content:
                    new_ref = new_path.replace("\\", "/")
                    content = content.replace(old_ref, new_ref)
                    with open(fp, "w") as fh:
                        fh.write(content)
                    print(f"      {c('Updated ref in', D)} {c(os.path.relpath(fp, PROJECT_DIR), D)}")
    return f"Renamed {old_rel} -> {new_rel}"


def tool_validate(path=None):
    from .config import CURRENT_PROJECT
    target = os.path.join(CURRENT_PROJECT, path) if path else CURRENT_PROJECT
    if not os.path.exists(target):
        return f"Not found: {path}"
    TOOL_PATTERNS = {
        "machine_event": re.compile(r"^T\d+\s+N\d+"),
        "human_play": re.compile(r"^play (note|chord)\("),
        "bpm": re.compile(r"@(?:bpm|tempo)"),
        "comment": re.compile(r"^//"),
        "ei_directive": re.compile(r"^(project|include|section)"),
    }
    files_checked = 0
    total_issues = 0
    issues = []
    for root, _, fnames in os.walk(target):
        for f in fnames:
            if not f.endswith((".e", ".ei")):
                continue
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, PROJECT_DIR)
            files_checked += 1
            with open(fp, "r", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    line_s = line.strip()
                    if not line_s or line_s.startswith("//") or line_s.startswith("#"):
                        continue
                    if f.endswith(".ei"):
                        if not TOOL_PATTERNS["ei_directive"].search(line_s) and \
                           not TOOL_PATTERNS["comment"].match(line_s) and \
                           not line_s.startswith("}") and not line_s.startswith("{") and \
                           not line_s.startswith("play") and not line_s.startswith("wait") and \
                           not line_s.startswith("tempo") and not line_s.startswith("include_dir"):
                            issues.append((rel, i, "Unknown .ei directive", line_s[:60]))
                            total_issues += 1
                    else:
                        if not TOOL_PATTERNS["machine_event"].search(line_s) and \
                           not TOOL_PATTERNS["human_play"].search(line_s) and \
                           not TOOL_PATTERNS["bpm"].search(line_s) and \
                           not line_s.startswith("@") and \
                           not line_s.startswith("]"):
                            issues.append((rel, i, "Suspicious line", line_s))
                            total_issues += 1
    print(f"  > {c('Validate:', YELLOW)} {files_checked} files, {total_issues} issues")
    for rel, ln, kind, line in issues[:10]:
        print(f"    {c(f'{rel}:{ln}', D)} {c(kind, RED)} {line[:60]}")
    if issues:
        return f"{total_issues} issues in {files_checked} files"
    print(f"    {c('All clean', GREEN)}")
    return "All clean"


def tool_git(args):
    from .config import CURRENT_PROJECT
    if not args:
        args = "status"
    full_args = args.split()
    try:
        r = subprocess.run(
            ["git"] + full_args,
            cwd=CURRENT_PROJECT,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        out = (r.stdout + r.stderr).strip()
        if out:
            print(f"  > {c('Git', CYAN)} {c('$ git ' + args, D)}")
            for line in out.split("\n")[:20]:
                print(f"    {line}")
            if len(out.split("\n")) > 20:
                print(f"    {c('...', D)}")
        return out[:500] if out else "(empty)"
    except FileNotFoundError:
        return "Git not installed"
    except subprocess.TimeoutExpired:
        return "Git timed out"


def tool_batch_edit(old_text, new_text, glob="*.e"):
    from .config import CURRENT_PROJECT
    import fnmatch
    if not CURRENT_PROJECT:
        return "No project"
    edited = []
    for root, _, fnames in os.walk(CURRENT_PROJECT):
        for f in fnames:
            if not fnmatch.fnmatch(f, glob):
                continue
            fp = os.path.join(root, f)
            with open(fp, "r") as fh:
                content = fh.read()
            if old_text not in content:
                continue
            _save_version(os.path.relpath(fp, CURRENT_PROJECT))
            new_content = content.replace(old_text, new_text)
            with open(fp, "w") as fh:
                fh.write(new_content)
            rel = os.path.relpath(fp, PROJECT_DIR)
            edited.append((rel, content.count(old_text)))
    if not edited:
        print(f"  > {c('No matches for:', YELLOW)} {old_text}")
        return "0 files"
    total = sum(c for _, c in edited)
    print(f"  > {c('Batch edit:', CYAN)} {len(edited)} files, {total} replacements")
    for rel, count in edited:
        print(f"    {c(rel, D)} ({count} replacements)")
    return f"{len(edited)} files, {total} replacements"


def _save_version(path):
    from .config import (
        CURRENT_PROJECT,
        VERSIONS as v,
    )
    import ai.config as cfg
    full = os.path.join(CURRENT_PROJECT, path) if not os.path.isabs(path) else path
    if not os.path.exists(full):
        return
    if full not in cfg.VERSIONS:
        cfg.VERSIONS[full] = []
    with open(full, "r") as f:
        content = f.read()
    cfg.VERSIONS[full].append(content)
    if len(cfg.VERSIONS[full]) > 10:
        cfg.VERSIONS[full].pop(0)
