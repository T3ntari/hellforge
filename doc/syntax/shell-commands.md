# Shell Commands — eshell Reference

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md) · [Core commands](../commands/core-commands.md)

The **eshell** is the HELLFORGE console. You reach it by booting through
K-rip (`run.py krip` → Enter, or `c`), via `run.py shell`, or directly
with `eshell.py` (which re-enters through K-rip unless `KRIP_BYPASS=1`).
Every start runs the integrity sequence first (Technique X → Y).

## Built-in commands

| Command | Description |
|---------|-------------|
| `cd <dir>` / `ls` | navigate the project |
| `compile <spec> [-o <out>] [--human\|--machine] [--recursive]` | compile `.e`/`.ei`/`.eci`/`.enx` → `.mid`/`.wav`/`.ec`/`.eic` |
| `convert <f>` | import MIDI/audio → `.e` (`--project` for `.ei`) |
| `play <f>` / `gui <f>` | play / open in the glassmorphism window |
| `info <f>` / `stats <f>` | file stats: notes, duration, range, velocity, polyphony, channels |
| `tracks <f>` / `inspect <f> [N]` | per-channel table / first N events (default 12) |
| `new <name>` | scaffold a v5 project (`index.ei` + `parts/main.e`) |
| `transpose <f> <n>` / `tempo <f> <bpm>` / `merge <a> <b>` | editing helpers ([-o out]) |
| `sign <f>` | sign a file — local ED25519 (`sign --setup` first) |
| `encrypt <f>` / `ecc <f>` | encrypt to `.ee` / compile+encrypt to `.ecc` |
| `mod <cmd>` / `plugin <cmd>` | manage mods/plugins (list/avail/scan/update/fetch/remove/version) |
| `pkglist <cmd>` | package registry (show/update/search/version/detail) |
| `ezip <cmd>` | install `.ezip` packages (install/list) |
| `gc <cmd>` | garbage collection (enable/disable/flush/clean/status) |
| `sys <cmd>` | system management (status/scan/reload/reset/panic, `sys strict 0\|1\|2`) |
| `audio <cmd>` | audio devices & config (devices/set-device/config) |
| `clear` / `help` / `exit` | screen, help, quit |

## Plugin commands

`help` lists, in order:

1. the **built-ins** above,
2. **plugin-authored help sections** — plain lines (`  ai status ...`) or
   `(cmd, desc)` pairs (e.g. the LLM copilot section),
3. **plugin commands grouped by the plugin that registered them** — names
   are dimmed and marked `(alias)` when the help text says "alias"
   (e.g. `pb` for portbaby, `launch` for launcher, `learn` for learner,
   `llm` for ai).

Notable plugin commands: `krip` (hypervisor — see
[K-rip commands](../commands/krip-commands.md)), `ai` (copilot — see
[LLM commands](../commands/llm-commands.md)), `humanize`,
`talisman`, `eaudio`, `radical`, `tensorsharp`, `openapi`, `vulkanizer`,
`lure`, `portbaby`, `learner`, `launcher` — each documented under
[doc/commands/](../commands/core-commands.md).

## run.py modes (same commands, CLI form)

```bash
run.py play|compile|check|shell|ai|bridge|hellgate|integrity|krip
run.py stats|tracks|inspect|new|transpose|tempo|merge <args>
```

`run.py krip` (or `krip` inside the shell) gives the hypervisor controls —
boot menu, sandbox, safe update.

---

**HELLFORGE OS v0.1.14.41-beta** — eshell: the console
