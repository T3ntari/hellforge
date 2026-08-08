"""Copilot session persistence — save/list/load chat histories under
.fent_cache/sessions/<ts>.json (gitignored runtime state). Enables resume:
each session holds the full message history plus meta (model, provider,
started, turns). Timestamp-based ids, corrupt files are skipped gracefully."""

import json
import time
from pathlib import Path

SESSIONS_DIR_NAME = "sessions"
MAX_SUMMARY_LEN = 120


def sessions_dir(project_dir):
    """The .fent_cache/sessions directory for a project root."""
    return Path(project_dir) / ".fent_cache" / SESSIONS_DIR_NAME


def summarize(history, n=3):
    """The first n user messages (first line each) joined with ' | ' —
    the compact card shown in session listings."""
    parts = []
    for m in history or []:
        if m.get("role") != "user":
            continue
        content = m.get("content") or ""
        if isinstance(content, list):  # Anthropic-style text blocks
            content = " ".join(str(b.get("text", "")) for b in content
                               if isinstance(b, dict))
        first = content.strip().splitlines()[0] if content.strip() else ""
        parts.append(first[:MAX_SUMMARY_LEN])
        if len(parts) >= n:
            break
    return " | ".join(parts)


def save_session(project_dir, history, meta):
    """Persist {history, meta} to .fent_cache/sessions/<ts>.json. meta
    (model/provider/started/turns) is filled from the history when absent.
    Returns the session id."""
    d = sessions_dir(project_dir)
    d.mkdir(parents=True, exist_ok=True)
    history = list(history or [])
    meta = dict(meta or {})
    if not meta.get("model"):
        meta["model"] = ""
    if not meta.get("provider"):
        meta["provider"] = ""
    if not meta.get("started"):
        meta["started"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    if not meta.get("turns"):
        meta["turns"] = sum(1 for m in history if m.get("role") == "user")
    sid = str(int(time.time() * 1000))
    path = d / f"{sid}.json"
    while path.exists():  # same-ms collision → bump until free
        sid = str(int(sid) + 1)
        path = d / f"{sid}.json"
    data = {"id": sid, "ts": time.time(), "meta": meta, "history": history}
    path.write_text(json.dumps(data, indent=1), encoding="utf-8")
    return sid


def list_sessions(project_dir):
    """All sessions, newest first: [{id, ts, model, turns, summary}]."""
    d = _sdir(project_dir)
    out = []
    if not d.is_dir():
        return out
    for path in sorted(d.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            meta = data.get("meta") or {}
        except Exception:
            continue  # corrupt file → skipped gracefully
        out.append({
            "id": data.get("id") or path.stem,
            "ts": data.get("ts") or 0.0,
            "model": meta.get("model") or "",
            "turns": meta.get("turns") or 0,
            "summary": summarize(data.get("history") or [], 1),
        })
    out.sort(key=lambda s: (s["ts"], s["id"]), reverse=True)
    return out


def load_session(project_dir, id_):
    """Load a session by id → {history, meta} (meta gains 'id'), or None
    when missing/corrupt."""
    if not id_:
        return None
    path = _sdir(project_dir) / f"{id_}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        history = data.get("history") or []
        meta = dict(data.get("meta") or {})
    except Exception:
        return None
    meta.setdefault("id", data.get("id") or id_)
    return {"history": history, "meta": meta}


def _sdir(project_dir):
    return sessions_dir(project_dir)