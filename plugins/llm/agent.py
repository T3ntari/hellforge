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
  "files": [
    {
      "path": "relative/path/in/project.py",
      "action": "write" | "edit" | "delete",
      "content": "full new file content for write (or omit for edit/delete)",
      "edits": [ {"search": "exact existing text", "replace": "replacement"} ]
    }
  ]
}

Rules:
- paths are ALWAYS relative to the project root, use forward slashes.
- "read" displays a file's content to the user (no changes are made).
- "edit" uses exact search/replace pairs; each search must match exactly once
  in the file as it currently exists; keep pairs small and precise.
- "write" replaces the entire file; include the complete content.
- "delete" removes the file (the user is always asked to confirm).
- When the user only asks a question, answer normally in plain text.
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
    for part in target.relative_to(root).parts:
        if part in FORBIDDEN_DIRS:
            raise ValueError(f"path inside protected dir: {rel_path}")
    return target


def parse_plan(text):
    """Parse the model's JSON plan from its reply. Tolerates markdown fences,
    leading/trailing prose and reasoning text. Returns dict or None."""
    s = (text or "").strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.I)
    s = re.sub(r"\s*```$", "", s)
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
            continue
        if isinstance(plan, dict) and "files" in plan:
            return plan
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
            new_text = f.get("content", "")
            old_text = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
            dv.print_diff(old_text, new_text, rel)
            if auto_accept:
                ok = True
            elif not confirm_write:
                ok = True
            else:
                ok, view, quit_, all_ = _confirm(f"Apply {action.upper()} {rel}? [y/n/v/a/q]")
                if all_:
                    auto_accept = True
                if quit_:
                    skipped.append((rel, "quit"))
                    break
                if view:
                    full = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
                    for line in dv.render_read(new_text.splitlines() if not full else full.splitlines()):
                        print(f"  {line}")
                    ok, _, quit_, _ = _confirm(f"Apply {action.upper()} {rel}? [y/n/a/q]")
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
        old_text = target.read_text(encoding="utf-8", errors="replace")
        new_text = old_text
        edits = f.get("edits") or []
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
