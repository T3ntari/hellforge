# AGENTS.md — AI Agent Instructions for HELLFORGE / E

This file is the **authoritative instruction set for any AI agent working in
this repository** (opencode, Claude Code, the built-in `ai` copilot, or any
other tool). Read it fully before doing anything. RULES.md is the condensed
hard-rules version of this document — when they conflict, RULES.md wins.

## What this project is

**HELLFORGE (E)** is a domain-specific language for **piano music
composition**. You write music as plain text — notes, chords, rhythms,
dynamics — and E compiles it to `.mid`, `.wav`, `.mp3`, `.mp4`, `.ec`
(compiled binary) and more. No piano or programming experience is needed to
compose with it.

- **Canonical syntax: v5** (the default for all sources). v1–v4 still compile
  for backward compatibility but are deprecated and emit warnings. Never add
  new syntax to the legacy paths; everything goes into the v5 path
  (`ep_compiler/`).
- **Runtime:** Python 3.10+ (dev/tested on 3.11). The project venv is
  symlinked at `.venv/` — always run Python through it
  (`.venv/bin/python ...`), never a bare `python`.
- **License:** MIT, open source. **Signing** (ED25519 file signatures) is an
  optional opt-in feature (`sys strict 2` enables enforcement); it must never
  be made mandatory.

## Project layout

```
ep_compiler/     The compiler core — parser, modes, directives, lint,
                 events, math, loops, scale quantizer, formats
plugins/         Plugin ecosystem (each plugin = its own package):
                   llm/       the AI copilot plugin (agent, todo, indexer)
                   humanize/  performance feel
                   eaudio/    spatial audio
                   radical/   GPU math
                   ...        and more
tests/           Test suite — tests/*_test.py, self-contained harnesses
samples/         Example .e sources, organized by syntax version
                 (v5-current/ is canonical; v1–v4 deprecated)
doc/             Wiki-style docs (syntax, audio, backend, plugins, signing)
SYNTAX.md        Full language reference — READ IT before touching syntax
README.md        Public overview
ai.py            AI copilot CLI entry point (same engine as plugins/llm/)
eshell.py, run.py, ep.py, player.py   Entry points (CLI / shell)
```

Key entry points: `ep.py compile|play`, `run.py compile|check`,
`eshell.py` (interactive shell), `ai.py` (copilot).

## Model documentation (docs/agent/)

Concise, model-consumable docs — read these before touching anything;
they are the distilled, code-verified versions of SYNTAX.md and the codebase.

- `docs/agent/quickstart.md` — **read first**: 2-minute briefing (what E is,
  v5 canonical, entry points, layout, the 5 hard rules).
- `docs/agent/language.md` — **consult before touching syntax**: complete v5
  reference (machine/human modes, directives, statements, loops, math,
  piano-performance layer, version detection, event dict).
- `docs/agent/compiler.md` — compiler pipeline (`compile_source` flow),
  event dict contract, directives → ll_state, export formats, mode modules.
- `docs/agent/plugins.md` — plugin API: `register(api)`, `api.on` hooks,
  add_command/register_directive/register_math_evaluator, eshell integration,
  mods security model.
- `docs/agent/testing.md` — test conventions: harness, how to run, what must
  be green before commit.
- `docs/agent/copilot.md` — the AI copilot tool protocol: JSON plan keys,
  actions, modes, safety rules, thinking, search, TODO.md.
- `docs/agent/architecture.md` — file map + end-to-end data flow
  (source → events → MIDI → WAV), eshell command routing.

Rule: **read `quickstart.md` first; consult `language.md` before touching
syntax.** These files must stay accurate — update them whenever the behavior
they describe changes.

## The v5 language — essentials

### Directives

`@`-prefixed, e.g. `@bpm 120`, `@key C major`, `@vol:0.7`, `@seed 42`,
`@sr`, `@bit`, `@quality`, `@pedal:<0-127>`, `@master`, `@gain`, `@sub`,
`@bass_boost`, `@stereo_width`, `@neural`. Mode headers: `#MACHINE`,
`#HUMAN`, `#V3`/`#SHORTHAND`, `#V4`. Comments are `//` (and `#` outside
headers).

### Statements (v5 statement set)

- `print <expr>` — print a value
- `assert <cond>, "message"` — runtime check
- `include "file.e"` — source-level include (macros/loops/directives participate)
- `!fn name(args) = ...` — macro definitions, invoked as `!name(args)`
- `prog(C:q G:q Am:h F:q)` — chord progression shorthand
- `perc(kick)`, `perc(hihat)` — percussion
- Loops: `for $n in scale(C major, 4, 1) { ... }`, `for $i in 1..4 { ... }`,
  list/run loops — all with `break` / `continue`
- `@seed 42` + `pick(...)` / `rand(...)` — deterministic randomness

### Piano performance features (v5 = v4 + these)

- **pedal** — `pedal on` / `pedal off`, `@pedal:<0-127>` (sustain)
- **rest** — silence with explicit duration
- **art** — articulations: `@art:staccato`, `@art:legato`, ...
- **tuplets** — `[C4 D4 E4 F4]/5` (five notes over one beat)
- **octave** — octave shifts/transposition
- **curve** — velocity/expression curves over time
- **ties** — note ties across beats

### Two writing modes

Machine mode — absolute timestamps: `T0 N60 D500 V80` (`T<ms> N<midi>
D<ms> V<0-127>`). Human mode — readable: `play note(C4) @dur:q @vel:mf`,
`play chord(C, major) @dur:h @vel:ff`, `pedal on`.

See SYNTAX.md for the complete reference. **Never invent syntax that is not
in SYNTAX.md.**

## Test conventions

- Every test file is `tests/*_test.py` and uses the shared harness:
  ```python
  def test(name, fn):
      global passed, failed
      try:
          fn(); passed += 1
      except Exception as e:
          failed += 1
  ```
  defined per-file, with a summary print at the end and `sys.exit(1)` on
  failures. There is no pytest.
- Run a suite with the project venv: `.venv/bin/python tests/<file>_test.py`
  (or `tests/run_all.py` for the combined run).
- **Always run the relevant test files after any `.py` change**, and the full
  suite before declaring work done. **NEVER commit unless the suite is
  green.** Every existing feature has tests — a change that breaks a test is
  a bug in your change, not in the test.
- New features need ≥2 tests using the existing `test(name, fn)` harness.

## Code conventions

- Python 3.10+ compatible; **f-strings preferred**; `#` comments only where
  they add real context (don't decorate code with obvious comments).
- **No stubs.** Every advertised feature must work end-to-end
  (source → compile → events → MIDI → render). If it's not implemented, it's
  not advertised.
- **Backward compatibility.** v1–v4 sources still compile (with deprecation
  warnings); the v5 path is where all new syntax goes.
- **No phone-home, no private dependencies.** The project is fully
  offline-capable. Any network feature must be gated behind an explicit
  opt-in flag. No personal trust keys, no private servers.
- **No personal identity.** Don't hardcode user paths (`C:\Users\...`), no
  Windows-only behavior without a cross-platform fallback.
- Match the surrounding style of the file you touch (module docstring,
  `test(name, fn)` sections, section banners like `# ── name ──`).

## How the copilot works (the built-in `ai` agent)

The repo embeds an LLM copilot (`ai.py`, engine in `plugins/llm/`). Commands:
`ai fix "<issue>"` (multi-step agentic loop: plan → review → apply →
verify → repeat), `ai agent` (interactive multi-turn REPL session), `ai chat`
(chat only, no edits), `ai read <file> [start [end]]`, `ai plugin "<desc>"`.

The agent communicates through a JSON plan format:
`{"summary", "commands": [...], "files": [...]}` or `{"done": true}`. The
copilot maintains the project checklist in **TODO.md** through the plan key
`"todo": [{"item": "...", "status": "open"|"done"}]` (see plugins/llm/todo.py).

Copilot policies you must honor when acting as (or through) this agent:

- **Edit-not-rewrite policy.** Existing files are NEVER rewritten whole-file;
  changes are applied as precise **line-range edits** (`"lines": [a, b]` +
  `"replace"`) or insertions (`"lines": [x]` alone). Whole-file writes are
  refused unless the user explicitly types `yes`.
- **Deletes need confirmation.** File deletions always require an explicit
  per-file confirmation from the user; the `a` (all) answer never
  auto-confirms deletes.
- **Safe command allowlist.** Only harmless commands are permitted
  (`python tests/x.py`, `git status`, ...). Destructive/meta commands
  (`rm`, `mv`, `sudo`, `pip install`, shell pipes, redirects) are blocked.
- Paths are always relative to the project root; nothing outside the root,
  no protected dirs (`.e_identity/`, `.venv/`, `logs/`, ...).
- After any `.py` change, a syntax check (py_compile) runs automatically;
  you should still run the relevant tests.

## Git workflow

- **`main` is the release branch.** Release-quality, green tests only.
- **All work happens in branches.** Create/use a feature branch per unit of
  work; never commit directly to main.
- Keep commits small and focused; match the repo's commit style
  (concise one-line summaries).
- **Never push without green tests.** Never force-push.
- Do not commit secrets, `.env`, runtime state, or build artifacts
  (see .gitignore).

## Workflow for a task

1. Read AGENTS.md, RULES.md, and **TODO.md** (the live agent-managed
   checklist). Add your task to TODO.md as `- [ ]` items and check them off
   as you complete them (via the `todo` plan key or direct edit).
2. Find the relevant code + tests; reproduce/verify the current behavior.
3. Make the **smallest change** that satisfies the task; keep
   backward compatibility; run the relevant tests.
4. Update tests for any behavior you changed; run the full suite; ensure
   green before finishing.
5. Update docs (README.md / SYNTAX.md / doc/) if user-visible behavior
   changed. Never fabricate file contents or claim things that don't exist —
   read the actual files.

## The HELL'S CODE TUI (plugins/llm/tui.py)

The copilot can run as a full-screen curses TUI (`ai agent` auto-detects a
real terminal; `--tui`/`--no-tui` force the choice). Architecture:

- **Screen buffer + frame loop**: the TUI owns the terminal grid; the agent
  logic runs on a background thread and communicates through a `Bridge`
  event queue (`stream`, `feed`, `box_open/line/close`, `ask`, `status`).
- **Raw keys**: typing, arrows, Tab completion, Ctrl+C/V/X clipboard, PgUp/
  PgDn scrollback, KEY_RESIZE reflow.
- **Sub-windows**: command output streams into a bordered box, never the
  main feed. **Gatekeeper**: approvals render as a modal box; the agent
  thread blocks on `bridge.ask()` until Y/N/E is pressed.
- **Fallback**: `tui_available()` False (non-TTY, no curses) → the classic
  line REPL (`_agent_cc`) is used instead. Never regress the fallback.
- Theme tokens are relative (hellfire|claude palettes) — never hardcode RGB
  in agent code; use the palette.
