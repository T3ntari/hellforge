# LLM — AI Copilot

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [hellgate](hellgate.md) | [llm](llm.md) | [commands](../commands/llm-commands.md)

---

## Overview

The **llm** plugin is the AI copilot: `ai ask`, `ai chat`, `ai fix`,
`ai plugin`, with providers **ollama, openai, anthropic, deepseek, custom**
(OpenAI-compatible endpoints via `ai url`). Ollama is auto-detected at
`ai provider ollama` — it asks which model to use and saves the selection;
`ai disconnect` stops.

## Commands

`ai status` · `ai provider <name>` · `ai model [name]` · `ai url <base>`
· `ai key <key>` · `ai ask "<q>"` · `ai chat` · `ai fix "<issue>"`
· `ai plugin "<desc>"` — registered as `ai` (alias `llm`, marked
`(alias)` in help). See [LLM commands](../commands/llm-commands.md).

## Agentic mode

`ai fix` runs a multi-step agentic loop (plan → review → apply → verify →
repeat) through a JSON plan format and maintains the project checklist in
TODO.md. The agent instructions live in `AGENTS.md` / `RULES.md` /
`TODO.md`. The HELL'S CODE TUI (`ai agent --tui`) is a full-screen curses
interface with a screen buffer, 10fps frame loop, gatekeeper approval
modal and scrollback — auto-detects a real terminal, falls back to the
line REPL.

## Config & keys

Keys are stored locally (`.plugin_config.json`, never committed). The
engine used by this plugin is shared with HellGate's provider registry.

---

See also: [HellGate](hellgate.md) · [LLM commands](../commands/llm-commands.md) · [Getting started](../getting-started.md)
