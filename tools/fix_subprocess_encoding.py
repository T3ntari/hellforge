#!/usr/bin/env python3
"""Fix subprocess UnicodeDecodeError: add utf-8+errors=replace to all
capture_output=True, text=True calls across the codebase."""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"__pycache__", "node_modules", ".git", ".vscode", "out", "resources"}
SKIP_PATHS = {"fix_subprocess_encoding.py", "update_all.py"}

PATTERN = re.compile(r"capture_output=True,\s*text=True")
REPLACEMENT = 'capture_output=True, text=True, encoding="utf-8", errors="replace"'

fixed = 0
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if not fn.endswith(".py") or fn in SKIP_PATHS:
            continue
        full = os.path.join(dirpath, fn)
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            src = f.read()
        new_src, n = PATTERN.subn(REPLACEMENT, src)
        if n:
            with open(full, "w", encoding="utf-8") as f:
                f.write(new_src)
            print(f"  FIXED {os.path.relpath(full, ROOT)} ({n})")
            fixed += 1
print(f"\n{fixed} files updated.")
