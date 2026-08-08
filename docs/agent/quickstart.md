# Quickstart — HELLFORGE / E for Models (2-minute briefing)

**HELLFORGE (E)** is a DSL for piano music composition: plain text → `.mid`,
`.wav`, `.mp3`, `.mp4`, `.ec`, `.eic`. Python 3.10+.
Read this first, then `language.md` (syntax), `compiler.md` (pipeline),
`copilot.md` (agent loop). Human docs: `SYNTAX.md`, `AGENTS.md`, `RULES.md`.
## Five things to know immediately

1. **v5 is canonical.** Everything compiles as v5 by default; v1–v4 still
   compile with warnings. New syntax goes ONLY in the v5 path
   (`ep_compiler/`), and only if it is in SYNTAX.md.
2. **The event dict is the whole world.** Every parser emits
   `{"timestamp", "midi", "duration", "velocity", "pan", "bend"}` dicts
   (`ep_compiler/events.py`). Compile → events → export. Nothing else.
3. **Two writing modes, no headers needed.** Machine: `T0 N60 D500 V80`
   (absolute ms). Human: `play note(C4) @dur:q @vel:mf` (relative cursor).
   v5 auto-detects and mixes both.
4. **Always venv**: `.venv/bin/python ...`, never bare `python`. Tests:
   `.venv/bin/python tests/<file>_test.py`.
5. **Hard rules:** no whole-file rewrites (line-range edits only), no
   deletions without per-file confirmation, no paths outside the project
   root, no destructive shell commands, suite green before finish.
## Where things live

- `ep_compiler/` — compiler core (parser, modes, directives, math, loops, formats)
- `ep_core.py` — plugin registry, GC, signing, encryption, identity
- `plugins/` — drop-in plugins (`llm/` = copilot, `humanize/` = feel, ...)
- `tests/` — `*_test.py` harness suites (no pytest); `samples/v5-current/` — canonical examples

## Entry points

```bash
.venv/bin/python ep.py compile song.e -o song.mid   # CLI compile
.venv/bin/python run.py compile song.e              # launcher compile
.venv/bin/python run.py check <spec>                # lint/check
.venv/bin/python eshell.py                          # interactive shell
.venv/bin/python player.py song.e                   # playback
.venv/bin/python ai.py fix "<issue>"                # AI copilot
```

eshell commands map to `ep_compiler/cli_cmds.py`; `cli.py` is the direct
CLI; `run.py` wraps everything; `ai.py` → `plugins/llm/`.

## The 5 most important rules (RULES.md)

1. Never rewrite an existing file whole-file — line-range edits
   (`"lines": [a, b]` + `"replace"`) or insertions (`"lines": [x]`).
2. Never delete a file without explicit per-file confirmation; `a` (all)
   never auto-confirms deletes.
3. Never touch anything outside the project root; no reads/writes in
   protected dirs (`.identity/`, `.venv/`, `.fent_cache/`, `logs/`, `.git/`).
4. Only safe commands: `python tests/x.py`, `git status/diff/log` — no
   `rm`, `mv`, `sudo`, `pip install`, pipes, redirects.
5. After any `.py` change run relevant tests; full suite green before done.
   Never commit red. Update `TODO.md` as you work.