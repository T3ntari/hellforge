# Copilot (plugins/llm) & HellGate Agents

Two agent surfaces ship with HELLFORGE:

1. The **built-in copilot** (`run.py ai` / `ai.py`, engine in
   `plugins/llm/`) — an LLM agent that edits the repo through a JSON plan
   protocol.
2. **HellGate** (`run.py hellgate` / `krip hellgate`) — a wrapper that boots
   **OpenCode** with two music-agent personas (Music-Composer,
   Music-Refiner) and the knowledge pack. You may be acting inside either.

## The llm copilot plugin

Providers: `openai | deepseek | claude | ollama | custom` (OpenAI-compatible;
`ai url <base_url>` for custom endpoints). State (provider/model/key) is
persisted in `.plugin_config.json`; the API key is stored via the auth-token
store.

Commands (`ai status|setup|provider|model|url|key|connect|disconnect`):

```
ai ask "<question>"        one-shot answer (no edits)
ai chat                    interactive REPL chat (no edits)
ai fix "<issue>" [--yes]   multi-step agentic loop: plan → review → apply →
                           verify → repeat (≤5 steps); --yes auto-applies
ai plugin "<description>"  generate a plugin skeleton in plugins/<name>/
ai read <file> [start [end]]  line-numbered file view
ai agent                   interactive multi-turn REPL with edit capability
ai agents on|off           multi-agent verification (daughter agent reviews)
ai index build|status|off  project index; ai index-model <name> (Ollama)
```

`ai ask`/`ai chat` use a **two-mode intent router**: explicit `/fix`-style
prefixes and plain-language task-intent phrases route to the agentic loop
(tools, file edits, command execution); everything else stays a chat
answer. `ai fix` is the full agent loop.

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

## Safety rules (non-negotiable)

1. **Edit-not-rewrite**: existing files are line-range edits or unique
   search/replace blocks; whole-file writes refused without explicit `yes`.
2. **Deletes confirmed** individually, always; `a` never auto-confirms.
3. **Path bounds**: relative paths only, inside the project root; `..`,
   absolute paths, the root itself rejected. Protected dirs (`.e_identity/`,
   `.venv/`, `hellgate-state/`, `logs/`, `__pycache__/`, `.git/`) never
   touched.
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
  .md/.json/.lua/.js/.ts/.html`) — gitignored cache; path tokens weight ×3,
  first line ×2.
- **Semantic**: optional Ollama embeddings (`ai index-model <name>`) —
  cosine-ranked; falls back to keyword.
- **Context builder**: project tree + files the request names + keyword-window
  line ranges, ~60KB budget — relevant code, not whole files. `ai read` for
  precise line-numbered views.

## HELL'S CODE TUI

`ai agent` may run as a full-screen curses TUI. The agent logic lives on a
background thread and talks to the frame loop through a Bridge:
`stream(text)`, `feed(text, color)`, `box_open/box_line/box_close`
(sub-windows, never spam the main feed), `ask(...)` (gatekeeper modal,
BLOCKS until y/n/e), `status(text)` / `thinking(on)`. Headless (no TTY) →
the classic line REPL; behavior parity is required, not just the TUI path.

## HellGate — OpenCode wrapper & personas

HellGate is a wrapper (not an official OpenCode product) that boots OpenCode
focused in this repo. Per launch: wrapper warning → first-run onboarding
(new machines, specs-based) → provider resolution → HellCode welcome +
`x/1024` loading → OpenCode TUI.

- **Provider registry** (first-available wins, Ollama last): Anthropic,
  OpenAI, OpenRouter, Google Gemini, custom, Ollama (model select list from
  `/api/tags`).
- **Agents**: `$agent` switches between **Music-Composer** and
  **Music-Refiner** — personas defined in
  `plugins/hellgate/knowledge/agents.md` (each `## <Name>` section is the
  agent's system prompt).
- **Knowledge pack**: `full.md` (comprehensive map), `core.md` (distilled
  digest — served to small-context models), `samples-index.md`, `agents.md`.
- Everything runs inside the **K-rip sandbox** (launched via
  `krip hellgate`): stay in the project root, never touch `.e_identity/`,
  `.venv/`, `hellgate-state/` (session/provider state lives there).
- Session commands after OpenCode exits: `Enter`/`$new` relaunch,
  `$agent`, `$provider`, `$model`, `$dir`, `q` quit.
