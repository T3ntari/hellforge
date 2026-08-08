# Architecture — File Map & Data Flow

## Root entry points

| File | Role |
|---|---|
| `ep.py` | CLI shim → `ep_compiler.cli.main()`; re-exports compile/events/formats |
| `run.py` | Launcher: `play/compile/check/shell/stats/tracks/inspect/new/transpose/tempo/merge` (+ `--window/--detach/--gui`) |
| `eshell.py` | Interactive shell: `do_*` handlers dispatched from a command map; boots plugins; merges `ep_core._eshell_commands` |
| `player.py` / `ai.py` | pygame playback (compiles first) / copilot CLI → `plugins/llm` |
| `ep_core.py` | Plugin/mod registry (`_PluginAPI`), event hooks, GC, ED25519 signing, identity, encryption, ezip |
| `ep_pkg.py` | Package registry / signing client |
| `piano_synth.py`, `ep_audio.py` | WAV rendering (NumPy synth + audio devices) |
| `render_midi.py`, `play_all.py`, `_launch.py` | Utilities |

## ep_compiler/ (the core)

- **Pipeline**: `compile.py` (orchestrator: `compile_source`/`compile_v1`/
  `compile_file`, version detect, post passes, strict errors), `events.py`
  (event dict contract), `directives.py` (`@`-parser, `DEFAULT_LL_STATE`),
  `comments.py`/`punctuation.py` (stripping/separators), `math_engine.py` +
  `variables.py` (`{$expr}` → AST → evaluator registry; `Scope`), `loops.py`
  (unroller), `syntax_check.py` + `lint.py` (lexicons, validators, lint),
  `scale_quantizer.py` (snap-to-scale), `graph.py`/`paths.py`/
  `runtime_config.py`/`debug.py` (guard/paths/limits/trace),
  `formats.py` (MIDI/EC/WAV/EIC export), `import_midi.py`/`audio_transcribe.py`
  (imports), `cli.py` + `cli_cmds.py` (CLI + shared eshell implementations).
- **Modes** (detailed map in compiler.md): `mode_v1_machine/human`,
  `mode_v2_semantic` (+`_v2compiler`), `mode_v3_extended`,
  `mode_v4_polyrhythm`, `mode_v5_performance`, `mode_v5_statements`,
  `mode_eci`, `e_runtime`, `mode_enx`.

## plugins/ (each is a package)

`llm/` (AI copilot) · `humanize/` (performance feel) · `eaudio/` (spatial
audio) · `radical/` (GPU math) · `vulkanizer/` (Vulkan compute) ·
`tensorsharp/` (tensor cores) · `openapi/` (OpenGL) · `lure/` (LuaJIT
accelerator) · `talisman/` (event culling) ·
`launcher/`, `learner/`, `portbaby/` (conversion), `example_plugin.py`.

## tests/

Self-contained `*_test.py` harness suites (no pytest): `parse_test`,
`syntax_test`, `v5_statements_test`, `piano_features_test`, `paths_test`,
`lint_test`, `cli_commands_test`, `async_test`, `launch_test`, `gpu_test`,
`humanize_test`, `llm_plugin_test`, `lsp_test`, `verify_signing` +
`run_all.py`. Harness contract in testing.md.

## Data flow: source → audio (end to end)

```
.e source → compile_source() → strip comments → include/!fn → version detect
→ preprocess (v3 → polyrhythm → performance pre) → unroll loops → math →
v5 statements → per-line parse (machine | human | v5 | plugin) →
sort/validate → @scale quantize → @gain/@gc/@mem → performance post-passes
→ post_compile hooks (humanize → talisman) → events
  ├─ export_midi()  → .mid (mido, CC64 sustain) → piano_synth.render() → .wav/.mp3
  ├─ export_ec()    → .ec compiled binary
  └─ ep_core._last_compiled_events (player reads this)
```

Project formats join upstream: `compile_file` routes `.ei` (parts/sections),
`.eci` (mode toggles), `.enx` (album ordering) — all resolve to the same
`compile_source` path and event dict.

## eshell command routing

`eshell.py main()` → boots core (`ep_core.init`, plugin loading, boot
progress) → REPL → dispatch map (`compile/play/info/stats/tracks/inspect/
new/transpose/tempo/merge/convert/lint/generate/encrypt/ecc/mod/plugin/
pkglist/audio/ezip/gc/sys/clear/help/exit` + aliases), then merges
`ep_core._eshell_commands` (plugins) and `_eshell_keybindings`. Built-in
handlers live in `ep_compiler/cli_cmds.py`; `cli.py::main()` is the
non-interactive equivalent. `help` appends plugin sections.

## Boot sequence

`eshell.py`/`ep.py` → `ep_core.init()` → `load_plugins()` (register → dep
check → signing verify per `sys strict` level) → `load_mods()` (AST scan) →
boot progress → REPL. `run.py` spawns the others as subprocesses
(optionally detached, logging to `logs/`).