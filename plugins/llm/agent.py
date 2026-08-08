"""Agentic edit engine — the model proposes changes, the user confirms,
edits/writes apply after one batch confirmation, deletes after per-file
confirmation. Path-safety enforced: nothing outside the project root."""

import json
import os
import re
import sys
from pathlib import Path

# Runtime state dirs that edits must never touch
FORBIDDEN_DIRS = {".e_identity", ".fent_cache", ".radical_cache", ".venv",
                  "node_modules", "logs", "__pycache__", ".git"}

SYSTEM_PROMPT = """You are HELLFORGE Copilot, an AI assistant embedded in the HELLFORGE
E Language music DSL compiler (Python). You help with the codebase: fixing
bugs, adding features, writing plugins, explaining code.

When the user asks you to MAKE CHANGES, respond with ONLY a JSON object
(no markdown fences, no commentary outside it) shaped like:

{
  "summary": "one-line description of the change",
  "commands": [ {"cmd": "python tests/syntax_test.py"} ],
  "files": [
    {
      "path": "relative/path/in/project.py",
      "action": "read" | "write" | "edit" | "delete",
      "content": "full new file content for write (or omit for edit/delete)",
      "edits": [ {"search": "exact existing text", "replace": "replacement"} ],
      "start": 1, "end": 50
    }
  ]
}

Rules:
- paths are ALWAYS relative to the project root, use forward slashes.
- "read" displays a file's content to the user (no changes are made);
  use start/end for line ranges.
- "edit" accepts EITHER:
    a) "lines": [startLine, endLine] (1-based, inclusive — the context shows
       files with line numbers like "1525 | def do_help(args):") plus
       "replace": "the exact new lines for that range", OR
    b) "edits": [ {"search": "exact existing text", "replace": "replacement"} ]
  Prefer (a) line ranges whenever the context shows the target lines — it is
  far more reliable. Keep ranges small and precise.
- "write" replaces the entire file; include the complete content. Only use it
  for NEW files; for existing files prefer line-range edits.
- "delete" removes the file (the user is always asked to confirm) — only use
  it when truly required.
- "commands" may run harmless commands like 'python tests/x.py' or
  'git status' — NEVER propose destructive commands (rm, del, mv, sudo,
  shutdown, etc.) or anything touching files outside the project root.
- HARD RULES: never delete files unless essential; NEVER modify, read, or
  reference anything outside the project root (no '..', no absolute paths);
  never access secrets or runtime state.
- When the user only asks a question, answer normally in plain text.
- When finished (or when nothing more is needed), reply
  {"done": true, "summary": "..."} instead of an empty plan.
Never propose edits outside the project. Never fabricate file contents;
if you cannot see a file, use the project structure the user described."""


def _is_tty():
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def safe_path(project_dir, rel_path):
    """Resolve a relative path inside project_dir. Returns Path or raises
    ValueError for escapes/forbidden dirs."""
    p = Path(rel_path)
    if p.is_absolute():
        raise ValueError(f"absolute paths not allowed: {rel_path}")
    root = Path(project_dir).resolve()
    target = (root / p).resolve()
    if not str(target).startswith(str(root)):
        raise ValueError(f"path escapes project root: {rel_path}")
    if target == root:
        raise ValueError(f"cannot target the project root itself: {rel_path}")
    for part in target.relative_to(root).parts:
        if part in FORBIDDEN_DIRS:
            raise ValueError(f"path inside protected dir: {rel_path}")
    return target


def _fix_json_escapes(s):
    """Drop backslashes before characters that are not valid JSON escapes
    (models write Python-regex escapes like \\[ inside JSON strings)."""
    out = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\" and i + 1 < len(s):
            nxt = s[i + 1]
            if nxt in '"\\/bfnrtu':
                out.append(ch)
                out.append(nxt)
            else:
                out.append(nxt)
            i += 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def parse_plan(text):
    """Parse the model's JSON plan from its reply. Tolerates markdown fences,
    leading/trailing prose, reasoning text, Python raw-string prefixes
    (r\"...\") and Python-regex escapes (\\[) in JSON values."""
    s = (text or "").strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.I)
    s = re.sub(r"\s*```$", "", s)
    s = re.sub(r'\br"', '"', s)  # r"..." → "..." (common small-model slip)
    s = re.sub(r"\br'", "'", s)
    s = _fix_json_escapes(s)
    start = s.find("{")
    if start < 0:
        return None
    # Walk closing-brace candidates from the end inward; the first span that
    # parses as JSON wins (robust against trailing prose and nested braces).
    end = len(s) - 1
    while end > start:
        end = s.rfind("}", 0, end + 1)
        if end <= start:
            break
        candidate = s[start:end + 1]
        try:
            plan = json.loads(candidate)
        except Exception:
            end -= 1
            continue
        if isinstance(plan, dict) and ("files" in plan or plan.get("done")):
            return plan
        end -= 1
    return None


def interactive_apply(plan, project_dir, confirm_write=True):
    """Review-and-apply loop used by `ai fix` / `ai plugin`.
    For every proposed change, renders a colored unified diff (or line-
    numbered read) and prompts:
        y = apply this change     n = skip
        v = show the whole file   a = apply all remaining writes/edits
        q = quit applying
    Deletes are ALWAYS confirmed individually (never via 'a', refused off-TTY).
    Returns (applied, skipped, messages)."""
    from . import diffview as dv

    project_dir = Path(project_dir).resolve()
    files = plan.get("files") or []
    applied, skipped, msgs = 0, [], []
    auto_accept = False

    def _confirm(prompt):
        if not _is_tty():
            return False, False, False, False  # (yes, view, quit, all)
        try:
            ans = input(f"  {prompt} ").strip().lower()
        except EOFError:
            return False, False, True, False
        if ans in ("y", "yes"):
            return True, False, False, False
        if ans in ("v", "view"):
            return False, True, False, False
        if ans in ("a", "all"):
            return True, False, False, True
        if ans in ("q", "quit"):
            return False, False, True, False
        return False, False, False, False

    for f in files:
        rel = f.get("path", "")
        action = f.get("action", "edit")
        try:
            target = safe_path(project_dir, rel)
        except ValueError as e:
            skipped.append((rel, str(e)))
            continue

        # ── read: display only ──
        if action == "read":
            if not target.exists():
                skipped.append((rel, "file does not exist"))
                continue
            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            lo = max(1, int(f.get("start", 1)))
            hi = int(f.get("end", len(lines))) if f.get("end") else len(lines)
            print(f"  {dv.yellow(rel)}  {dv.dim(f'Read ({lo}-{min(hi, len(lines))})')} "
                  f"{dv.dim(f'[{len(lines)} lines]')}")
            for line in dv.render_read(lines, lo, hi):
                print(f"  {line}")
            msgs.append(f"  read {rel} (shown, no changes)")
            continue

        # ── delete: always individually confirmed ──
        if action == "delete":
            if not target.exists():
                skipped.append((rel, "file does not exist"))
                continue
            head = target.read_text(encoding="utf-8", errors="replace").splitlines()[:12]
            print(f"  {dv.red(f'DELETE {rel}')}")
            for line in dv.render_read(head):
                print(f"  {dv.red(line)}")
            if not _is_tty():
                skipped.append((rel, "delete declined (not a terminal)"))
                continue
            try:
                ans = input(f"  Delete {rel}? [y/N] ").strip().lower()
            except EOFError:
                ans = "n"
            if ans != "y":
                skipped.append((rel, "delete declined"))
                continue
            if target.is_dir():
                import shutil
                shutil.rmtree(target)
            else:
                target.unlink()
            applied += 1
            msgs.append(f"  deleted {rel}")
            continue

        # ── write / edit: diff preview + confirm ──
        if action == "write":
            if target.is_dir():
                skipped.append((rel, "is a directory — cannot write over it"))
                continue
            new_text = f.get("content", "")
            old_text = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
            # Catastrophic-collapse guard: replacing a large existing file
            # with a tiny one is the classic small-model hallucination.
            collapse = False
            if target.exists() and len(old_text) > 200 and \
                    len(new_text) < len(old_text) * 0.1:
                collapse = True
                print(f"  {dv.red('WARNING')}: this WRITE would shrink {rel} from "
                      f"{len(old_text)} to {len(new_text)} bytes "
                      f"({int(100 * len(new_text) / max(1, len(old_text)))}%).")
                print("  " + dv.red("Likely a hallucinated rewrite — the file must "
                                    "be edited, not replaced."))
            dv.print_diff(old_text, new_text, rel)
            if collapse:
                # Only an explicit 'yes' (full word) can authorize a collapse.
                if auto_accept or not confirm_write:
                    skipped.append((rel, "collapse guard — type 'yes' to replace"))
                    continue
                if not _is_tty():
                    skipped.append((rel, "declined (collapse guard, no TTY)"))
                    continue
                try:
                    ans = input(f"  Type 'yes' to REPLACE {rel} anyway? [yes/n/v] ").strip().lower()
                except EOFError:
                    ans = "n"
                if ans == "v":
                    for line in dv.render_read(new_text.splitlines()):
                        print(f"  {line}")
                    try:
                        ans = input(f"  Type 'yes' to REPLACE {rel} anyway? [yes/n] ").strip().lower()
                    except EOFError:
                        ans = "n"
                if ans != "yes":
                    skipped.append((rel, "declined (collapse guard)"))
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(new_text, encoding="utf-8")
                applied += 1
                msgs.append(f"  wrote {rel}")
                continue
            if auto_accept:
                ok = True
            elif not confirm_write:
                ok = True
            else:
                ok, view, quit_, all_ = _confirm(f"Apply WRITE {rel}? [y/n/v/a/q]")
                if all_:
                    auto_accept = True
                if quit_:
                    skipped.append((rel, "quit"))
                    break
                if view:
                    full = old_text if old_text else ""
                    for line in dv.render_read(new_text.splitlines() if not full else full.splitlines()):
                        print(f"  {line}")
                    ok, _, quit_, _ = _confirm(f"Apply WRITE {rel}? [y/n/a/q]")
                    if quit_:
                        skipped.append((rel, "quit"))
                        break
            if not ok:
                skipped.append((rel, "declined"))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(new_text, encoding="utf-8")
            applied += 1
            msgs.append(f"  wrote {rel}")
            continue

        # edit
        if not target.exists():
            skipped.append((rel, "file does not exist"))
            continue
        if target.is_dir():
            skipped.append((rel, "is a directory — cannot edit it"))
            continue
        old_text = target.read_text(encoding="utf-8", errors="replace")
        old_lines = old_text.splitlines()
        new_text = old_text
        edits = f.get("edits") or []
        line_edit = f.get("lines")
        if line_edit is not None:
            # Line-range edit: [lo, hi] 1-based inclusive, replace with text.
            try:
                lo, hi = int(line_edit[0]), int(line_edit[1])
            except (TypeError, ValueError, IndexError):
                skipped.append((rel, "bad lines range"))
                continue
            if lo < 1 or hi < lo or hi > len(old_lines):
                skipped.append((rel, f"lines {lo}-{hi} out of range "
                                     f"(file has {len(old_lines)} lines)"))
                continue
            new_lines = old_lines[:lo - 1] + f.get("replace", "").splitlines() \
                        + old_lines[hi:]
            new_text = "\n".join(new_lines)
            if old_text.endswith("\n"):
                new_text += "\n"
        else:
            if not edits:
                skipped.append((rel, "no edits provided"))
                continue
            failed = False
            for pair in edits:
                search, replace = pair.get("search", ""), pair.get("replace", "")
                if not search:
                    skipped.append((rel, "empty search block"))
                    failed = True
                    break
                if new_text.count(search) != 1:
                    skipped.append((rel, f"search block not unique/missing "
                                         f"({new_text.count(search)} matches)"))
                    failed = True
                    break
                new_text = new_text.replace(search, replace)
            if failed:
                continue
        dv.print_diff(old_text, new_text, rel)
        if auto_accept:
            ok = True
        elif not confirm_write:
            ok = True
        else:
            ok, view, quit_, all_ = _confirm(f"Apply EDIT {rel}? [y/n/v/a/q]")
            if all_:
                auto_accept = True
            if quit_:
                skipped.append((rel, "quit"))
                break
            if view:
                for line in dv.render_read(new_text.splitlines()):
                    print(f"  {line}")
                ok, _, quit_, _ = _confirm(f"Apply EDIT {rel}? [y/n/a/q]")
                if quit_:
                    skipped.append((rel, "quit"))
                    break
        if not ok:
            skipped.append((rel, "declined"))
            continue
        target.write_text(new_text, encoding="utf-8")
        applied += 1
        adds, dels = dv.diff_stat(old_text, new_text)
        msgs.append(f"  edited {rel} {dv.green(f'+{adds}')} {dv.red(f'-{dels}')}")

    return applied, skipped, msgs


def apply_plan(plan, project_dir, confirm_write=True):
    """Apply a validated plan. Returns (applied_count, skipped, messages).
    Edits/writes batch-confirm once when confirm_write=True (TTY required);
    confirm_write=False auto-applies writes/edits (scripted / tests) but
    deletes ALWAYS require per-file confirmation and are refused off-TTY."""
    project_dir = Path(project_dir).resolve()
    files = plan.get("files") or []
    applied, skipped = 0, []
    msgs = []

    # Normalize actions
    writes = [f for f in files if f.get("action") in ("write", "edit")]
    deletes = [f for f in files if f.get("action") == "delete"]

    def _confirm(prompt):
        if not _is_tty():
            return False
        try:
            return input(f"  {prompt} [y/N] ").strip().lower() == "y"
        except EOFError:
            return False

    for f in writes:
        rel = f.get("path", "")
        try:
            target = safe_path(project_dir, rel)
        except ValueError as e:
            skipped.append((rel, str(e)))
            continue
        action = f.get("action", "edit")
        if action == "write":
            content = f.get("content", "")
            if not content and target.exists():
                skipped.append((rel, "empty write content"))
                continue
            if confirm_write and not _confirm(f"Apply WRITE {rel} "
                                              f"({len(content)} bytes)?"):
                skipped.append((rel, "declined"))
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            applied += 1
            msgs.append(f"  wrote {rel} ({len(content)} bytes)")
        else:  # edit
            if not target.exists():
                skipped.append((rel, "file does not exist"))
                continue
            content = target.read_text(encoding="utf-8", errors="replace")
            edits = f.get("edits") or []
            if not edits:
                skipped.append((rel, "no edits provided"))
                continue
            if confirm_write and not _confirm(f"Apply {len(edits)} EDIT(s) to {rel}?"):
                skipped.append((rel, "declined"))
                continue
            new_content = content
            failed = False
            for pair in edits:
                search, replace = pair.get("search", ""), pair.get("replace", "")
                if not search:
                    skipped.append((rel, "empty search block"))
                    failed = True
                    break
                if new_content.count(search) != 1:
                    skipped.append((rel, f"search block not unique/missing "
                                         f"({new_content.count(search)} matches)"))
                    failed = True
                    break
                new_content = new_content.replace(search, replace)
            if failed:
                continue
            target.write_text(new_content, encoding="utf-8")
            applied += 1
            msgs.append(f"  edited {rel} ({len(edits)} block(s))")

    for f in deletes:
        rel = f.get("path", "")
        try:
            target = safe_path(project_dir, rel)
        except ValueError as e:
            skipped.append((rel, str(e)))
            continue
        if not target.exists():
            skipped.append((rel, "file does not exist"))
            continue
        # Deletes are ALWAYS individually confirmed, even when writes were
        # batch-confirmed. Never auto-confirmed.
        if not _confirm(f"DELETE {rel}?"):
            skipped.append((rel, "delete declined"))
            continue
        if target.is_dir():
            import shutil
            shutil.rmtree(target)
        else:
            target.unlink()
        applied += 1
        msgs.append(f"  deleted {rel}")

    return applied, skipped, msgs


def execute_plan_commands(plan, project_dir):
    """Execute every command in the plan's "commands" list (validated by
    exec.py's guard). Returns (results, chat_lines)."""
    from . import exec as safe_exec
    results = []
    for c in plan.get("commands") or []:
        cmd = c.get("cmd") if isinstance(c, dict) else str(c)
        res = safe_exec.run_command(cmd, project_dir)
        res["cmd"] = cmd
        results.append(res)
    chat_lines = [safe_exec.chat_line(r) for r in results]
    return results, chat_lines


def plan_is_done(plan):
    """True when the model says it is finished (no files, no commands)."""
    if not plan:
        return True
    if plan.get("done"):
        return True
    files = plan.get("files") or []
    commands = plan.get("commands") or []
    return not files and not commands
