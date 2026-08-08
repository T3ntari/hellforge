"""Project index for the copilot — a deterministic symbol/file index built
locally (no model needed), optionally enriched with model summaries when an
indexing model is configured. Persisted to .fent_cache/llm_index.json.

The index powers: 'ai index', multi-step context, and the model's map of
what lives where. Indexing models can be selected from Ollama; indexing can
be disabled (not recommended)."""

import hashlib
import json
import os
import re
import time
from pathlib import Path

INDEX_PATH = None  # set at build time from project dir

SKIP_DIRS = {".venv", "node_modules", ".git", "__pycache__", ".fent_cache",
             ".e_identity", ".radical_cache", "logs", "embedded_plugins"}
SKIP_EXT = {".pyc", ".pyo", ".mid", ".wav", ".mp3", ".vsix", ".zip", ".sig"}

# Symbol regexes per file type
SYMBOL_RES = {
    ".py": [
        (r"^\s*(?:async\s+)?def\s+([a-zA-Z_]\w*)", "def"),
        (r"^\s*class\s+([a-zA-Z_]\w*)", "class"),
        (r"^\s*register\(api\)", "plugin-entry"),
    ],
    ".e": [
        (r"^\s*!fn\s+(\w+)", "macro"),
        (r"^\s*!(\w+)\s*=", "macro"),
        (r"^\s*(?:for|repeat|while)\b", "loop"),
        (r"^\s*prog\s*\(", "progression"),
        (r"^\s*perc\s*\(", "percussion"),
    ],
    ".lua": [
        (r"^\s*function\s+([a-zA-Z_]\w*)", "function"),
        (r"^\s*local\s+function\s+([a-zA-Z_]\w*)", "function"),
    ],
    ".json": [],
}
DIRECTIVE_RE = re.compile(r"^@(\w+)")


def build_index(project_dir, cache_dir=None):
    """Build a file/symbol index for project_dir. Returns dict."""
    root = Path(project_dir).resolve()
    index = {
        "root": str(root),
        "built": time.time(),
        "file_count": 0,
        "line_count": 0,
        "files": {},
    }
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix.lower() in SKIP_EXT or p.name.startswith("."):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        lines = text.splitlines()
        index["file_count"] += 1
        index["line_count"] += len(lines)
        syms = []
        for pattern, kind in SYMBOL_RES.get(p.suffix.lower(), []):
            for m in re.finditer(pattern, text, re.MULTILINE):
                name = m.group(1) if m.groups() else m.group(0)
                syms.append({"kind": kind, "name": name,
                             "line": text[:m.start()].count("\n") + 1})
        directives = sorted({m.group(1) for m in
                             DIRECTIVE_RE.finditer(text)})[:20]
        entry = {
            "lines": len(lines),
            "size": p.stat().st_size,
            "symbols": syms[:50],
            "directives": directives,
        }
        if p.suffix.lower() == ".py":
            entry["sha"] = hashlib.sha256(text.encode()).hexdigest()[:12]
        index["files"][str(rel)] = entry

    global INDEX_PATH
    path = None
    if cache_dir:
        path = Path(cache_dir) / "llm_index.json"
    else:
        path = root / ".fent_cache" / "llm_index.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(index, indent=1), encoding="utf-8")
    except Exception:
        pass
    return index


def load_index(project_dir):
    """Load the cached index, or None."""
    p = Path(project_dir) / ".fent_cache" / "llm_index.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def index_to_text(index, max_files=40):
    """Compact text rendering of the index for model prompts."""
    if not index:
        return "(no index — run 'ai index')"
    out = [f"Project index: {index.get('file_count', 0)} files, "
           f"{index.get('line_count', 0)} lines"]
    files = index.get("files", {})
    for rel in sorted(files)[:max_files]:
        e = files[rel]
        syms = ", ".join(f"{s['name']}" for s in e.get("symbols", [])[:6])
        line = f"  {rel} ({e.get('lines', 0)} lines)"
        if syms:
            line += f" — {syms}"
        out.append(line)
    if len(files) > max_files:
        out.append(f"  ... {len(files) - max_files} more files")
    return "\n".join(out)
