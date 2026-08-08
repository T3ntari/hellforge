# Copilot Tool Protocol (plugins/llm + ai.py)

The repo embeds an LLM copilot. CLI: `ai.py` (thin wrapper over
`plugins/llm`). When acting as the copilot you emit a **JSON plan** — the
harness parses, previews diffs, confirms with the user, applies, runs
commands/tests, and feeds results back. When done, reply `{"done": true}`.

## Commands

```
ai fix "<issue>" [--yes]   multi-step loop: plan → review → apply → verify →
                           repeat (≤5 steps); --yes auto-applies writes/edits
ai agent                   interactive multi-turn REPL with edit capability
ai chat / ai ask "<q>"     chat / one-shot answer (no edits)
ai read <file> [start [end]]   line-numbered file view
ai plugin "<description>"  generate a plugin skeleton
ai todo | review | cost | status | setup | provider | model | url | key
ai agents on|off           multi-agent verification (daughter agent reviews)
ai index build|status|off  project index; ai index-model <name> (Ollama)
```

`ai agent` REPL: `/status`, `/read`, `/todo` slash-commands, context
compaction, persisted sessions.

## JSON plan format (exact)

```json
{
  "summary": "one-line description",
  "commands": [{"cmd": "python tests/v5_statements_test.py"}],
  "tests": "all",
  "todo": [{"item": "fix velocity bug", "status": "done"}],
  "subagents": [{"task": "...", "context": "..."}],
  "files": [
    {"path": "ep_compiler/loops.py", "action": "edit",
     "lines": [1525, 1531], "replace": "new text for those lines"},
    {"path": "plugins/myplug/__init__.py", "action": "write",
     "content": "# full new file ..."}
  ]
}
```

Plan keys: `summary` · `commands` (validated safe executables) · `tests`
("all" or list; auto-fix loop until green) · `todo` (TODO.md: `open` adds,
`done` checks off) · `files` · `subagents` (≤4 focused child chats) · `done`.

## Actions

- `read` — display file (no change); `start`/`end` line range.
- `write` — create a **new** file with `content`; refused for existing files
  unless the user types full-word `yes`.
- `edit` — existing file: `lines: [a, b]` + `replace` = replace range
  (1-based inclusive); `lines: [x]` alone = insert before line x. Alt:
  `edits: [{"search", "replace"}]` (search must match exactly once).
- `delete` — always requires explicit per-file confirmation; refused off-TTY;
  never via `a`/all.

## Modes

- **plan** — model returns plans; user confirms each change
  (`y`/`n`/`v` view/`a` apply-all/`q` quit).
- **auto** — `ai fix --yes` auto-applies writes/edits; deletes still need
  per-file confirmation. **ask/chat** — plain text, no edits.

## Safety rules (non-negotiable)

1. **Edit-not-rewrite**: existing files are line-range edits or unique
   search/replace blocks; whole-file writes refused without explicit `yes`.
2. **Deletes confirmed** individually, always; `a` never auto-confirms.
3. **Path bounds**: relative paths only, inside the project root; `..`,
   absolute paths, the root itself rejected. Protected dirs (`.e_identity/`,
   `.fent_cache/`, `.radical_cache/`, `.venv/`, `node_modules/`, `logs/`,
   `__pycache__/`, `.git/`) never touched.
4. **Command allowlist** (exec.py): no `rm`/`mv`/`sudo`/`pip`/`curl`/`wget`;
   no shell metachars or `..`; `git` only for safe subcommands (status/diff/
   log — push/pull/reset/checkout banned); `python -c` and os/sys/subprocess/
   open modules banned; 30s timeout; 4000-char output cap. `python` → venv.
5. **No secrets, no network calls without opt-in**, no fabrication: never
   claim a file exists without reading it.

## Thinking & flow

The CLI shows a thinking indicator while the model works (`ui.thinking`);
plans are parsed tolerantly (markdown fences, trailing prose, `r"..."`
slips; one automatic retry demanding pure JSON on failure). After any `.py`
write/edit a py_compile syntax check runs automatically; then `todo`,
`subagents`, and (if enabled) a **daughter-agent review** run before the
next loop iteration. Reply `{"done": true, "summary": "..."}` when finished.

## TODO.md

Live checklist at repo root. Maintained through the plan `todo` key — the
system edits the file; never rewrite it wholesale. Add `- [ ]` items, check
them off as you complete them; never delete items.

## Search & context

- **Index** (`ai index build`): keyword index (`.py/.e/.ei/.enx/.eci/.eic/
  .md/.json/.lua/.js/.ts/.html`) in `.fent_cache/llm_index.json` (gitignored);
  path tokens weight ×3, first line ×2.
- **Semantic**: optional Ollama embeddings (`ai index-model <name>`) —
  cosine-ranked; falls back to keyword.
- **Context builder**: project tree + files the request names + keyword-window
  line ranges, ~60KB budget — relevant code, not whole files. `ai read` for
  precise line-numbered views.

## Sessions & subagents

`ai chat`/`ai agent` persist sessions (provider/model/turns/summary),
resumable via `ai resume`/`ai sessions`. The `subagents` plan key runs up
to 4 focused child requests in parallel; daughter-agent verification
(`ai agents on`, `ai agent-model`) reviews changes read-only before each
next step.
## HELL'S CODE TUI

`ai agent` may run as a full-screen curses TUI. The agent logic lives on a
background thread and talks to the frame loop through a Bridge:

- `stream(text)` — streamed reply chunks (displayed live)
- `feed(text, color)` — a full line in the feed (colors: accent/accent2/
  text/dim/ok/err/warn)
- `box_open(title)` / `box_line(text)` / `box_close(summary)` — bordered
  sub-window for command output (never spam the main feed)
- `ask(question, detail, choices)` — gatekeeper modal; BLOCKS the agent
  thread until the user answers y/n/e
- `status(text)` / `thinking(on)` — status bar and thinking indicator

When running headless (no TTY), the same flows run through the classic line
REPL — behavior parity is required, not just the TUI path.
