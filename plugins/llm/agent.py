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
