"""Code index for the copilot — keyword index over project files, optional
Ollama embedding model for semantic search. Persisted in .fent_cache/
(gitignored). Disable-able via 'ai index off' (not recommended)."""

import hashlib
import json
import os
import re
import time
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".identity",
             ".fent_cache", ".radical_cache", "logs", ".traycer"}
INDEXABLE = {".py", ".e", ".ei", ".enx", ".eci", ".eic", ".md", ".json",
             ".lua", ".js", ".ts", ".html"}

_WORD_RE = re.compile(r"[a-zA-Z_]\w*")


def _tokenize(text):
    return [w.lower() for w in _WORD_RE.findall(text) if len(w) > 1]


def build_index(project_dir):
    """Walk the project and build {path: {size, lines, first_line, terms}}."""
    root = Path(project_dir).resolve()
    entries = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith((".pyc", ".sig")):
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext not in INDEXABLE:
                continue
            full = os.path.join(dirpath, fn)
            try:
                rel = str(Path(full).relative_to(root)).replace(os.sep, "/")
            except ValueError:
                continue
            try:
                with open(full, "r", encoding="utf-8", errors="replace") as f:
                    head = f.read(8192)
            except Exception:
                continue
            lines = head.count("\n") + 1
            first_line = head.splitlines()[0][:120] if head.splitlines() else ""
            entries[rel] = {
                "size": os.path.getsize(full),
                "lines": lines,
                "first_line": first_line,
                "terms": _tokenize(rel) * 3 + _tokenize(first_line) * 2,
            }
    return entries


def index_path(project_dir):
    return Path(project_dir) / ".fent_cache" / "llm_index.json"


def save_index(project_dir, entries, embedding_model=None):
    path = index_path(project_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "built": time.time(),
        "count": len(entries),
        "embedding_model": embedding_model,
        "entries": {k: {kk: vv for kk, vv in v.items() if kk != "terms"}
                    for k, v in entries.items()},
        # terms stored separately to keep the JSON small-ish
        "terms": {k: v["terms"] for k, v in entries.items()},
    }
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp, path)
    return path


def load_index(project_dir):
    path = index_path(project_dir)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def search(index, query, limit=6):
    """Keyword search: rank files by term overlap with the query.
    Path tokens weight 3, first-line tokens weight 2, content terms 1."""
    if not index:
        return []
    q = _tokenize(query)
    if not q:
        return []
    scored = []
    for rel, ent in index.get("entries", {}).items():
        terms = index.get("terms", {}).get(rel, [])
        score = sum(terms.count(t) for t in q)
        if score > 0:
            # Boost small files and files whose path contains query tokens
            path_boost = sum(3 for t in q if t in rel.lower())
            scored.append((score + path_boost, ent["size"], rel))
    scored.sort(key=lambda x: (-x[0], x[1]))
    return [rel for _, _, rel in scored[:limit]]


def refresh(project_dir, embedding_model=None):
    entries = build_index(project_dir)
    save_index(project_dir, entries, embedding_model)
    return len(entries)


# ── optional Ollama embedding model ─────────────

def embed_document(text, model, base="http://127.0.0.1:11434"):
    """Embed text via Ollama's native /api/embed endpoint. Returns a vector
    (list of floats) or None on failure (model missing / server down)."""
    import urllib.request
    payload = json.dumps({"model": model, "input": text[:6000]}).encode("utf-8")
    req = urllib.request.Request(base + "/api/embed", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        emb = data.get("embeddings") or data.get("embedding")
        if emb:
            return emb[0] if isinstance(emb, list) and emb and isinstance(emb[0], list) else emb
    except Exception:
        pass
    return None


def cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def semantic_search(index, query, model, project_dir, base="http://127.0.0.1:11434",
                    limit=6, cache=None):
    """Embed the query and rank files by cosine similarity. Uses a tiny
    per-process cache of file vectors (embedded lazily)."""
    qv = embed_document(query, model, base)
    if not qv:
        return None  # embedding unavailable — caller falls back to keyword
    cache = cache if cache is not None else {}
    scored = []
    entries = index.get("entries", {}) if index else {}
    root = Path(project_dir).resolve()
    for rel in entries:
        ev = cache.get(rel)
        if ev is None:
            try:
                with open(root / rel, "r", encoding="utf-8", errors="replace") as f:
                    text = f.read(6000)
            except Exception:
                continue
            ev = embed_document(text, model, base)
            if not ev:
                continue
            cache[rel] = ev
        scored.append((cosine(qv, ev), rel))
    scored.sort(key=lambda x: -x[0])
    return [rel for _, rel in scored[:limit]]
