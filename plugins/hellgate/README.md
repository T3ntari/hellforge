# HELLFORGE hellgate

Launch the proper agent TUIs — OpenCode, Aider, OpenHands, Goose — focused
inside the HELLFORGE root, with the full E Language knowledge pack fed in.

```
run.py hellgate                 # interactive picker
run.py hellgate opencode        # launch one tool directly
```

## Session commands

| Command | What it does |
|---|---|
| `1`–`4` / Enter | launch a tool (fresh chat), default project dir = HELLFORGE root |
| `$change` | switch to another tool |
| `$new` | start a fresh chat in the current tool |
| `$dir [path]` | show / add a project directory (default: the root) |
| `$agent [name]` | Music-Composer, Music-Refiner, or default |
| `$provider [name]` | show / switch provider — Anthropic, OpenAI, OpenRouter, Gemini, custom, or Ollama (last option, never the default) |
| `$model [name]` | show / set the model for the current provider |
| `$help`, `quit` | help / exit |

## How it works

- **Confinement** — every tool runs with cwd = the chosen project dir and all
  generated configs land under `hellgate-state/<tool>/` inside the repo; the
  tools never write global config. OpenHands additionally needs Docker
  (checked at detect; launch explains if missing).
- **Knowledge** — `knowledge/full.md` (comprehensive, v5-first), `core.md`
  (distilled ~30% "75% index" digest), `samples-index.md` (samples/examples
  map), `agents.md` (Music-Composer / Music-Refiner personas). At launch,
  `knowledge/current.md` is prepared automatically: small-context models get
  the distilled digest, larger ones the full map.
- **Low-context summarizer** — `summarizer.py` re-digests the docs with the
  local Qwen2.5-Coder-3B (ollama) into `knowledge/core-llm.md`; used when a
  session context budget is ~75% spent (`needs_digest`).
- **Agents** — Music-Composer (writes v5 songs from scratch) and
  Music-Refiner (fixes/refines existing `.ec` files, converts v1–v4 → v5),
  each fed with the v5 statement set from `tests/v5_statements_test.py`.
- **Providers** — `hellgate-state/provider.json` drives every launch.
  Registry order: Anthropic, OpenAI, OpenRouter, Google Gemini, custom
  (OpenAI-compatible), Ollama LAST. The default is the first provider whose
  API key is set in the environment; with no keys anywhere, Ollama is the
  last-resort local option (only when `ollama serve` is actually running).
  Keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`,
  `GEMINI_API_KEY`; `HELLGATE_MODEL` / `HELLGATE_OLLAMA_URL` still override
  the ollama path.

## Licensing

See `licenses/NOTICE.md`. OpenCode/OpenHands are MIT, Aider/Goose are
Apache-2.0; HELLFORGE bundles no tool source, it launches the official
installers unmodified.
