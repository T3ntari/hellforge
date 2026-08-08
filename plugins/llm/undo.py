"""Per-turn undo stack for the copilot — snapshots file states at
begin_turn, restores them LIFO via undo(), plus per-change line stats.

The orchestrator calls begin_turn(project_dir, paths) before applying a
plan and end_turn(project_dir) after (or after each interactive_apply);
each completed turn is one undo unit. Snapshots are in-memory plain
dicts {ts, done, files: {rel: bytes}} with ABSENT marking files that did
not exist at snapshot time. undo(n) restores the last n completed turns,
writing snapshot content back or deleting files that were absent.

diffstat/format_stat reuse plugins/llm/diffview (lazily imported; inline
fallbacks keep this module usable if diffview is unavailable)."""

import difflib
import os
import time

ABSENT = object()  # snapshot value: file did not exist at begin_turn

_stack = []  # [{ts, done, files: {rel: bytes | ABSENT}}]; last entry active while done False


def _root(project_dir):
    return os.path.realpath(os.path.abspath(project_dir))


def _resolve(project_dir, rel_path):
    """Resolve rel_path to an absolute path inside project_dir.

    Raises ValueError for absolute paths or escapes outside the root."""
    if os.path.isabs(rel_path):
        raise ValueError(f"absolute paths not allowed: {rel_path}")
    root = _root(project_dir)
    target = os.path.realpath(os.path.join(root, os.path.normpath(rel_path)))
    if target == root or not target.startswith(root + os.sep):
        raise ValueError(f"path escapes project root: {rel_path}")
    return target


def _finalize(entry, project_dir):
    """Mark entry done, or drop it when nothing changed since snapshot.

    Returns the entry when kept (a change was made), None when dropped."""
    root = _root(project_dir)
    for rel, snap in entry["files"].items():
        current = ABSENT
        try:
            with open(os.path.join(root, *rel.split("/")), "rb") as f:
                current = f.read()
        except OSError:
            pass
        if current != snap:
            entry["done"] = True
            return entry
    if _stack and _stack[-1] is entry:
        _stack.pop()
    return None


def begin_turn(project_dir, paths):
    """Snapshot the current content of each path into a new stack entry.

    Missing files are recorded as ABSENT. Returns the snapshot dict.
    A previously active (un-ended) snapshot is finalized first."""
    if _stack and not _stack[-1]["done"]:
        _finalize(_stack[-1], project_dir)
    root = _root(project_dir)
    files = {}
    for rel in paths:
        abs_path = _resolve(project_dir, rel)
        key = os.path.relpath(abs_path, root).replace(os.sep, "/")
        try:
            with open(abs_path, "rb") as f:
                files[key] = f.read()
        except OSError:
            files[key] = ABSENT
    entry = {"ts": time.time(), "done": False, "files": files}
    _stack.append(entry)
    return entry


def end_turn(project_dir):
    """Mark the active snapshot complete; drop it if nothing changed.

    Returns the finalized entry, or None when there was no active
    snapshot or the turn changed nothing."""
    if not _stack or _stack[-1]["done"]:
        return None
    return _finalize(_stack[-1], project_dir)


def undo(project_dir, n=1):
    """Restore the last n completed turns (LIFO). Returns
    ([(path, "restored"|"deleted")], count). When n exceeds the available
    depth, everything present is undone."""
    if _stack and not _stack[-1]["done"]:
        _finalize(_stack[-1], project_dir)
    n = max(1, int(n))
    count = min(n, len(_stack))
    root = _root(project_dir)
    results = []
    for _ in range(count):
        entry = _stack.pop()
        for rel, snap in entry["files"].items():
            abs_path = os.path.join(root, *rel.split("/"))
            if snap is ABSENT:
                if os.path.exists(abs_path):
                    os.remove(abs_path)
                    results.append((rel, "deleted"))
            else:
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                with open(abs_path, "wb") as f:
                    f.write(snap)
                results.append((rel, "restored"))
    return results, count


def can_undo():
    """True when at least one snapshot (active or completed) exists."""
    return len(_stack) > 0


def depth():
    """Number of snapshots currently on the stack."""
    return len(_stack)


def clear():
    """Drop all snapshots (e.g. after a session save)."""
    _stack.clear()


def diffstat(old_text, new_text):
    """(added, removed) line counts via difflib.

    Reuses plugins.llm.diffview.diff_stat when importable; falls back to
    an identical inline implementation otherwise."""
    try:
        from plugins.llm import diffview as _dv
        return _dv.diff_stat(old_text, new_text)
    except Exception:
        old = (old_text or "").splitlines()
        new = (new_text or "").splitlines()
        sm = difflib.SequenceMatcher(None, old, new)
        adds = dels = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag in ("insert", "replace"):
                adds += j2 - j1
            if tag in ("delete", "replace"):
                dels += i2 - i1
        return adds, dels


def format_stat(path, added, removed):
    """'path +12 -3' — + green, - red (ANSI stripped when off-TTY)."""
    try:
        from plugins.llm import diffview as _dv
        plus = _dv.green(f"+{added}")
        minus = _dv.red(f"-{removed}")
    except Exception:
        plus = f"+{added}"
        minus = f"-{removed}"
    return f"{path} {plus} {minus}"


# ── Persistence: snapshots survive restarts ──

def save_stack(project_dir, path=None):
    """Persist the undo stack to .fent_cache/undo_stack.json (bytes → b64)."""
    import base64
    import json as _json
    from pathlib import Path
    target = path or (Path(project_dir) / ".fent_cache" / "undo_stack.json")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        entries = []
        for snap in _stack:
            files = {}
            for rel, data in snap.get("files", {}).items():
                if data is ABSENT:
                    files[rel] = {"absent": True}
                elif isinstance(data, (bytes, bytearray)):
                    files[rel] = {"b64": base64.b64encode(bytes(data)).decode()}
                else:
                    files[rel] = {"text": str(data)}
            entries.append({"ts": snap.get("ts", 0), "done": snap.get("done", True),
                            "files": files})
        target.write_text(_json.dumps(entries), encoding="utf-8")
        return True
    except Exception:
        return False


def load_stack(project_dir, path=None):
    """Restore the undo stack from disk. Returns the number of snapshots."""
    import base64
    import json as _json
    from pathlib import Path
    target = path or (Path(project_dir) / ".fent_cache" / "undo_stack.json")
    if not target.exists():
        return 0
    try:
        entries = _json.loads(target.read_text(encoding="utf-8"))
        for entry in entries:
            files = {}
            for rel, blob in (entry.get("files") or {}).items():
                if blob.get("absent"):
                    files[rel] = ABSENT
                elif "b64" in blob:
                    files[rel] = base64.b64decode(blob["b64"])
                else:
                    files[rel] = blob.get("text", "")
            _stack.append({"ts": entry.get("ts", 0),
                           "done": entry.get("done", True),
                           "files": files})
        return len(entries)
    except Exception:
        return 0
