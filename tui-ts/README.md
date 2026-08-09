# HELL'S CODE — TypeScript TUI

A full-screen terminal UI for the HELLFORGE copilot, built with Ink + React.

## Architecture
- `src/bridge.ts` — spawns `python run.py bridge` (JSON-lines stdio),
  typed event emitter with replay (no lost early events), buffered sends
- `src/protocol.ts` — shared PyToTs / TsToPy message types
- `src/App.tsx` — Ink root: splash with setup checklist, status bar
  (model · mode · branch · tokens), streaming feed, tool accordion,
  sub-windows, gatekeeper modal, command palette, model picker
- `src/frame.ts` — feed reducer, word-wrap, scroll math, palette→ANSI
- `src/theme.ts` — hellfire palette (fiery red, ember, cream, dim grey)
- Components: Header, StatusBar, Footer, Splash, ChatFeed, ToolPanel,
  SubWindow, Gatekeeper, ModelPicker, CommandPalette, Complete

## Run
```bash
npm install
npm run build
node dist/index.js          # from anywhere in the repo tree
```

## Keys
Ctrl+C copy line · Ctrl+V paste · Ctrl+X cut · PgUp/PgDn scrollback ·
↑/↓ history · `/` command palette · `/exit` leave

## Protocol (Python side)
`run.py bridge` — two-mode router (chat vs agent), streaming replies,
plans, gatekeeper asks, sub-window events. See plugins/llm/bridge.py.
