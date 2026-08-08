"""HELLFORGE smart path resolution — shared by eshell commands and plugins.

resolve_inputs() turns user-supplied specs into a flat list of real files:

  - Relative path        samples/v4-current/hello.e
  - Absolute path        D:/abc.e  (drive-letter detected on Windows)
  - Directory            samples/v4-current   → every supported file inside
  - "/" wildcard         /          → all supported files in cwd
  - Glob                 samples/**/*.e
  - Multiple specs       a.e b.e samples/     → all matched, deduplicated

Supported extensions are the E-language family plus MIDI/audio import formats."""

import glob as _glob
import os
import re

SUPPORTED_EXTS = {
    ".e", ".ei", ".eic", ".enx", ".eci", ".ec", ".machine", ".human",
    ".mid", ".midi", ".wav", ".mp3", ".mp4", ".m4a", ".mov", ".avi",
    ".flac", ".ogg", ".aac", ".wma", ".aiff", ".ee", ".ecc",
}

# Absolute-path detection: Windows drive (C:/, D:\) or POSIX root (/...)
_DRIVE_RE = re.compile(r"^[A-Za-z]:[\\/]")


def is_absolute(path):
    """True for OS-absolute paths, including Windows drive-letter paths."""
    if os.path.isabs(path):
        return True
    return bool(_DRIVE_RE.match(path))


def _expand_user(path):
    if path == "~" or path.startswith("~/"):
        home = os.path.expanduser("~")
        return os.path.join(home, path[2:]) if path != "~" else home
    return path


def resolve_inputs(specs, cwd=None, recursive=False):
    """Resolve one or more input specs to a flat, deduplicated list of files.
    specs: str or list of str (each may be file / dir / '/' / glob)
    cwd:   working directory for relative resolution (defaults to os.getcwd)
    recursive: include subdirectories when a directory or '/' is given
    Returns list of absolute paths that exist and have a supported extension."""
    if isinstance(specs, str):
        specs = [specs]
    cwd = os.path.abspath(cwd or os.getcwd())
    found = []

    def walk_dir(d, rec):
        for root, dirs, files in os.walk(d):
            if not rec:
                dirs[:] = []
            for fn in sorted(files):
                ext = os.path.splitext(fn)[1].lower()
                if ext in SUPPORTED_EXTS:
                    found.append(os.path.join(root, fn))

    for spec in specs:
        s = spec.strip().strip("\"'")
        if not s:
            continue

        # "/" wildcard → everything supported under cwd
        if s == "/":
            walk_dir(cwd, recursive)
            continue

        s = _expand_user(s)
        path = s if is_absolute(s) else os.path.join(cwd, s)

        # Glob if it contains wildcard characters
        if any(ch in s for ch in "*?["):
            matches = _glob.glob(path, recursive=True)
            for m in sorted(matches):
                if os.path.isdir(m):
                    walk_dir(m, recursive)
                elif os.path.isfile(m):
                    found.append(m)
            continue

        if os.path.isdir(path):
            walk_dir(path, recursive)
        elif os.path.isfile(path):
            found.append(path)

    # Deduplicate, keep order
    seen = set()
    result = []
    for p in found:
        ap = os.path.abspath(p)
        if ap not in seen:
            seen.add(ap)
            result.append(ap)
    return result


def batch_suffix(path, tag):
    """'song.e' + 'v3' -> 'song_v3.e'. Preserves directory, replaces extension."""
    d = os.path.dirname(path)
    base = os.path.splitext(os.path.basename(path))[0]
    ext = os.path.splitext(path)[1]
    return os.path.join(d, f"{base}_{tag}{ext}")
