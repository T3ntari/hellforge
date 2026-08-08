# RULES.md — Hard Rules for AI Agents in HELLFORGE / E

Short, imperative rules. AGENTS.md is the full reference — when they
conflict, these win. Violating any of these is a bug in your work.

## Editing files

1. **Never rewrite an existing file whole-file.** Changes to existing files
   are precise line-range edits (`"lines": [a, b]` + `"replace"`) or
   insertions (`"lines": [x]` alone). A whole-file write is refused unless
   the user explicitly types `yes`.
2. **Never delete a file without confirmation.** Deletes always require an
   explicit per-file yes from the user; the `a` (all) answer never
   auto-confirms deletes.
3. **Never touch anything outside the project root** — no `..`, no absolute
   paths — and never read or write protected dirs (`.e_identity/`, `.venv/`,
   `logs/`, `.fent_cache/`, `__pycache__/`, `.git/`, `node_modules/`).

## Commands

4. **Only run safe commands**: `python tests/<file>_test.py`, `git status`,
   `git diff`, `git log`, and other read-only/harmless checks. Destructive or
   meta commands are blocked: `rm`, `mv`, `sudo`, `pip install`, shell
   pipes, redirects, anything touching files outside the project.

## Tests

5. **Always run the relevant tests after any `.py` change** (and a syntax
   check via py_compile — it runs automatically). Run the full suite before
   declaring work done.
6. **Never commit unless the suite is green.** A change that breaks a test
   is a bug in your change, not in the test.

## TODO.md

7. **Update TODO.md as you work** — add your task as `- [ ]` items (via the
   plan key `"todo": [{"item": "...", "status": "open"|"done"}]` or direct
   edit), check them off as you complete them. Never delete items.

## Honesty and scope

8. **Never fabricate file contents** or claim things exist that don't —
   read the actual files; if you can't see it, say so.
9. **Prefer the smallest change** that satisfies the task; keep backward
   compatibility (v1–v4 sources must still compile).
10. **Never invent syntax.** New syntax only in the v5 path, and only if it
    is in SYNTAX.md (or you document it there first).
