# HELLFORGE Knowledge Pack — Core Digest (v5)

Distilled key points for small-context agents. Full map: `full.md`;
samples table: `samples-index.md`; personas: `agents.md`.

## 1. What HELLFORGE Is
- **E** = DSL for piano music composition: plain text → `.mid/.wav/.mp3/
  .mp4/.ec/.eic`.
- Python 3.10+; **always** `.venv/bin/python ...`, never bare `python`.
- Pipeline: `.e` source → `compile_source()` (`ep_compiler/compile.py`) →
  event dicts → export. Event dict contract:
  `{"timestamp", "midi", "duration", "velocity", "pan", "bend"}` (+
  optional channel/track/sustain/pedal/art/tie/octave/...).
- Two modes, no headers, auto-detected & mixable:
  Machine `T0 N60 D500 V80` (absolute ms) · Human
  `play note(C4) @dur:q @vel:mf` (relative cursor).
- Core dirs: `ep_compiler/` (compiler), `plugins/`, `tests/`, `samples/`,
  `examples/`, `docs/agent/`, `SYNTAX.md`.

## 2. v5 Syntax (verified against tests/v5_statements_test.py, 29/29)
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
- Never invent syntax not in SYNTAX.md. If docs conflict with the tests,
  tests win.

## 3. Core Commands (`run.py`; eshell has the same built-ins)
- `play <file>` · `compile <spec> -o out.mid` (`--to vN` = convert syntax,
  `--strict`, `--mem`, `--human/--machine`) · `check <spec>` (lint) ·
  `stats <file>` · `tracks <file>` · `inspect <file> [N]` ·
  `new <name>` (v5 project scaffold: index.ei + parts/main.e) ·
  `transpose <file> <n>` · `tempo <file> <bpm>` · `merge <a> <b>` ·
  `shell` (eshell) · `ai ...` (copilot) · `hellgate [tool]`.
- Direct CLI: `ep.py compile`. eshell also has `convert` (MIDI→E import),
  `encrypt`, `sign`, `gc`, `audio`.

## 4. Plugins (each: package with `def register(api)`)
- `llm/` — AI copilot (`ai fix/agent/chat/read/plugin`), JSON-plan loop,
  providers openai/deepseek/claude/ollama, TUI + REPL.
- `portbaby/` — syntax version conversion (backs `--to vN`).
- `humanize/` — `@humanize:nn` MoE micro-timing/velocity feel.
- `radical/` — GPU shader math (GLSL compute).
- `tensorsharp/` — NVIDIA Tensor Core math (CuPy).
- `lure/` — LuaJIT compile accelerator (5-15×).
- `eaudio/` — 3D spatial audio API (buffers/spatial/effects).
- `openapi/`, `vulkanizer/` — low-level OpenGL / Vulkan APIs.
- `radical/` — GPU shader math core; `talisman/` — audio culling;
  DSP...). `talisman/` — audio culling + privacy.
- `launcher/` — window/process mgmt. `learner/` — tutorial.
  `hellgate/` — this pack (launches the agent TUIs).
- `example_plugin.py` — reference plugin (variable-handler + syntax hooks).
- Plugin API: `add_command`, `api.on("post_compile", cb)` (feed-forward,
  return None = unchanged), `register_syntax`, `register_directive`,
  `register_math_evaluator`, `register_gc`, `require(pkgs)`.

## 5. Testing
- No pytest. Run: `.venv/bin/python tests/<name>_test.py`, or
  `.venv/bin/python tests/run_all.py` (combined run).
- Harness: per-file `test(name, fn)`, passed/failed counters,
  `sys.exit(1)` on failure.
- ~13 suites: parse, syntax, **v5_statements (29 tests)**, piano_features,
  paths, lint, cli_commands, async, launch, gpu, humanize, llm_plugin,
  lsp (+ verify_signing.py).
- Run relevant tests after every `.py` change; suite green before done;
  never commit red; new features need ≥2 tests.

## 6. Samples & Examples
- `samples/v5-current/` — canonical v5: `pattern_demo.e` (statements:
  !fn, loops, print, assert, prog, perc, @seed+pick), `performance_demo.e`
  (pedal, rests, articulations, tuplets, octave, curve, ties).
- `samples/v4-current/` — euclidean rhythms, polyrhythms, `@prob`,
  `@curve bpm`, `@humanize:40`, loops/math demos.
- `samples/v3-supported/` — shorthand, channels, dynamics words, loops,
  math. `samples/v1-deprecated/` + `v2-deprecated/` — legacy syntax.
- `samples/ei/ eic/ enx/` — project formats (inherit parts, mode toggles,
  album tracks).
- `examples/` — full pieces: `Rush_E.e` (19853 events, 270 BPM; also
  `Rush_E.ec` binary), `v3-compositions/`, `v4-compositions/`
  (cinematic/lullaby/techno), `projects/suite.ei` (3-movement),
  `albums/opus1.enx`, `audio/`, `gpu/`, `eic/hybrid.eic`,
  `opengl_engine.py`.
- Full table with per-file detail: `samples-index.md`.

## 7. Workflow for Agents
- Verify before claiming — read files; ground syntax in the v5 tests +
  docs; never invent syntax not in SYNTAX.md.
- Always write v5; old files → `run.py compile --to v5`.
- Before done: `run.py check <file>` + `run.py compile <file> -o out.mid`;
  Python changes → run relevant tests, then `tests/run_all.py`.
- Keep all output inside the project root; avoid protected dirs
  (`.identity/`, `.venv/`, `.fent_cache/`, `logs/`, `.git/`).
- Edit-not-rewrite: line-range edits only; no deletions without
  confirmation; no `rm/mv/sudo/pip install`; relative paths only.
- Mirror `samples/v5-current/` for idiomatic v5; scaffold with
  `run.py new <name>`; MIDI output via `run.py compile`.
