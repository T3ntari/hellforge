# HELLFORGE Knowledge Pack — Core Digest (v5)

Distilled key points for small-context agents. Full map: `full.md`;
samples table: `samples-index.md`; personas: `agents.md`.

## 1. What HELLFORGE Is
- **E** = DSL for piano music composition: plain text → `.mid/.wav/.mp3/
  .mp4/.ec/.eic`. Version **v0.1.14.41-beta**.
- Built like an OS: **kernel** = `ep_core.py`, **plugins = drivers** (14),
  **hypervisor = K-rip** (`krip os` shows the table).
- Python 3.10+; **always** `.venv/bin/python ...`, never bare `python`.
- Pipeline: `.e` source → `compile_source()` (`ep_compiler/compile.py`) →
  event dicts → export. Event dict contract:
  `{"timestamp", "midi", "duration", "velocity", "pan", "bend"}` (+
  optional channel/track/sustain/pedal/art/tie/octave/...).
- v5 writing = human-mode + statements: `play note(C4) @dur:q @vel:mf`,
  auto-detected, no headers. Machine lines compile only as legacy.
- Core dirs: `ep_compiler/`, `plugins/`, `tests/`, `samples/`, `songs/`,
  `examples/`, `docs/agent/`, `SYNTAX.md`.

## 2. You Run Inside K-rip
- Everything launches through the **hypervisor**: `krip` → GRUB-style menu
  (3s countdown, ↑/↓, Enter boot, `c` console, `u` update, Esc exit) →
  boot kernel → **eshell console**, inside the sandbox.
- Sandbox: mem budget (RLIMIT_AS), CPU affinity, GPU
  (`CUDA_VISIBLE_DEVICES`; auto|list|all|"0,1"), engine vulkan (default)/
  opengl, vulkanrt, tensor — config in **`krip.json`** (`krip edit` = nano,
  live reload).
- `krip run <cmd>` · `krip eshell` · `krip hellgate` · `krip player
  <file>` · `krip status` · `krip os` · `krip sandbox run/list/kill` ·
  `krip kernels` (current + previous — rollback via safe update).
- **Every `run.py` mode re-enters through krip** (`KRIP_INNER=1` no
  re-wrap; `KRIP_BYPASS=1` skip).
- **Stay in the project root; never touch `.e_identity/`, `.venv/`,
  `hellgate-state/`, `logs/`, `.git/`.**

## 3. v5 Syntax (verified against tests/v5_statements_test.py, 29/29)
- **v5 is canonical; v1–v4 compile but are deprecated (warnings).**
  Convert old files: `run.py compile <old.e> --to v5`.
- Statements (exact spellings): `print "hi"` / `print {2+3}` / `print N60`
  · `assert {2+2} == 4, "msg"` (compile fails when false) ·
  `include "hook.e"` (relative to source dir; cycles rejected) ·
  `!fn name(args) = ...` macros invoked `!name(a, b)` (literal, $var,
  {expr}, note-name args) · `prog(C:q G:q Am:h F:q)` chord progression ·
  `perc(kick|snare|hihat|...)` GM drums on channel 9 · `@seed N` +
  `pick(60 64 67)` / `rand(1, 4)` deterministic randomness.
- Loops (all with `break`/`continue`): `for $n in [C4 E4 G4]` (list) ·
  `for $i in 1..4` (inclusive) · `for $n in scale(C major, 4, 1)` ·
  `for $n in run(C4, E4)` (chromatic, inclusive) · `repeat 5 { }`.
  Unroll cap 100k.
- Piano performance: `pedal on/off` · `rest q` · `@art:staccato|legato|
  tenuto|accent` · `t3(C4 E4 G4)` tuplets · `@oct:+1` · `@curve vel 60 115`
  · ties `C4~ q q`.
- Directives: `@bpm 120`, `@key C major`, `@scale`, `@vol:`, `@master:`,
  `@gain:`, `@sr:`, `@bit:`, `@quality:`, `@seed 42`, `@strict on|off`.
- Math: `$x = 60`, `{$expr}` (`+ - * / // % ^`), functions
  `sin cos sqrt pow round floor abs min max quadratic solve_linear pick rand`.
- Durations `w h q e s t` (=4/2/1/½/¼/⅛ beats), velocity words
  `ppp pp p mp mf f ff fff`; comments `//`, `/* */`, `#`.
- **Valid v5 superset (use freely, no deprecation):** polyrhythm
  `[C4 E4 G4](3:2)`, Euclidean `E(5,4)`, v3 shorthand `C4 q`.
- **Legacy HARD BANS (never write):** machine lines `T0 N60 D500 V80`,
  `N60`/`N60-72`, `CH0 3:2 C4|E4 e`, `ritard(...)`, `!name` macros,
  `?0.8`, `x4`, `chord(I)` roman numerals, `while`, `for $i = 0 to N step
  S`, `@curve bpm from`.
- Never invent syntax not in SYNTAX.md. If docs conflict with the tests,
  tests win.

## 4. Integrity & SAFE MODE (X / Y)
- `SECURITY_HASH.txt`: committed manifest (SHA-512 per file) + 160-byte
  triple aggregate (SHA-256 + SHA-512 + BLAKE2b-512).
- **X** (offline): digest hidden as rotating random fragments in
  `.e_identity/.integrity`; order file auto-deleted after use,
  re-randomized every init. Tamper → SAFE MODE.
- **Y** (online): per-version key in `ep_compiler/_version_key.py`
  (blake2b512(aggregate + ":" + tag)) verified vs GitHub at the version
  tag. Boot order: **X → network → Y/version-sync**; offline X suffices.
- SAFE MODE: `status` | `reinstall` (preserves everything) | `/safemode
  exit force` (risky) | `quit`.
- `run.py integrity [--github]`; after intentional core changes run
  `tools/gen_security_hash.py` and commit manifest + key + X together.

## 5. Safe Updates
- `ep_compiler/update.py::safe_update(tag)`: backup (configs, `.e_identity/`,
  mods, `SECURITY_HASH.local`, custom plugins) → kernel registry snapshot →
  fetch/checkout tag → restore + register custom plugins in
  `SECURITY_HASH.local` → fresh X/Y. **Nothing is lost.** Boot menu `u`
  updates; booting a previous kernel rolls back safely.

## 6. HellGate
- `run.py hellgate` / `krip hellgate` boots **OpenCode** in this repo
  (wrapper, not official). Wrapper warning every launch; first-run
  onboarding (specs-based); HellCode welcome + `x/1024` loading.
- Providers (first-available wins, **Ollama last**): Anthropic, OpenAI,
  OpenRouter, Google Gemini, custom, Ollama (model select from `/api/tags`).
- Session: `Enter`/`$new` relaunch · `$agent` (Music-Composer /
  Music-Refiner) · `$provider` · `$model` · `$dir` · `q`.
- Knowledge: `full.md` (comprehensive), `core.md` (this digest — served to
  small contexts), `samples-index.md`, `agents.md` (personas, parsed by
  `## <Name>` headings). `current.md` is generated — never edit it.
- State lives in `hellgate-state/` inside the repo — never touch it.

## 7. Core Commands (`run.py`; eshell has the same built-ins)
- `play <file>` · `compile <spec> -o out.mid` (`--to vN` = convert syntax,
  `--strict`, `--mem`, `--human/--machine`) · `check <spec>` (lint —
  **authoritative**: pure v5 → at most I001) · `stats <file>` ·
  `tracks <file>` · `inspect <file> [N]` · `new <name>` (v5 project
  scaffold) · `transpose <file> <n>` · `tempo <file> <bpm>` ·
  `merge <a> <b>` · `integrity [--github]` · `shell` (eshell) ·
  `ai ...` (copilot) · `hellgate`.
- Direct CLI: `ep.py compile`. eshell also has `convert` (MIDI→E import),
  `encrypt`, `sign`, `gc`, `audio`, plus plugin commands (`krip`, `ai`, ...).

## 8. Plugins (14 drivers; each: package with `def register(api)`)
- `krip/` — hypervisor: boot manager, kernel registry, sandbox, safe updates.
- `hellgate/` — OpenCode wrapper (this pack, provider registry, personas).
- `llm/` — AI copilot (`ai ask/chat/fix/plugin/agent`), JSON-plan loop,
  intent routing, indexing, TUI.
- `eaudio/` — 3D spatial audio API. `humanize/` — `@humanize:nn` MoE
  micro-timing/velocity feel. `launcher/` — window/process mgmt.
- `learner/` — tutorial. `lure/` — LuaJIT compile accelerator (5-15×).
- `openapi/` — OpenGL API. `vulkanizer/` — Vulkan API.
- `portbaby/` — syntax conversion (backs `--to vN`). `radical/` — GPU
  shader math. `talisman/` — audio culling + privacy.
- `tensorsharp/` — Tensor Core math.
- Reference plugin: `examples/plugins/example_plugin.py`.
- Plugin API: `add_command`, `add_help_section`, `add_boot_step`,
  `api.on("post_compile", cb)` (feed-forward, return None = unchanged),
  `register_syntax`, `register_directive`, `register_math_evaluator`,
  `register_gc`, `require(pkgs)`. Mods (`mods/`) are AST-scanned drop-ins.

## 9. Testing
- No pytest. Run: `.venv/bin/python tests/<name>_test.py`, or
  `.venv/bin/python tests/run_all.py` (combined run); plus
  `tests/security_hash_test.py` (X/Y) and
  `plugins/krip/tests/test_krip.py` (hypervisor).
- Harness: per-file `test(name, fn)`, passed/failed counters,
  `sys.exit(1)` on failure.
- Suites: parse, syntax, **v5_statements (29 tests — authoritative)**,
  piano_features, paths, lint, cli_commands, async, launch, gpu,
  humanize, llm_plugin, lsp, verify_signing, security_hash (+ run_all).
- Run relevant tests after every `.py` change; suite green before done;
  never commit red; new features need ≥2 tests.

## 10. Samples & Examples
- `samples/v5-current/` — canonical v5: `pattern_demo.e` (statements:
  !fn, loops, print, assert, prog, perc, @seed+pick), `performance_demo.e`
  (pedal, rests, articulations, tuplets, octave, curve, ties).
- `songs/aurora_nocturne.e` — complete v5 piano piece (48 bars, C major):
  pedal, !fn ornaments, loops, `@curve vel`, `@seed`, dynamics pp→fff.
- `samples/v4-current/` — euclidean, polyrhythms, `@prob`, `@curve bpm`,
  `@humanize:40`, loops/math (deprecated). `samples/v3-supported/` —
  shorthand, channels, loops, math. `v1/v2-deprecated/` — legacy.
- `samples/ei/ eic/ enx/` — project formats (inherit parts, mode toggles,
  album tracks).
- `examples/` — `Rush_E.e` (19853 events, 270 BPM; + `.ec` binary),
  `v3-compositions/`, `v4-compositions/`, `projects/suite.ei`,
  `albums/opus1.enx`, `audio/`, `gpu/`, `eic/`, `opengl_engine.py`,
  `plugins/example_plugin.py`.
- Full table with per-file detail: `samples-index.md`.

## 11. Workflow for Agents
- You run **inside K-rip**: stay in the project root; never touch
  `.e_identity/`, `.venv/`, `hellgate-state/`, `logs/`, `.git/`.
- Verify before claiming — read files; ground syntax in the v5 tests +
  docs; never invent syntax not in SYNTAX.md.
- Always write v5; old files → `run.py compile --to v5`; legacy
  constructs are hard-banned.
- **`run.py check` is authoritative** (pure v5 → at most I001) + confirm
  with `run.py compile <file> -o out.mid`; Python changes → relevant
  tests, then `tests/run_all.py` + security/krip suites.
- Don't touch `SECURITY_HASH.txt` / `_version_key.py` / `.e_identity/`
  without regenerating the manifest (SAFE MODE trigger).
- Keep all output inside the project root; avoid protected dirs.
- Edit-not-rewrite: line-range edits only; no deletions without
  confirmation; no `rm/mv/sudo/pip install`; relative paths only.
- Mirror `samples/v5-current/` + `songs/aurora_nocturne.e` for idiomatic
  v5; scaffold with `run.py new <name>`; MIDI via `run.py compile`.
