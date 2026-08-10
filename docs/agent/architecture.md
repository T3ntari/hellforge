# Architecture — HELLFORGE OS: Kernel, Drivers, Hypervisor

HELLFORGE behaves like an OS: `ep_core.py` is the **kernel**, every plugin
is a **driver**, K-rip is the **hypervisor** (`krip os` shows the table).
Version **v0.1.14.41-beta**. Everything launches through krip; the boot
flow is: **boot menu → krip sandbox → integrity X → Y → console**.

## Boot flow (end to end)

```
krip (no args)
  → GRUB-style menu: 3s countdown · ↑/↓ · Enter boot · c console
    · u update (safe) · Esc exit · Ctrl+C console
  → boot entry (current kernel; previous kernel = safe-update rollback)
  → SAFE MODE check if the kernel entry is safemode
  → eshell console spawn INSIDE the krip sandbox
      (memory budget · CPU affinity · GPU env · engine vulkan/opengl)
      with KRIP_INNER=1

eshell/eshell.py boot:
  → [security] technique X (offline hidden digest)   ← local proof, first
  → network probe:
        offline → "X is the proof, skipping Y" (rotate X, boot)
        online  → technique Y (per-version key vs GitHub @ tag)
                  + version check → offer safe update
  → ep_core.init(): load plugins (register → deps → signing per
      `sys strict` level) → load mods (AST scan) →
      boot progress → REPL
```

`run.py <mode>` and `eshell.py` both **re-enter through the hypervisor**
(self-spawn via `plugins.krip._spawn` unless `KRIP_INNER=1` or
`KRIP_BYPASS=1`). Children carry `KRIP_INNER`, `KRIP_SANDBOX`,
`KRIP_ENGINE`, `KRIP_VULKANRT`, `KRIP_TENSOR`, and GPU env.

## X/Y integrity

- **`SECURITY_HASH.txt`** — committed manifest: SHA-512 per covered core
  file + a 160-byte triple aggregate (SHA-256 + SHA-512 + BLAKE2b-512 over
  the sorted manifest).
- **Technique X** — the aggregate is split into tiny hidden fragments
  re-randomized into `.e_identity/.integrity/.store` on every init; the
  order file (`.e_identity/.integrity/.order`) is **auto-deleted after
  use**. Offline proof of the current core state — tampering with any
  covered file (or the fragments) mismatches and triggers SAFE MODE.
- **Technique Y** — a permanent per-version key
  (`blake2b512(aggregate + ":" + version_tag)` committed in
  `ep_compiler/_version_key.py`), verified online against the
  `SECURITY_HASH.txt` at the version tag on GitHub.
- Boot order: **X → network → Y/version-sync**; offline, X alone suffices.
- Check it yourself: `run.py integrity [--github]`.
- Regenerate after intentional core changes: `python3
  tools/gen_security_hash.py` (commit manifest + key + X together);
  `tools/verify_integrity.py` verifies locally.

## SAFE MODE

Entered when X or Y fails. The core is isolated — plugins are NOT loaded;
a minimal restricted shell offers: `status` (what failed), `reinstall`
(re-install the current version from GitHub with a progress bar; configs/
plugins/mods/identity preserved; "installation successful, exiting safe
mode"), `/safemode exit force` (warned: highly risky), `quit` (stay, safe).

## Safe updates

`ep_compiler/update.py::safe_update(tag)` — version = a GitHub version tag:

1. Backup user data: `.plugin_config.json`, `.env`, `.e_identity/`, `mods/`,
   `SECURITY_HASH.local`, custom plugin dirs → `.backup_update/`.
2. K-rip kernel registry snapshot (`snapshot_previous_kernel`) — the current
   kernel becomes a bootable previous entry (rollback target).
3. `git fetch origin tag <tag>` → stash uncommitted work → `checkout -f`.
4. Restore user data; **register custom plugins in `SECURITY_HASH.local`**
   so the digest accepts them.
5. Restore stashed work; fresh X + Y embed + integrity re-check.

`krip` menu: a "NEW KERNEL AVAILABLE" notice appears and `u` updates.
Booting a previous kernel entry performs `safe_update(previous_tag)` —
"nothing is lost".

## Root entry points

| File | Role |
|---|---|
| `ep.py` | CLI shim → `ep_compiler.cli.main()`; re-exports compile/events/formats |
| `run.py` | Launcher: `play/compile/check/shell/stats/tracks/inspect/new/transpose/tempo/merge/integrity/hellgate/ai`; re-enters through krip |
| `eshell.py` | Interactive shell: `do_*` handlers dispatched from a command map; boots plugins; merges `ep_core._eshell_commands` |
| `player.py` / `ai.py` | pygame playback (compiles first) / copilot CLI → `plugins/llm` |
| `ep_core.py` | **The kernel**: plugin/mod registry (`_PluginAPI`), event hooks, GC, ED25519 signing, identity, encryption, ezip |
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
  (imports), `cli.py` + `cli_cmds.py` (CLI + shared eshell implementations),
  `security_hash.py` (X/Y), `safemode.py`, `update.py`.
- **Modes** (detailed map in compiler.md): `mode_v1_machine/human`,
  `mode_v2_semantic` (+`_v2compiler`), `mode_v3_extended`,
  `mode_v4_polyrhythm`, `mode_v5_performance`, `mode_v5_statements`,
  `mode_eci`, `e_runtime`, `mode_enx`.

## plugins/ (drivers — 14 shipped)

`krip/` (hypervisor) · `hellgate/` (OpenCode wrapper) · `llm/` (AI copilot)
· `eaudio/` (spatial audio) · `humanize/` (performance feel) · `launcher/`
(process mgmt) · `learner/` (tutorial) · `lure/` (LuaJIT accelerator) ·
`openapi/` (OpenGL) · `portbaby/` (syntax conversion) · `radical/` (GPU
shader math) · `talisman/` (audio culling + privacy) · `tensorsharp/`
(tensor cores) · `vulkanizer/` (Vulkan compute). One-line purposes +
registration API in plugins.md. Reference plugin:
`examples/plugins/example_plugin.py`.

## tests/

Self-contained `*_test.py` harness suites (no pytest): `parse_test`,
`syntax_test`, `v5_statements_test` (the authoritative v5 statement set),
`piano_features_test`, `paths_test`, `lint_test`, `cli_commands_test`,
`async_test`, `launch_test`, `gpu_test`, `humanize_test`,
`llm_plugin_test`, `lsp_test`, `verify_signing`, `security_hash_test`
(X/Y), `run_all.py` (combined) + `plugins/krip/tests/test_krip.py`
(hypervisor). Harness contract in testing.md.

## Data flow: source → audio (end to end)

```
.e source → compile_source() → strip comments → include/!fn → version detect
→ preprocess (v3 → polyrhythm → performance pre) → unroll loops → math →
v5 statements → per-line parse (performance | machine | human | v5 | plugin)
→ sort/validate → @scale quantize → @gain/@gc/@mem → performance post-passes
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
non-interactive equivalent. `help` appends plugin sections. Boot log
conventions: `Plugin X present (N files)`,
`[encryption] N module(s): ...`.
