# HELLFORGE Knowledge Pack — Full Map (v5-accurate)

Comprehensive, code-verified knowledge digest for coding agents (OpenCode
via HellGate, Aider-style) working in the HELLFORGE (E) piano-music DSL
repo. Source-of-truth checks: `tests/v5_statements_test.py`,
`tests/security_hash_test.py`, `plugins/krip/tests/test_krip.py`,
`docs/agent/*.md`, `SYNTAX.md`, `run.py`, and the samples/examples tree.

---

## 1. What HELLFORGE Is

**HELLFORGE (E)** is a domain-specific language for piano music composition.
You write music as plain text — notes, chords, rhythms, dynamics — and E
compiles it to `.mid`, `.wav`, `.mp3`, `.mp4`, `.ec` (compiled binary),
`.eic` (one-file bundle), and more. Version **v0.1.14.41-beta**. No piano
or programming experience is required.

HELLFORGE is built like an **OS**:
- **kernel** = `ep_core.py` — plugin/mod registry, event hooks, GC, ED25519
  signing, identity, encryption, ezip
- **plugins = drivers** — 14 shipped drivers under `plugins/`
- **hypervisor = K-rip** (`plugins/krip/`) — boot manager + sandbox layer
  (`krip os` shows the table: kernel · hypervisor · drivers)

- **Runtime:** Python 3.10+ (dev/tested on 3.11). Always run Python through
  the project venv — `.venv/bin/python ...`, never bare `python`.
- **Compiler pipeline:** `.e` source text → `compile_source()` in
  `ep_compiler/compile.py` → a list of **event dicts** → export. The event
  dict is the single contract every parser produces:
  `{"timestamp" (int ms), "midi" (0-127), "duration" (ms), "velocity" (0-127),
  "pan" (-1..1), "bend" (-64..64)}` plus optional keys (`channel`, `track`,
  `sustain`, `pedal`, `art`, `tie`, `octave`, `master_vol`, `gain_db`,
  `filter_*`, `env_*`, `phase`, `cents`, `swing`, `strum`).
- **v5 writing is human-mode + statements** (auto-detected, no headers):
  `play note(C4) @dur:q @vel:mf`, `prog(...)`, `perc(...)`, loops, `!fn`
  macros, pedal/rest/articulations/curves/ties. Machine lines
  (`T0 N60 D500 V80`) compile only as legacy — never write them.
- **Project layout:** `ep_compiler/` (compiler core), `plugins/` (drivers),
  `tests/` (self-contained test harnesses, no pytest), `samples/` (example
  `.e` sources by syntax version), `songs/` (complete v5 pieces),
  `examples/` (full compositions, projects, albums, demos),
  `docs/agent/` (model-consumable docs), `SYNTAX.md` (full reference),
  `AGENTS.md`/`RULES.md` (agent rules).

---

## 2. You Are Running Inside K-rip

Everything in this repo launches through the **K-rip hypervisor**
(`plugins/krip/`):

- **Boot flow:** `krip` (no args) → GRUB-style menu (3s countdown, ↑/↓
  select, Enter boot, `c` console, `u` update, Esc exit) → boot the kernel
  → drop into the **eshell console**.
- **Sandbox layer:** memory budget (RLIMIT_AS), CPU thread caps + affinity,
  GPU selection (`CUDA_VISIBLE_DEVICES`; auto|list|all|"0,1" multi-GPU),
  graphics engine (vulkan default / opengl), vulkanrt on/off, tensor
  on/off/auto. Config lives in **`krip.json`** at the project root; `krip
  edit` opens it in nano with live reload.
- **Commands:** `krip status` (allocation) · `krip os` (kernel/driver
  table) · `krip sandbox run <name> -- <cmd...>` / `list` / `kill` ·
  `krip run <cmd...>` · `krip eshell|shell` · `krip hellgate` ·
  `krip player <file>` · `krip kernels` (current + previous) ·
  `krip mem <mb>` / `cpu <n>` / `gpu <spec>` / `engine <vulkan|opengl>` /
  `vulkanrt <on|off>` / `tensor <on|off|auto>` / `config` / `reload` /
  `reset`.
- **Every `run.py` mode re-enters through krip** (self-spawn inside the
  sandbox). Children carry `KRIP_INNER=1` (no re-wrap), `KRIP_SANDBOX`,
  `KRIP_ENGINE`, `KRIP_VULKANRT`, `KRIP_TENSOR`, GPU env. `KRIP_BYPASS=1`
  skips the wrap; `KRIP_NO_MENU=1` boots straight to the console.
- **Kernel registry** (`.e_identity/kernels.json`): the current version
  plus the previous one (normal + safemode entries). Booting a previous
  entry performs a **safe update** to that tag (rollback — nothing lost).
  The menu shows a "NEW KERNEL AVAILABLE" notice; `u` updates.
- The sandbox confines processes to the project root. **You (the agent)
  are inside this sandbox: stay in the project root; never touch
  `.e_identity/`, `.venv/`, `hellgate-state/`, `logs/`, `.git/`.**

---

## 3. v5 Canonical Syntax — The Statement Set

**v5 is canonical.** Every source compiles as v5 by default. v1–v4 still
compile for backward compatibility but are **deprecated** and emit warnings
(e.g. `v4 syntax is deprecated — use v5 (convert with 'run.py compile --to v5')`).
New syntax goes ONLY in the v5 path (`ep_compiler/`) and only if it is in
`SYNTAX.md`. `run.py compile <old.e> --to v5` converts old sources.

The statement list below is verified against `tests/v5_statements_test.py`
(29/29 passing). Exact spellings:

### Statements (v5 statement set)

| Statement | Exact form | What it does |
|---|---|---|
| `print` | `print "hello"`, `print {2 + 3}`, `print N60`, `print $var` | Emits a value (literal string, `{expr}`, note name, `$var`); resolves inside loop bodies too (`print {$i}`) |
| `assert` | `assert {2 + 2} == 4, "ok"`, `assert $x == 60, "x"` | Compile-time/runtime check; **compile fails** when false (AssertionError with the message); `$var` and `{expr}` conditions allowed |
| `include` | `include "hook.e"` | Source-level include; inlines the file **relative to the source dir** before version detection; missing file raises (`cannot find`); circular includes rejected (depth limit) |
| `!fn` macros | `!fn f(ts, note) = T{$ts * 100} N{$note} D200 V80` then `!f(0, 60)` | Parameterized macro definition + invocation. Args: literals `!f(0, 60)`, loop vars `!f($i, 60)`, expressions `!f({2 + 3}, 60)`, note names `!n(C4, 1)`; `$name` params substituted in the body |
| `prog` | `prog(C:q G:q Am:h F:q)` | Chord-progression shorthand: `root:duration` per chord, expands to stacked chord notes (C major = 60/64/67; `q` = 500ms, `h` = 1000ms) |
| `perc` | `perc(kick)`, `perc(snare)`, `perc(hihat)` | GM percussion on **channel 9** (kick=36, snare=38, hihat=42; also clap, openhat, tom_low/mid/high, crash, ride, tambourine, cowbell, shaker); unknown drum names are rejected (`unknown drum`) |
| `@seed` + `pick`/`rand` | `@seed 42` + `$x = pick(60 64 67)`, `$y = rand(1, 4)` | Deterministic randomness: same seed → same pick; `rand(a, b)` is inclusive int in range |

### Loops (all with `break` / `continue`; single- or multi-line `{ }`)

| Form | Example | Notes |
|---|---|---|
| List | `for $n in [C4 E4 G4] { T0 N $n D100 V80 }` | Iterates literal note list |
| Range | `for $i in 1..4 { ... }` | **Inclusive** `1..N` |
| Scale | `for $n in scale(C major, 4, 1) { ... }` | `scale(name, octave, octave_count)`; `scale(A minor, 4, 2)` = 14 notes, 2 octaves |
| Chromatic run | `for $n in run(C4, E4) { ... }` | **Inclusive** chromatic run (C4 D4 E4) |
| Fixed count | `repeat 5 { ... }` | `break`/`continue` work inside `repeat` too |

Scale names: `major minor harmonicminor melodicminor pentatonic blues dorian
phrygian lydian mixolydian locrian chromatic wholehalf halfwhole`. Loop
unroll cap 100k; loop vars resolve in `print`, `assert`, `!fn` args, and
math expressions.

### Piano-performance layer (v5 = v4 + these)

- `pedal on` / `pedal off` / `@pedal:<0-127>` — sustain CC64
- `rest q` / `rest 500ms` / `R 500ms` — silence advancing the cursor
- `@art:staccato|legato|tenuto|accent` — articulations
- Tuplets: `t3(C4 E4 G4)`, `trip(...)`, `tup(5,1,...)`, `[C4 D4 E4]/3`
- `@oct:+1` / `@oct:-1` — octave shift
- `@curve vel 60 115` (+ `over 4q` windowed) — velocity curves
- Ties: `C4~ q q` shorthand, `@tie` — merged durations

### Human-mode play statements (canonical note writing)

`play note(C4) @dur:q @vel:mf`, `play chord(C, major) @dur:h @vel:ff`;
quality table `major minor dim aug dom7 maj7 min7 dim7 sus2 sus4 m m7 7 maj
min`; extra props `@pan:`, `@bend:`, `@ch:`, `@track:`, `@time:`,
`@sustain:`, `@art:`, `@oct:`, `@tie`, `@strum:`; dotted durations `q.`.
Durations `w h q e s t` = 4/2/1/½/¼/⅛ beats; velocity words
`ppp pp p mp mf f ff fff`.

### Directives (`@`-prefixed)

`@bpm 120` (also `@tempo`, Italian aliases `@allegro @adagio ...`),
`@key C major`, `@scale A_minor` (quantize; `off` disables), `@vol:0.7`,
`@master:0.7`, `@gain:-3db`, `@sr:44100`, `@bit:16`, `@quality:standard`,
`@sub:40hz`, `@bass_boost:3db`, `@stereo_width:120`, `@neural on`,
`@mem:64k` (event budget warn+truncate), `@seed 42`, `@gc:aggressive`,
`@oct:+1`, `@pedal:64`, `@sustain:64`, `@strict on|off`.

### Math, variables, randomness

`$x = 60`, `$x = {$bpm * 2}` `{expr}` substitution
(`+ - * / // % ^ ( )`), `@dur:{$d * 0.5}ms` inline expressions. Known
functions: `sin cos sqrt pow round floor abs min max quadratic
solve_linear pick rand`. `@seed N` makes pick/rand reproducible.
Comments: `//` line, `/* */` block, `#` legacy (outside headers).

### Valid v5 superset constructs (from older versions, NOT deprecated)

v5 is a superset — these compile as v5 and do NOT demote the file (no
deprecation warning): polyrhythm `[C4 E4 G4](3:2)`, Euclidean `E(5,4)`,
v3 shorthand `C4 q` (note + duration). Files using them are v5 unless they
carry an explicit old-version marker (`Version: v4`, `// v4`, `#MACHINE`,
...) — those still warn and should be converted with
`run.py compile <file> --to v5`.

### Legacy syntax — HARD BAN in new files

The following compile (for old material) but must NEVER appear in files you
write: `T0 N60 D500 V80` machine lines, `N60`/`N60-72` v1 shorthand,
`CH0 3:2 C4|E4 e` shorthand polyrhythm, `ritard(2 bars)->100`, `!name` v3
macros, `?0.8` probability gates, `x4` repeat suffix, `chord(I)`/`chord(V7)`
roman numerals, `while` loops, `for $i = 0 to N step S` loops, `@curve bpm
from` v4 curves. ALWAYS write the v5 statement set above (play note/chord
with `@dur/@vel/@art`, pedal/rest, !fn, prog, perc, for-in loops, repeat,
print/assert, @seed/pick/rand, @curve vel ... over).

### Version detection & conversion

`detect_syntax_version` checks v5 markers first (`pedal on/off`, `rest`,
`t3(`, `@oct:`, `@art:`, `@tie`, `~` ties, `print/assert/include`, `prog(`,
`perc(`, `!fn`, `pick(/rand(`, `scale(/run(`, list/range loops,
break/continue), then v4/v3/v2/v1 markers, else defaults to v5. A
deprecation banner prints once per deprecated version.
`run.py compile <old.e> --to v5` converts (portbaby; the v5 target is
implemented as the v4-superset conversion).

---

## 4. Integrity & SAFE MODE (X / Y)

Every init runs the security sequence:

1. **Technique X first (local, offline)** — the committed
   `SECURITY_HASH.txt` manifest (SHA-512 per covered core file) has a
   160-byte **triple aggregate** (SHA-256 + SHA-512 + BLAKE2b-512). X hides
   that digest as tiny rotating random fragments under
   `.e_identity/.integrity/.store`; the **order file is auto-deleted after
   use** and a fresh random layout is embedded every init. Tamper with any
   covered file (or the fragments) → mismatch → SAFE MODE.
2. **Network probe** — offline: "X is the proof, skipping Y".
3. **Technique Y (online)** — a permanent per-version key
   (`blake2b512(aggregate + ":" + version tag)`, committed in
   `ep_compiler/_version_key.py`) is verified against the live
   `SECURITY_HASH.txt` at the version tag on GitHub; a newer version is
   offered as a safe update.

**SAFE MODE** (on failure): plugins are isolated, only a restricted shell
runs — `status` (what failed), `reinstall` (re-install the current version
from GitHub, preserving configs/plugins/mods/identity), `/safemode exit
force` (highly risky), `quit` (stay, safe).

Check integrity yourself: `run.py integrity [--github]`. After intentional
core changes, regenerate everything together with
`python3 tools/gen_security_hash.py` and commit the manifest + key + X;
`tools/verify_integrity.py` verifies locally.

## 5. Safe Updates

`ep_compiler/update.py::safe_update(tag)` — version = a GitHub version tag:

1. **Backup** user data (`.plugin_config.json`, `.env`, `.e_identity/`,
   `mods/`, `SECURITY_HASH.local`, custom plugin dirs) to `.backup_update/`.
2. K-rip **kernel registry snapshot** — current kernel becomes a bootable
   previous entry (rollback target).
3. `git fetch origin tag <tag>` → stash uncommitted work → `checkout -f`.
4. **Restore** user data; **register custom plugins in `SECURITY_HASH.local`**
   so the digest accepts them.
5. Restore stashed work; fresh X + Y embed + integrity re-check.

Nothing is lost — custom plugins, mods, configs and identity survive.
The krip menu offers this via `u`; booting a previous kernel entry rolls
back through the same path.

---

## 6. HellGate — You Are the OpenCode Agent Inside It

**HellGate** (`run.py hellgate` / `krip hellgate`) is a wrapper that boots
**OpenCode** directly, focused in this repo, with this knowledge pack fed
in. It is a wrapper — not an official product of OpenCode.

- **Per launch:** wrapper warning → first-run onboarding on a NEW machine
  (specs-based: summertime + legal agreements) → provider resolution →
  HellCode welcome + loading screen with a real `x/1024` counter →
  OpenCode TUI.
- **Provider registry** (first-available wins the default, **Ollama
  last**): Anthropic, OpenAI, OpenRouter, Google Gemini, custom, Ollama.
  Ollama asks for a model via a select list of every installed model
  (`/api/tags`). Keys: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
  `OPENROUTER_API_KEY`, `GEMINI_API_KEY`; `HELLGATE_MODEL` /
  `HELLGATE_OLLAMA_URL` override the ollama path.
- **Session commands** (after OpenCode exits): `Enter`/`$new` relaunch,
  `$agent [name]` (Music-Composer, Music-Refiner, or default), `$provider
  [name]`, `$model [name]`, `$dir [path]`, `$help`, `q`.
- **Knowledge pack** (`plugins/hellgate/knowledge/`): `full.md`
  (this file — comprehensive), `core.md` (distilled ~30% digest),
  `samples-index.md` (samples table), `agents.md` (personas — each
  `## <Name>` section is the agent's system prompt). At launch `current.md`
  is prepared: small-context models get the digest, larger ones the full
  map. `current.md` is generated — never edit it.
- **Confinement:** OpenCode runs with cwd = the project root; all state
  lands in `hellgate-state/` inside the repo. Stay in the project root;
  never touch `.e_identity/`, `.venv/`, `hellgate-state/`, `logs/`, `.git/`.

---

## 7. Core Commands

### `run.py` launcher (every mode re-enters through the krip sandbox)

| Command | Usage | What it does |
|---|---|---|
| `play` | `run.py play <file>` | Playback via `player.py` (compiles `.e` first; handles `.mid/.wav/.mp3/.mp4/.e/.ei/.eic/.enx/.ec`) |
| `compile` | `run.py compile <spec> -o <out>` | Compile to output (default `<input>.mid`); `<spec>` = file/dir/`/`/glob; flags `--human`, `--machine`, `--strict`, `--mem`, `--recursive`; **`--to v1..v5` = syntax conversion instead of MIDI export** |
| `check` | `run.py check <spec>` | Lint E files — **the authoritative gate**; `--recursive`, `--max <N>`; a pure v5 file reports at most the I001 info line |
| `stats` | `run.py stats <file>` | Notes, duration, note range, velocity, polyphony, density, channels |
| `tracks` | `run.py tracks <file>` | Per-channel table (+ per-track when `TRK[]` metadata present) |
| `inspect` | `run.py inspect <file> [N]` | Show first N events (default 12) |
| `new` | `run.py new <name> [-o <dir>]` | Scaffold a **v5 project**: `index.ei` + `parts/main.e` (pedal/rest/articulations) + `README.md` |
| `transpose` | `run.py transpose <file> <n> [-o out]` | Shift all notes by n semitones (clamped 0-127); default `<file>_transposed.mid` |
| `tempo` | `run.py tempo <file> <bpm> [-o out]` | Recompile at a new tempo; default `<file>_tempo.mid` |
| `merge` | `run.py merge <a> <b> [-o out]` | Concatenate two files; default `<a>_merged.mid` |
| `integrity` | `run.py integrity [--github]` | Verify core digest vs committed + GitHub copy |
| `ai` | `run.py ai status\|ask\|chat\|fix\|plugin ...` | Built-in copilot (see `plugins/llm`) |
| `hellgate` | `run.py hellgate` | HellGate → OpenCode wrapper |
| `krip` | `run.py krip [run \| eshell \| hellgate \| player \| status]` | The hypervisor entry — same as `krip` |

### `eshell.py` interactive shell

Built-in command map: `cd/ls/clear/exit`, `compile` (+`--human/--machine/
--volume`), `play`, `gui`, `run`, `shell`, `info` (alias `stats`), `stats`,
`tracks`, `inspect`, `new`, `transpose`, `tempo`, `merge`, `lint`,
`generate`, `convert` (import MIDI/audio → `.e`; `--project` full project),
`encrypt` (`.ee`), `ecc`, `sign`, `mod`/`plugin`/`pkglist`/`ezip`
(packages), `audio` (devices), `gc`, `sys`, plus plugin commands
(`krip`, `ai`, `launcher`, `learner`, ...). Aliases: `build`→compile,
`glass`→gui, `plugins`→plugin, `?`→help, `quit`→exit.

### Direct CLI: `ep.py`

`ep.py compile <file> -o <out> [--human|--machine|--strict]` — thin shim over
`ep_compiler.cli.main()`; re-exports `compile_source`, `compile_file`,
`detect_syntax_version`, event helpers, `export_midi/ec/eic`.

---

## 8. Plugins (14 drivers; each a package, entry `def register(api)`)

| Driver | One-line purpose |
|---|---|
| `krip/` | **The hypervisor** — boot manager, kernel registry, sandbox (mem/CPU/GPU/engine), safe updates |
| `hellgate/` | OpenCode wrapper — this pack + provider registry + personas |
| `llm/` | AI copilot — `ai ask/chat/fix/plugin/agent`, JSON-plan loop, intent routing, indexing, TUI |
| `eaudio/` | Low-level 3D spatial audio API (devices, PCM buffers, spatial/doppler, effects) |
| `humanize/` | Performance feel — MoE micro-timing + expressive velocity (`@humanize:nn`) |
| `launcher/` | New-window launching & process management (`launcher open/player/compile/...`) |
| `learner/` | Interactive CLI tutorial for E (`learner start/lesson/list/progress`) |
| `lure/` | LuaJIT compile accelerator (5–15× on the hot path; requires `lupa`) |
| `openapi/` | Low-level OpenGL graphics API (context/shader/buffer/... primitives) |
| `portbaby/` | Syntax conversion v1–v4 ↔ v5 — backs `run.py compile --to vN` |
| `radical/` | GPU shader math core (E math AST → GLSL compute shaders; multi-GPU) |
| `talisman/` | Audio culling/occlusion + privacy & QOL engine (local-only mode, auto-backup) |
| `tensorsharp/` | NVIDIA Tensor Core math (CuPy, TF32/FP16 mixed precision) |
| `vulkanizer/` | Low-level Vulkan graphics & compute API (instance/pipeline/ray-trace/...) |

Reference plugin: `examples/plugins/example_plugin.py` — `register(api)`,
`api.register_variable_handler`, `api.register_syntax` demo.

Plugin API essentials (see `docs/agent/plugins.md`): `add_command`,
`add_help_section`, `on(event, cb)` hooks (`pre_compile`, `post_compile`,
`pre_play`, `post_play`, `pre_render`, `post_render`, `on_load`, `on_unload`,
`on_exit`), `register_syntax`, `register_variable_handler`,
`register_directive`, `register_math_evaluator`, `register_gc`,
`register_encryptor`, `require(*pkgs)`, config + auth-token storage, theme,
`add_boot_step`. `post_compile` hooks feed forward (each sees the previous
hook's output; return None to leave events unchanged — e.g. Humanize →
Talisman layering). Mods (`mods/`) are security-scanned drop-ins with
`def init(api)` and restricted builtins.

---

## 9. Testing

No pytest. Every suite is `tests/<name>_test.py`, self-contained, run
directly:

```bash
.venv/bin/python tests/v5_statements_test.py   # one suite
.venv/bin/python tests/security_hash_test.py   # X/Y integrity
.venv/bin/python plugins/krip/tests/test_krip.py  # hypervisor
.venv/bin/python tests/run_all.py              # combined mega-run
```

- Each file defines its own `test(name, fn)` harness with `passed`/`failed`
  globals, registers tests at module scope, prints a summary, and calls
  `sys.exit(1)` on failures.
- Suites: `parse_test.py` (machine/human/version detect),
  `syntax_test.py` (strict diagnostics, lexicons), `v5_statements_test.py`
  (print/assert/include/!fn/prog/perc/loops/@seed+pick — **29 tests, the
  authoritative v5 statement set**), `piano_features_test.py`
  (pedal/rest/art/tuplets/octave/curve/ties), `paths_test.py`,
  `lint_test.py`, `cli_commands_test.py`, `async_test.py`, `launch_test.py`,
  `gpu_test.py`, `humanize_test.py`, `llm_plugin_test.py` (copilot
  protocol), `lsp_test.py`, `verify_signing.py`, `security_hash_test.py`
  (X/Y), `run_all.py` (combined) — plus `plugins/krip/tests/test_krip.py`
  (boot menu, kernel registry/rollback, sandbox lifecycle, krip.json,
  hypervisor entry).
- Rules: run relevant tests after **every** `.py` change; full suite green
  before declaring done; never commit red; a change that breaks a test is a
  bug in the change, never in the test; new features need ≥2 tests.
- Tests import from the repo root and exercise the real compiler
  (`ep_compiler.compile.compile_source`), not mocks.

---

## 10. Samples & Examples

- **`samples/v5-current/`** — canonical v5 (the ground truth for idiomatic
  v5): `pattern_demo.e` (the full v5 statement set — `!fn`, scale/range
  loops, `print`, `assert`, `prog`, `perc`, `@seed` + `pick`),
  `performance_demo.e` (the seven piano-performance features: pedal, rests,
  articulations, tuplets, octave shift, velocity curves, ties) +
  `README.md` cheat-sheet.
- **`songs/aurora_nocturne.e`** — a complete, polished v5 piano piece
  ("Aurora Nocturne", C major, 48 bars): `pedal`, `!fn` ornament macros,
  arpeggio loops, `@curve vel` swells, `@seed 7`, dynamic arcs pp→fff.
  Ideal reference for full-song structure.
- **`samples/v4-current/`** — v4-era examples (compile with deprecation
  warning): `basics/` (hello_world_v4, euclidean 5:8/3:4/7:12,
  rhythm_layers polyrhythm 3:2), `generative/` (probability `@prob`,
  tempo_curve `@curve bpm`, polyrhythm_complex multi-channel),
  `humanize/humanize_demo.e` (`@humanize:40`), `loops/` (for_step,
  nested_for, var_update_loop with `while`), `math/` (velocity_sin,
  modulo_arpeggio, quadratic_notes).
- **`samples/v3-supported/`** — v3 shorthand: `basics/` (channels CH0-2,
  first_note, note_durations, velocity_dynamics ppp-fff), `chords/`
  (arpeggio_v3, chord_progression), `loops/` (for_scale, repeat_pattern,
  while_counter), `math/` (functions, scale_calc, var_expr).
- **`samples/v1-deprecated/`, `samples/v2-deprecated/`** — legacy syntax:
  `machine/` (bare_minimum, dynamics, melody), `human/` (play_notes,
  play_chords), v2 `semantic_basics.e` / `semantic_song.e`.
- **`samples/ei/`, `samples/eic/`, `samples/enx/`** — project formats:
  `simple_project.ei` with `**inherit parts/*.e**`; `toggle_*.eic`
  (#MACHINE/#HUMAN toggling); `album.enx` with `**track tracks/song1.e**`.
- **`examples/`** — full compositions: `Rush_E.e` (reference piece, 19853
  events, 270 BPM, ~174s; `.ec` binary + `.mid/.wav/.mp3/.mp4`),
  `v3-compositions/` (chord_song_v3, melody_v3), `v4-compositions/`
  (cinematic_v4, lullaby_v4, techno_v4), `projects/suite.ei`
  (3-movement `.ei`), `albums/opus1.enx` (5-track), `audio/audio_dsp_demo.e`,
  `gpu/gpu_math_demo.e`, `eic/duality.eic` + `hybrid.eic`,
  `opengl_engine.py` (game-engine reference on OPENapi/Vulkanizer/EAudio),
  `plugins/example_plugin.py` (reference plugin).
- See `plugins/hellgate/knowledge/samples-index.md` for the full table.

---

## 11. Workflow Rules for Agents

1. **You run inside K-rip.** Everything is launched through the hypervisor
   sandbox. Stay in the project root; never touch `.e_identity/`, `.venv/`,
   `hellgate-state/`, `logs/`, `.git/`. Never modify `krip.json` or the
   kernel registry unless explicitly asked.
2. **Verify before claiming.** Never assert a file/feature exists without
   reading it; never invent syntax not in `SYNTAX.md`. Ground every claim
   about the language in `tests/v5_statements_test.py` + `docs/agent/`.
3. **Always write v5 syntax.** v1–v4 sources still compile but emit
   deprecation warnings; new/edited `.e` sources must use canonical v5.
   Legacy constructs (machine lines, `while`, `for $i = 0 to N step S`,
   `?0.8`, roman chords, `ritard`, `N60-72`, `@curve bpm from`) are
   **hard-banned** in new files. When asked to touch old files, convert
   them (`run.py compile <old.e> --to v5`).
4. **`run.py check` is authoritative.** A pure v5 file reports at most the
   I001 info line; any deprecation warning means the file is NOT v5 —
   rewrite it. Then confirm compilation: `run.py compile <file> -o
   <out.mid>`. For Python changes run the relevant test suite
   (`.venv/bin/python tests/<name>_test.py`), `tests/security_hash_test.py`,
   `plugins/krip/tests/test_krip.py`, and `tests/run_all.py` before
   finishing.
5. **Integrity is real.** Don't touch `SECURITY_HASH.txt`,
   `ep_compiler/_version_key.py`, or `.e_identity/` — altering covered
   files without regenerating the manifest triggers SAFE MODE. If you
   intentionally change core files, the manifest + key + X must be
   regenerated together (`tools/gen_security_hash.py`) and committed.
6. **Keep output inside the project root.** Write new `.e` sources and MIDI
   outputs under the repo root (e.g. `out/` or `run.py new <name>`); never
   touch protected dirs.
7. **Follow the edit-not-rewrite policy.** Existing files get precise
   line-range edits, never whole-file rewrites; deletions require explicit
   per-file confirmation; no destructive shell commands (`rm`, `mv`,
   `sudo`, `pip install`); relative paths only.
8. **Use samples/ and examples/ as reference.** For idiomatic v5, mirror
   `samples/v5-current/pattern_demo.e`, `performance_demo.e`, and
   `songs/aurora_nocturne.e`; `run.py new` scaffolds a canonical v5
   project structure.
9. **MIDI output via run.py compile.** `run.py compile <file> -o
   <file>.mid` is the supported path to produce MIDI; verify with
   `run.py stats` / `run.py inspect` / `run.py tracks` when reviewing a
   result.
10. **When in doubt about the language**, consult `docs/agent/language.md`
    (v5 reference), `docs/agent/compiler.md` (pipeline), and `SYNTAX.md`
    (human reference). If docs disagree with the tests, the tests win.

---

## Footer — Doc accuracy notes

- `docs/agent/*.md` are v5-aware and accurate as of this pack's writing:
  `language.md` is titled "Language Reference — v5 (canonical)" and its
  statement list matches `tests/v5_statements_test.py` (verified 29/29).
- The **verified ground truth for the v5 statement set is
  `tests/v5_statements_test.py`** (print, assert, include, !fn, prog, perc,
  list/range/scale/run loops + break/continue, repeat, @seed + pick/rand).
  Any doc line that contradicts the tests should be treated as stale.
- Legacy constructs (`T0 N60 D500 V80` machine lines, `?0.8` probability
  gates, `N60-72` ranges, `chord(I)` roman numerals, `while` loops,
  `for $i = 0 to N step S`, `ritard`, `@curve bpm from`) are NOT part of
  the v5 statement set — they belong to v1–v4 paths, compile with
  deprecation warnings, and are **hard-banned** in new files. Polyrhythm
  `[C4 E4 G4](3:2)`, Euclidean `E(5,4)`, and v3 shorthand `C4 q` ARE valid
  v5 superset constructs (no deprecation).
- OS/integrity facts (krip boot flow, X/Y, SAFE MODE, safe updates,
  hellgate launch) were verified by reading `plugins/krip/__init__.py`,
  `ep_compiler/security_hash.py`, `ep_compiler/safemode.py`,
  `ep_compiler/update.py`, `plugins/hellgate/*`, `run.py`, and the tests.
- Repo facts (commands, plugin names, sample paths) were verified by
  reading `run.py`, `eshell.py`, `ep.py`, plugin `__init__.py` docstrings,
  and the samples/examples tree in this repository.
