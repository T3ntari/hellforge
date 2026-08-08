#!/usr/bin/env python3
"""HELLFORGE import hygiene tool — split all single-line imports (PEP 8).
Converts:
    import a
    import b
    import c            →  import a / import b / import c
    import a.b
    import c.d as e      →  import a.b / import c.d as e
    from x import (
        a,
        b        →  from x import (\n    a,
        \n    b,
        \n),
    )
Skips __pycache__, node_modules, and already-multi-line imports."""

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"__pycache__", "node_modules", ".git", ".vscode", "out"}
SKIP_EXT = {".vsix"}

IMPORT_RE = re.compile(r"^(\s*)import\s+(.+?)(\s*#.*)?$")
FROM_RE = re.compile(r"^(\s*)from\s+([\w.]+)\s+import\s+(.+?)(\s*#.*)?$")


def walk_py_files():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            full = os.path.join(dirpath, fn)
            if any(full.endswith(ext) for ext in SKIP_EXT):
                continue
            yield full


def split_plain_import(names):
    """Split 'a, b as c, d.e' into ['a', 'b as c', 'd.e']."""
    parts = [p.strip() for p in names.split(",")]
    return [p for p in parts if p]


def split_from_import(names):
    """Split 'a, b as c, d' (from-import) into list."""
    parts = [p.strip() for p in names.split(",")]
    return [p for p in parts if p]


def fix_file(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()

    changed = False
    out = []
    for raw in lines:
        line = raw.rstrip("\n")
        indent_match = re.match(r"^(\s*)(import|from)\b", line)
        if not indent_match:
            out.append(raw)
            continue
        indent = indent_match.group(1)

        m = IMPORT_RE.match(line)
        if m and "," in m.group(2):
            parts = split_plain_import(m.group(2))
            if len(parts) > 1:
                comment = (m.group(3) or "").rstrip()
                for i, part in enumerate(parts):
                    suffix = f"  {comment.strip()}" if (comment and i == 0) else ""
                    out.append(f"{indent}import {part}{suffix}\n")
                changed = True
                continue

        m = FROM_RE.match(line)
        if m and "," in m.group(3):
            parts = split_from_import(m.group(3))
            if len(parts) > 1:
                comment = (m.group(4) or "").rstrip()
                out.append(f"{indent}from {m.group(2)} import (\n")
                for i, part in enumerate(parts):
                    suffix = f"  {comment.strip()}" if (comment and i == 0) else ""
                    out.append(f"{indent}    {part},{suffix}\n")
                out.append(f"{indent})\n")
                changed = True
                continue

        out.append(raw)

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(out)
        return True
    return False


def main():
    fixed = 0
    for path in walk_py_files():
        rel = os.path.relpath(path, ROOT)
        if fix_file(path):
            print(f"  FIXED {rel}")
            fixed += 1
    print(f"\n{fixed} files updated.")


if __name__ == "__main__":
    main()
