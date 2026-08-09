# HELLFORGE Knowledge Pack — Full Map (v5-accurate)

Comprehensive, code-verified knowledge digest for external agent TUIs
(OpenCode, Aider, OpenHands, Goose) working in the HELLFORGE (E) piano-music
DSL repo. Source-of-truth checks: `tests/v5_statements_test.py`,
`docs/agent/*.md`, `SYNTAX.md`, `run.py`, and the samples/examples tree.

---

## 1. What HELLFORGE Is

**HELLFORGE (E)** is a domain-specific language for piano music composition.
You write music as plain text — notes, chords, rhythms, dynamics — and E
compiles it to `.mid`, `.wav`, `.mp3`, `.mp4`, `.ec` (compiled binary),
`.eic` (one-file bundle), and more. No piano or programming experience is
required.

- **Runtime:** Python 3.10+ (dev/tested on 3.11). Always run Python through
  the project venv — `.venv/bin/python ...`, never bare `python`.
- **Compiler pipeline:** `.e` source text → `compile_source()` in
  `ep_compiler/compile.py` → a list of **event dicts** → export. The event
  dict is the single contract every parser produces:
  `{"timestamp" (int ms), "midi" (0-127), "duration" (ms), "velocity" (0-127),
  "pan" (-1..1), "bend" (-64..64)}` plus optional keys (`channel`, `track`,
  `sustain`, `pedal`, `art`, `tie`, `octave`, `master_vol`, `gain_db`,
  `filter_*`, `env_*`, `phase`, `cents`, `swing`, `strum`).
- **Two writing modes, no header needed** (v5 auto-detects and mixes):
  - Machine (absolute timestamps): `T0 N60 D500 V80`
  - Human (relative cursor): `play note(C4) @dur:q @vel:mf`
- **Project layout:** `ep_compiler/` (compiler core), `plugins/` (plugin
  ecosystem), `tests/` (self-contained test harnesses, no pytest),
  `samples/` (example `.e` sources organized by syntax version),
  `examples/` (full compositions, projects, albums, demos),
  `docs/agent/` (model-consumable docs), `SYNTAX.md` (full reference),
  `AGENTS.md`/`RULES.md` (agent rules).
- **Key entry points:** `ep.py compile|play`, `run.py compile|check`,
  `eshell.py` (interactive shell), `player.py` (playback),
  `ai.py` (built-in copilot → `plugins/llm/`).

---

## 2. v5 Canonical Syntax — The Statement Set

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
| `perc` | `perc(kick)`, `perc(snare)`, `perc(hihat)` | GM percussion on **channel 9** (kick=36, snare=38, hihat=42); unknown drum names are rejected (`unknown drum`) |
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

### Base line syntax every v5 file also uses

- Machine: `T<ms> N<midi|name> D<ms> V<0-127|0.0-1.0|word>` — e.g.
  `T0 N60 D500 V80`; word forms `N C4`, `D q`, `V mf`; optional
  `CH[n]`/`CHn` channel, `TRK[name]` track meta, `P[bend:-12]`,
  `S[pan:0.5]` `S[art:staccato]`, `F[c:200hz] F[r:0.8] F[t:lowpass]`,
  `E[a:5ms] E[r:100ms] E[s:0.7]`. Durations `w h q e s t` = 4/2/1/½/¼/⅛
  beats; missing D → 500ms.
- Human: `play note(C4) @dur:q @vel:mf`, `play chord(C, major) @dur:h
  @vel:ff`; quality table `major minor dim aug dom7 maj7 min7 dim7 sus2 sus4
  m m7 7 maj min`; extra props `@pan:`, `@bend:`, `@ch:`, `@track:`,
  `@time:`, `@sustain:`, `@art:`, `@oct:`, `@tie`, `@strum:`; dotted
  durations `q.`.
- Piano-performance layer (v5 = v4 + these): `pedal on` / `pedal off` /
  `@pedal:<0-127>` (CC64 sustain), `rest q` / `rest 500ms` / `R 500ms`
  (silence advancing the cursor), `@art:staccato|legato|tenuto|accent`,
  tuplets `t3(C4 E4 G4)`, `trip(...)`, `tup(5,1,...)`, `[C4 D4 E4]/3`,
  `@oct:+1`, `@curve vel 60 115` (`over 4q` windowed), ties `C4~ q q` /
  `@tie` (merged durations).
- Directives (`@`-prefixed): `@bpm 120` (also `@tempo`, Italian aliases
  `@allegro @adagio ...`), `@key C major`, `@scale A_minor` (quantize; `off`
  disables), `@vol:0.7`, `@master:0.7`, `@gain:-3db`, `@sr:44100`,
  `@bit:16`, `@quality:standard`, `@sub:40hz`, `@bass_boost:3db`,
  `@stereo_width:120`, `@neural on`, `@mem:64k` (event budget warn+truncate),
  `@seed 42`, `@gc:aggressive`, `@oct:+1`, `@pedal:64`, `@sustain:64`,
  `@strict on|off`.
- Math/variables: `$x = 60`, `$x = {$bpm * 2}` `{expr}` substitution
  (`+ - * / // % ^ ( )`), `@dur:{$d * 0.5}ms` inline expressions. Known
  functions: `sin cos sqrt pow round floor abs min max quadratic
  solve_linear pick rand`.
- Comments: `//` line, `/* */` block, `#` legacy (outside headers).

### Legacy syntax — HARD BAN in new files

The following DO compile (for old material) but must NEVER appear in files
you write: `T0 N60 D500 V80` machine lines, `N60`/`N60-72` v1 shorthand,
`[C4 E4 G4](5:4)` / `CH0 3:2 C4|E4 e` polyrhythms, Euclidean `E(5,4)`,
`ritard(2 bars)->100`, v3 shorthand `C4 q`, `!name` v3 macros, `?0.8`
probability gates, `x4` repeat suffix, `chord(I)`/`chord(V7)` roman
numerals, `while` loops, `for $i = 0 to N step S` loops, `@curve bpm from`
v4 curves. They are deprecated paths — writing them makes a file v1–v4 and
it compiles with deprecation warnings. ALWAYS write the v5 statement set
above (play note/chord with `@dur/@vel/@art`, pedal/rest, !fn, prog, perc,
for-in loops, repeat, print/assert, @seed/pick/rand, @curve vel ... over).

### Version detection & conversion

`detect_syntax_version` checks v5 markers first (`pedal on/off`, `rest`,
`t3(`, `@oct:`, `@art:`, `@tie`, `~` ties, `print/assert/include`, `prog(`,
`perc(`, `!fn`, `pick(/rand(`, `scale(/run(`, list/range loops,
break/continue), then v4/v3/v2/v1 markers, else defaults to v5. A
deprecation banner prints once per deprecated version.
`run.py compile <old.e> --to v5` converts (portbaby; the v5 target is
implemented as the v4-superset conversion).

---

## 3. Core Commands

### `run.py` launcher (subprocesses; `--window`/`--detach`/`--gui` flags)

| Command | Usage | What it does |
|---|---|---|
| `play` | `run.py play <file>` | Playback via `player.py` (compiles `.e` first; handles `.mid/.wav/.mp3/.mp4/.e/.ei/.eic/.enx/.ec`) |
| `compile` | `run.py compile <spec> -o <out>` | Compile to output (default `<input>.mid`); `<spec>` = file/dir/`/`/glob; flags `--human`, `--machine`, `--strict`, `--mem`, `--recursive`; **`--to v1..v5` = syntax conversion instead of MIDI export** |
| `check` | `run.py check <spec>` | Lint E files (static analysis, error/warning codes, catalog stats); `--recursive`, `--max <N>` |
| `shell` | `run.py shell` | Launch `eshell.py` in a new window |
| `stats` | `run.py stats <file>` | Notes, duration, note range, velocity, polyphony, density, channels |
| `tracks` | `run.py tracks <file>` | Per-channel table (+ per-track when `TRK[]` metadata present) |
| `inspect` | `run.py inspect <file> [N]` | Show first N events (default 12) |
| `new` | `run.py new <name> [-o <dir>]` | Scaffold a **v5 project**: `index.ei` (project/composer/tempo/`@title`/`include ... as main`/`section "Main" { play main }`) + `parts/main.e` (v5 part: `pedal on/off`, `play note(...) @art:staccato`, `rest e`, `play chord(...) @art:tenuto`) + `README.md` |
| `transpose` | `run.py transpose <file> <n> [-o out]` | Shift all notes by n semitones (clamped 0-127); default `<file>_transposed.mid` |
| `tempo` | `run.py tempo <file> <bpm> [-o out]` | Recompile at a new tempo; default `<file>_tempo.mid` |
| `merge` | `run.py merge <a> <b> [-o out]` | Concatenate two files; default `<a>_merged.mid` |
| `ai` | `run.py ai status\|ask\|chat\|fix ...` | Built-in copilot (see `plugins/llm`) |
| `hellgate` | `run.py hellgate [tool]` | The hellgate plugin picker/launcher for the agent TUIs |

### `eshell.py` interactive shell

Built-in command map: `cd/ls/clear/exit`, `compile` (+`--human/--machine/
--volume`), `play`, `gui`, `run`, `shell`, `info` (alias `stats`), `stats`,
`tracks`, `inspect`, `new`, `transpose`, `tempo`, `merge`, `lint`,
`generate`, `convert` (import MIDI/audio → `.e`; `--project` full project),
`encrypt` (`.ee`, AES-256-GCM), `ecc`, `sign`, `mod`/`plugin`/`pkglist`/
`ezip` (packages), `audio` (devices), `gc`, `sys`, plus plugin commands.
Aliases: `build`→compile, `glass`→gui, `plugins`→plugin, `?`→help,
`quit`→exit.

### Direct CLI: `ep.py`

`ep.py compile <file> -o <out> [--human|--machine|--strict]` — thin shim over
`ep_compiler.cli.main()`; re-exports `compile_source`, `compile_file`,
`detect_syntax_version`, event helpers, `export_midi/ec/eic`.

---

## 4. Plugins (`plugins/`, each a package; entry `def register(api)`)

- **llm/** — the AI copilot plugin: `ai fix/agent/chat/ask/read/plugin/...`
  commands, JSON-plan agentic loop (plan → review → apply → verify),
  OpenAI-compatible providers (openai/deepseek/claude/ollama), project
  indexing (keyword + optional Ollama embeddings), sessions, TODO.md
  management, full-screen curses TUI with a line-REPL fallback.
- **portbaby/** — syntax version porting/conversion between v1 machine,
  v1 human, v2, v3, v4 (and the v5 target); reports loss percentage; can
  generate multi-file project structure. Backs `run.py compile --to vN`.
- **tensorsharp/** — NVIDIA Tensor Core acceleration for E math (CuPy, TF32/
  FP16 mixed precision); math evaluator priority 3; graceful fallback chain
  Tensorsharp → Radical → LURE → Python.
- **humanize/** — de-robots MIDI with a tiny numpy Mixture-of-Experts model
  (~50k params, 8 experts): `@humanize:nn` directive adds human micro-timing
  and expressive velocity (strength 0-100, default 15); post_compile hook;
  trained on synthetic human-performance regression, cached to `.fent_cache`.
- **launcher/** — new-window launching & process management
  (`launcher open|player|compile|shell|log|ps|kill`).
- **learner/** — interactive CLI tutorial for the E language
  (`learner start|lesson <N>|list|progress|reset`), executes code via the E
  compiler.
- **eaudio/** — low-level 3D spatial audio API: devices, PCM buffers/ring
  buffers, spatial positioning/velocity/doppler/attenuation, effects
  (reverb/EQ/compressor/delay/convolution). Building block for audio engines.
- **fentclient/** — performance accelerator + bug fixes + enhanced syntax:
  FluidSynth, arpeggiator, music theory, DSP, MIDI recording, compilation
  cache, playback culling, AI composer modules (fixer/directives/commands/
  cache/security/engine/...).
- **openapi/** — low-level OpenGL graphics API (context/shader/buffer/
  texture/render/window primitives); building block for game engines;
  reference engine in `examples/opengl_engine.py`.
- **radical/** — GPU shader math core: compiles E math ASTs to GLSL compute
  shaders, executed on GPU; math evaluator priority 5; multi-GPU switching,
  VRAM limits; graceful fallback.
- **talisman/** — audio culling/occlusion, privacy & QOL engine: local-only
  mode, auto-backup, device-ID rotation, event inspection, compile stats.
- **vulkanizer/** — low-level Vulkan graphics & compute API (instance/
  pipeline/buffer/command/ray-trace/upscale primitives); building block for
  game engines.
- **lure/** — LuaJIT runtime accelerator for E: fast string parsing + bulk
  event math on the compile hot path (5-15× speedup); async engine;
  graceful Python fallback; requires `lupa`.
- **hellgate/** — this knowledge pack: launches OpenCode/Aider/OpenHands/
  Goose TUIs focused inside the project root, feeding them
  `knowledge/full.md` + `knowledge/samples-index.md` and the personas from
  `knowledge/agents.md`.
- **example_plugin.py** — single-file reference plugin: `register(api)`,
  `api.register_variable_handler`, `api.register_syntax` ($repeat_n variable
  handler + `@shuffle` syntax demo).

Plugin API essentials (see `docs/agent/plugins.md`): `add_command`,
`add_help_section`, `on(event, cb)` hooks (`pre_compile`, `post_compile`,
`pre_play`, `post_play`, `pre_render`, `post_render`, `on_load`, `on_unload`,
`on_exit`), `register_syntax`, `register_variable_handler`,
`register_directive`, `register_math_evaluator`, `register_gc`,
`register_encryptor`, `require(*pkgs)`, config + auth-token storage, theme.
`post_compile` hooks feed forward (each sees the previous hook's output;
return None to leave events unchanged — e.g. Humanize → Talisman layering).
Mods (`mods/`) are security-scanned drop-ins with `def init(api)` and
restricted builtins.

---

## 5. Testing

No pytest. Every suite is `tests/<name>_test.py`, self-contained, run
directly:

```bash
.venv/bin/python tests/v5_statements_test.py   # one suite
.venv/bin/python tests/run_all.py              # combined mega-run
```

- Each file defines its own `test(name, fn)` harness with `passed`/`failed`
  globals, registers tests at module scope, prints a summary, and calls
  `sys.exit(1)` on failures.
- Suites: `parse_test.py` (machine/human/version detect),
  `syntax_test.py` (strict diagnostics, lexicons), `v5_statements_test.py`
  (print/assert/include/!fn/prog/perc/loops/@seed+pick — **29 tests**),
  `piano_features_test.py` (pedal/rest/art/tuplets/octave/curve/ties),
  `paths_test.py`, `lint_test.py`, `cli_commands_test.py`, `async_test.py`,
  `launch_test.py`, `gpu_test.py`, `humanize_test.py`,
  `llm_plugin_test.py` (copilot protocol), `lsp_test.py`,
  `verify_signing.py` — plus `run_all.py` for the combined run.
- Rules: run relevant tests after **every** `.py` change; full suite green
  before declaring done; never commit red; a change that breaks a test is a
  bug in the change, never in the test; new features need ≥2 tests.
- Tests import from the repo root and exercise the real compiler
  (`ep_compiler.compile.compile_source`), not mocks.

---

## 6. Samples & Examples

- **`samples/v5-current/`** — canonical v5 examples (the ground truth for
  idiomatic v5): `pattern_demo.e` exercises the full v5 statement set
  (`!fn`, scale/range loops, `print`, `assert`, `prog`, `perc`, `@seed` +
  `pick`); `performance_demo.e` exercises the seven piano-performance
  features (pedal, rests, articulations, tuplets, octave shift, velocity
  curves, ties) plus audio directives (`@sr`, `@bit`, `@quality`, `@vol`,
  `@curve vel 60 115`).
- **`samples/v4-current/`** — v4-era examples (still compile with
  deprecation warning): `basics/` (hello_world_v4, euclidean 5:8/3:4/7:12,
  rhythm_layers polyrhythm 3:2), `generative/` (probability `@prob`,
  tempo_curve `@curve bpm`, polyrhythm_complex multi-channel 3:2+4:3),
  `humanize/humanize_demo.e` (`@humanize:40`), `loops/` (for_step,
  nested_for, var_update_loop with `while`), `math/` (velocity_sin,
  modulo_arpeggio, quadratic_notes).
- **`samples/v3-supported/`** — v3 shorthand: `basics/` (channels CH0-2,
  first_note, note_durations, velocity_dynamics ppp-fff), `chords/`
  (arpeggio_v3 `@mode:arpeggio`, chord_progression), `loops/` (for_scale,
  repeat_pattern, while_counter), `math/` (functions, scale_calc, var_expr).
- **`samples/v1-deprecated/`, `samples/v2-deprecated/`** — legacy syntax:
  `machine/` (bare_minimum, dynamics V0-127, melody C major scale),
  `human/` (play_notes, play_chords), v2 `semantic_basics.e` /
  `semantic_song.e` (`[Section:]`, `Key:`, `arpeggio()`, `chromatic_run()`).
- **`samples/ei/`, `samples/eic/`, `samples/enx/`** — project formats:
  `simple_project.ei` with `**inherit parts/*.e**` parts (intro/verse);
  `toggle_*.eic` (#MACHINE/#HUMAN mode toggling); `album.enx` with
  `**track tracks/song1.e**` listing.
- **`examples/`** — full compositions: `Rush_E.e` reference piece (19853
  events, 270 BPM, ~174s; compiled binary `Rush_E.ec`, plus `.mid/.wav/.mp3/
  .mp4` and a `Rush_E.human` variant); `v3-compositions/` (chord_song_v3,
  melody_v3); `v4-compositions/` (cinematic_v4 "The Approaching Storm" with
  tempo curves + dynamic arcs, lullaby_v4, techno_v4 with Euclidean kick
  patterns); `projects/suite.ei` (3-movement `.ei` inheritance);
  `albums/opus1.enx` (5-track album); `audio/audio_dsp_demo.e` (reverb/
  delay DSP); `gpu/gpu_math_demo.e` (GPU math in loops); `eic/hybrid.eic`
  (machine+human hybrid); `opengl_engine.py` (game-engine reference built
  on the OPENapi/Vulkanizer/EAudio plugins).
- See `plugins/hellgate/knowledge/samples-index.md` for the full table.

---

## 7. Workflow Guidance for Agents

1. **Verify before claiming.** Never assert a file/feature exists without
   reading it; never invent syntax not in `SYNTAX.md`. Ground every claim
   about the language in `tests/v5_statements_test.py` + `docs/agent/`.
2. **Always write v5 syntax.** v1–v4 sources still compile but emit
   deprecation warnings; new/edited `.e` sources must use canonical v5.
   When asked to touch old files, prefer converting them
   (`run.py compile <old.e> --to v5`) or keeping changes v5-compatible.
3. **Use `run.py check` before claiming done.** Lint the file with
   `run.py check <file>`; make sure it compiles via `run.py compile <file>
   -o <out.mid>`. For Python changes run the relevant test suite
   (`.venv/bin/python tests/<name>_test.py`) and the combined
   `tests/run_all.py` before finishing.
4. **Keep output inside the project root.** Write new `.e` sources and MIDI
   outputs under the repo root (e.g. an `out/` or project dir created with
   `run.py new <name>`); never touch protected dirs (`.e_identity/`,
   `.venv/`, `.fent_cache/`, `logs/`, `.git/`).
5. **Follow the edit-not-rewrite policy.** Existing files get precise
   line-range edits, never whole-file rewrites; deletions require explicit
   per-file confirmation; no destructive shell commands (`rm`, `mv`,
   `sudo`, `pip install`); relative paths only.
6. **Use samples/ and examples/ as reference.** For idiomatic v5, mirror
   `samples/v5-current/pattern_demo.e` and `performance_demo.e`; `run.py new`
   scaffolds a canonical v5 project structure.
7. **MIDI output via run.py compile.** `run.py compile <file> -o <file>.mid`
   is the supported path to produce MIDI; verify with `run.py stats` /
   `run.py inspect` / `run.py tracks` when reviewing a result.
8. **When in doubt about the language**, consult `docs/agent/language.md`
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
- A few constructs listed in `language.md` as v5-valid carry-overs
  (Euclidean `E(N,M)`, `?0.8` probability gates, `N60-72` ranges,
  `chord(I)` roman numerals, v3 `C4 q` shorthand, `x4` repeats, `while`
  loops, `for $i = 0 to N step S`) are NOT covered by the v5 statement
  test suite — they belong to v3/v4 paths and compile with deprecation
  warnings. Prefer the tested v5 statements for new code.
- Repo facts (commands, plugin names, sample paths) were verified by
  reading `run.py`, `eshell.py`, `ep.py`, plugin `__init__.py` docstrings,
  and the samples/examples tree in this repository.
