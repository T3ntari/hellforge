"""File upload support for the copilot REPL — classify and load a file for
context injection.

The REPL orchestrator parses `/$path` uploads (UPLOAD_RE lives here);
this module provides the pieces it uses:

  classify()          — kind (image|text|code|binary) + mime + size
  load_upload()       — bounded content dict ready for context injection
  format_for_context()— bounded `--- uploaded ... ---` context block

Binary safety: any file carrying a null byte is classified binary no matter
its extension (real text files never contain them), and unknown extensions
default to binary. Images are never slurped as text — the model gets a note
that a vision model can view the file."""

import os
import re

# ── classification ──

IMAGE_EXT = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
}

CODE_EXT = {
    ".py", ".e", ".js", ".ts", ".lua", ".json", ".yaml", ".yml", ".toml",
    ".md", ".sh", ".c", ".h", ".cpp", ".rs", ".go", ".java", ".html", ".css",
}

TEXT_EXT = {".txt", ".log", ".csv"}

TEXT_MIME = "text/plain"
BINARY_MIME = "application/octet-stream"

_NULL_CHUNK = 64 * 1024


def _has_null_byte(path):
    """True when the file contains a NUL byte anywhere (chunked scan)."""
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(_NULL_CHUNK)
            if not chunk:
                return False
            if b"\x00" in chunk:
                return True


def classify(path):
    """Classify a file → {"kind", "mime", "size"}.

    kind is "image" (png/jpg/jpeg/gif/webp/bmp), "code" (source/config
    extensions), "text" (.txt/.log/.csv) or "binary" — unknown extensions
    and any file containing a null byte are binary."""
    ext = os.path.splitext(path)[1].lower()
    size = os.path.getsize(path)
    if ext in IMAGE_EXT:
        return {"kind": "image", "mime": IMAGE_EXT[ext], "size": size}
    if ext in CODE_EXT or ext in TEXT_EXT:
        if _has_null_byte(path):
            return {"kind": "binary", "mime": BINARY_MIME, "size": size}
        return {"kind": "code" if ext in CODE_EXT else "text",
                "mime": TEXT_MIME, "size": size}
    return {"kind": "binary", "mime": BINARY_MIME, "size": size}


# ── loading ──

DEFAULT_CAP = 20000


def load_upload(path, cap=DEFAULT_CAP):
    """Load a file for context injection → dict {path, kind, size, content,
    binary_note}.

    - image  → content "" + note "image attached (vision model can view)"
    - binary → content "" + note "file is binary — not viewable"
    - text/code → full text capped at `cap` chars, truncation noted
    """
    info = classify(path)
    up = {"path": path, "kind": info["kind"], "size": info["size"],
          "content": "", "binary_note": None}
    if info["kind"] == "image":
        up["binary_note"] = f"image attached (vision model can view); path: {path}"
        return up
    if info["kind"] == "binary":
        up["binary_note"] = "file is binary — not viewable"
        return up
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if len(text) > cap:
        up["content"] = text[:cap]
        up["binary_note"] = f"content truncated to {cap} chars"
    else:
        up["content"] = text
    return up


def format_for_context(upload):
    """Bounded context block for the model:
    `--- uploaded <path> (kind, size) ---` + content (+ note when set)."""
    head = f"--- uploaded {upload['path']} ({upload['kind']}, {upload['size']}) ---"
    block = head
    if upload.get("content"):
        block += "\n" + upload["content"]
    note = upload.get("binary_note")
    if note:
        block += "\n" + note
    return block


# ── REPL upload syntax ──

UPLOAD_RE = re.compile(r'^/\$(.+)$')
