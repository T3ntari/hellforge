# HELLFORGE — Core Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [krip-commands](krip-commands.md) | [integrity-commands](integrity-commands.md) | [llm-commands](llm-commands.md)

These are the **built-in** eshell commands plus the `run.py` CLI modes. Every
launch re-enters through the K-rip hypervisor (`KRIP_INNER=1` marks children,
`KRIP_BYPASS=1` escapes). Plugin-registered commands are listed in their own
pages.

## eshell built-ins

## cd
**Syntax:** `cd <path>`
**Description:** Change the current working directory within eshell.
**Example:** `cd songs/`

## ls
**Syntax:** `ls [path]`
**Description:** List files and directories.
**Example:** `ls doc/commands/`

## compile
**Syntax:** `compile <spec> [-o <out>] [--human] [--machine] [--recursive]`
**Description:** Compile `.e`/`.ei`/`.eci`/`.enx` sources to `.mid`/`.wav`/`.ec`/`.eic` (`--human`/`--machine` convert between modes inside `.eic`).
**Example:** `compile songs/aurora_nocturne.e -o aurora.mid`

## convert
**Syntax:** `convert <input>`
**Description:** Import MIDI/audio → `.e` source; `--project` for `.ei` project structure.
**Example:** `convert input.mid`

## play / gui
**Syntax:** `play <file>` · `gui <file>`
**Description:** Play a file (or open it in the glassmorphism window).
**Example:** `play songs/aurora_nocturne.e`

## info / stats / tracks / inspect
**Syntax:** `info <file>` · `stats <file>` · `tracks <file>` · `inspect <file> [N]`
**Description:** File stats (notes, duration, range, velocity, polyphony, density, channels), per-channel tables, and the first N events (default 12).
**Example:** `inspect songs/aurora_nocturne.e 20`

## new
**Syntax:** `new <name> [-o <dir>]`
**Description:** Scaffold a v5 project directory (`index.ei` + `parts/main.e` + `README.md`).
**Example:** `new my-piece`

## transpose / tempo / merge
**Syntax:** `transpose <file> <semitones> [-o out]` · `tempo <file> <bpm> [-o out]` · `merge <a> <b> [-o out]`
**Description:** Shift notes, recompile at a new tempo, concatenate two files.
**Example:** `transpose song.mid 2`

## lint
**Syntax:** `lint <spec>`
**Description:** Run the v5-aware linter (same diagnostics as `run.py check`).
**Example:** `lint songs/`

## sign
**Syntax:** `sign <file>`
**Description:** Sign a file with your local ED25519 identity (`sign --setup` creates it under `.e_identity/`).
**Example:** `sign songs/aurora_nocturne.e`

## encrypt / ecc
**Syntax:** `encrypt <file> [-o <out.ee>]` · `ecc <file> [-o <out.ecc>]`
**Description:** Encrypt a file to `.ee`, or compile+encrypt to `.ecc` (one step).
**Example:** `encrypt song.e -o song.ee`

## mod / plugin / pkglist / ezip
**Syntax:** `mod <cmd>` · `plugin <cmd>` · `pkglist <cmd>` · `ezip <cmd>`
**Description:** Manage mods and plugins (list/avail/scan/update/fetch/remove/version), the package registry (show/update/search/version/detail), and install `.ezip` packages (install/list).
**Example:** `plugin list`

## audio
**Syntax:** `audio <cmd>`
**Description:** Audio devices & config (devices/set-device/config).
**Example:** `audio devices`

## gc
**Syntax:** `gc <cmd>`
**Description:** Garbage collection (enable/disable/flush/clean/status).
**Example:** `gc status`

## sys
**Syntax:** `sys <cmd>`
**Description:** System management (status/scan/reload/reset/panic, `sys strict 0|1|2`).
**Example:** `sys strict 2`

## clear / help / exit
**Syntax:** `clear` · `help` · `exit`
**Description:** Clear the screen; show help (built-ins → plugin help sections → grouped plugin commands with dimmed `(alias)` markers); quit.

## `run.py` CLI modes

```bash
run.py play <file> [--gui] [--window] [--detach]
run.py compile <spec> -o <out> [--to v5] [--strict] [--mem] [--recursive]
run.py check <spec> [--recursive] [--max <N>]      # v5-aware lint
run.py shell | stats | tracks | inspect | new | transpose | tempo | merge
run.py ai <cmd>                                    # LLM copilot
run.py bridge                                      # stdio bridge for the TS TUI
run.py hellgate                                    # HellGate -> OpenCode
run.py integrity [--github]                        # X/Y digest verification
run.py krip [run|eshell|hellgate|player|status]    # the hypervisor entry
```

- `--window` opens a dedicated console window; `--detach` runs in the
  background logging to `logs/`; `--gui` uses the pygame glassmorphism
  player.
- `compile --to <v1|v2|v3|v4|v5>` converts syntax instead of exporting
  MIDI (via the portbaby plugin).
- `--strict` fails fast on any diagnostic; `--mem` prints the in-memory
  event estimate.

See also: [K-rip commands](krip-commands.md) · [Integrity commands](integrity-commands.md) · [LLM commands](llm-commands.md)
