# LLM Copilot Commands (`ai`)

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [llm-commands](llm-commands.md) | [plugin page](../plugins/llm.md)

The **llm** plugin registers the `ai` command (alias `llm`) — the AI
copilot. Providers: **ollama, openai, anthropic, deepseek, custom** — the
choice is yours; nothing is hardcoded and no keys ship with the repo.

## ai status
**Syntax:** `ai status`
**Description:** Show the current provider/model/connection state.

## ai provider
**Syntax:** `ai provider <openai|deepseek|claude|ollama|custom>`
**Description:** Select the provider. `ai provider ollama` auto-detects the local server and asks which model to use; the selection is saved. `ai disconnect` stops.
**Example:** `ai provider ollama`

## ai model
**Syntax:** `ai model [<name>]`
**Description:** List known models for the current provider / set the model.
**Example:** `ai model llama3.1`

## ai url
**Syntax:** `ai url <base_url>`
**Description:** Set a custom OpenAI-compatible endpoint base URL.
**Example:** `ai url http://127.0.0.1:11434/v1`

## ai key
**Syntax:** `ai key <key>`
**Description:** Set the API key for the current provider (stored locally in `.plugin_config.json`, never committed).
**Example:** `ai key sk-...`

## ai ask
**Syntax:** `ai ask "<question>"`
**Description:** Single-shot question to the model.
**Example:** `ai ask "What does a tie do in v5?"`

## ai chat
**Syntax:** `ai chat`
**Description:** Interactive multi-turn chat session.

## ai fix
**Syntax:** `ai fix "<issue>"`
**Description:** Agentic edits — the copilot plans, reviews, applies and
verifies, confirming before touching files.

## ai plugin
**Syntax:** `ai plugin "<description>"`
**Description:** Generate a plugin skeleton from a description.

## run.py entry points

```bash
run.py ai <subcommand>        # same engine, CLI form
run.py ai bridge              # stdio bridge (JSON lines) for the TypeScript TUI
```

The copilot agent instructions live in `AGENTS.md` / `RULES.md` / `TODO.md`;
the HELL'S CODE TUI (`ai agent --tui`) is a full-screen curses interface.
HellGate (`run.py hellgate`) reuses the same provider registry with
`$provider`/`$model`/`$agent` session commands — see
[HellGate](../plugins/hellgate.md).

---

See also: [LLM plugin page](../plugins/llm.md) · [Getting started](../getting-started.md)
