# HELLFORGE HellGate

A wrapper that boots and launches **OpenCode** directly, focused inside the
HELLFORGE root, with the full E Language knowledge pack fed in.

```
run.py hellgate
```

## What happens per launch

1. **Wrapper warning** — "HellGate is just a wrapper — not an official
   product of OpenCode." Shown **every** launch.
2. **First-run onboarding** on a NEW machine — detected by machine specs
   (cpu/arch/hostname/python), not by session history, so a fresh PC with
   old state still gets the questions:
   - "Do you agree *summertime rendering* is the greatest anime of all
     time?" — N exits, Y continues.
   - The legal one: agree to use this software under the HellGate wrapper
     and the OpenCode MIT License, HellGate being independent of OpenCode's
     projects, trademarks and support. N exits.
3. **Provider/model resolution** — provider registry: Anthropic, OpenAI,
   OpenRouter, Google Gemini, custom, then Ollama **last**. Default is the
   first provider with an API key set; with no keys, Ollama (only when
   `ollama serve` is running). Ollama asks for a model via a select list of
   every installed model (`/api/tags`) whenever no model is chosen yet.
4. **HellCode welcome page** — banner + `HellGate v<version>`, `- T3ntari`
   tiny at the bottom, and a loading screen: dots spinner, real init steps
   (imports, compile checks, self-tests, knowledge pack, config) with a
   `x/1024` counter below the loader.
5. **OpenCode TUI**, directly — agent (Music-Composer / Music-Refiner),
   knowledge, provider/model all preconfigured.

After OpenCode exits: `Enter` relaunches, `$provider` / `$model` /
`$agent` / `$dir` / `$new` manage the session, `q` quits.

## Session commands

| Command | What it does |
|---|---|
| `Enter` / `$new` | relaunch OpenCode (fresh chat) |
| `$agent [name]` | Music-Composer, Music-Refiner, or default |
| `$provider [name]` | show / switch provider (ollama is one option — and asks for a model) |
| `$model [name]` | show / set the model for the current provider |
| `$dir [path]` | show / add a project directory (default: the root) |
| `$help`, `q` | help / quit |

## How it works

- **Confinement** — OpenCode runs with cwd = the project dir and all configs
  land under `hellgate-state/` inside the repo; no global config writes.
- **Knowledge** — `knowledge/full.md` (comprehensive, v5-first), `core.md`
  (distilled ~30% "75% index" digest), `samples-index.md`, `agents.md`
  (Music-Composer / Music-Refiner personas). At launch `current.md` is
  prepared: small-context models get the digest, larger ones the full map.
- **Low-context summarizer** — `summarizer.py` re-digests the docs with the
  local Qwen2.5-Coder-3B (ollama) into `knowledge/core-llm.md`.
- **Providers** — `hellgate-state/provider.json` drives every launch.
  Keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`,
  `GEMINI_API_KEY`; `HELLGATE_MODEL` / `HELLGATE_OLLAMA_URL` override the
  ollama path.

## Licensing

HellGate launches the official OpenCode CLI unmodified (MIT — see
`licenses/MIT-OpenCode.txt`). HellGate itself is MIT. It is a wrapper, not
an official product of OpenCode.
