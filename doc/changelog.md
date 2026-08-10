**HELLFORGE OS v0.1.14.41-beta** — [index](index.md) | [getting-started](getting-started.md) | [contributing](contributing.md) | [changelog](changelog.md) | [faq](faq.md)

## Changelog

### v0.1.14.41-beta (current)

The HELLFORGE OS release — kernel, hypervisor, drivers.

- **K-rip hypervisor v1.0.0** (`plugins/krip`): every launch re-enters
  through K-rip (`krip run <cmd>`, `krip eshell`, `krip hellgate`,
  `krip player`). GRUB-style boot menu: 3s countdown auto-boot, ↑/↓
  select, Enter boot, `c` console, `u` safe update, Esc exit; styled
  banner + blue highlight bar + mode chips. Children run sandboxed
  (`KRIP_INNER=1`, `KRIP_BYPASS=1` escapes).
- **K-rip sandbox layer**: `krip mem <mb>` (RLIMIT_AS soft),
  `krip cpu <n>` (affinity), `krip gpu <auto|list|all|0,1|2 3>`
  (multi-GPU via `CUDA_VISIBLE_DEVICES`), `krip engine <vulkan|opengl>`
  (vulkan default), `krip vulkanrt <on|off>`, `krip tensor <on|off|auto>`,
  `krip sandbox run/list/kill/status`, `krip os`, `krip kernels`,
  `krip edit` (LIVE auto-reload), `krip config/save/reload/reset`.
  Config: `krip.json` at the project root.
- **Kernel registry** (`.e_identity/kernels.json`): current + previous
  kernel entries (previous seeded from the git tag before current),
  bootable rollback via safe update, `ep_core:safemode` entries.
- **X/Y integrity**: committed `SECURITY_HASH.txt` (per-file SHA-512
  manifest + 160-byte triple aggregate SHA-256+SHA-512+BLAKE2b-512).
  Technique X: rotating hidden digest fragments in a deep gitignored
  store (`.e_identity/.integrity/.store`), order file auto-deleted after
  use, re-randomized every init. Technique Y: per-version key hash
  (blake2b512 of aggregate+tag) in `ep_compiler/_version_key.py`,
  verified against the live GitHub copy at the version tag (peeled
  commit). Boot order: X (offline proof) → network → Y + version sync.
- **SAFE MODE** (`ep_compiler/safemode.py`): isolated shell on failure —
  status / reinstall with progress bar (everything preserved) /
  `/safemode exit force` with risk warning.
- **Safe updates** (`ep_compiler/update.py`): version = GitHub's version;
  preserves custom plugins, mods, `.plugin_config.json`, `.env`,
  `.e_identity`; backup/restore + `SECURITY_HASH.local` extension for
  custom plugins.
- **HellGate** (`plugins/hellgate`): boots OpenCode focused in the repo —
  onboarding questions (summertime rendering + legal agreement,
  machine-specs based first run), wrapper warning every launch, HellCode
  welcome page + `x/1024` loading counter, provider registry (Anthropic,
  OpenAI, OpenRouter, Google, custom, Ollama last), `$provider`/`$model`/
  `$agent`/`$dir`/`$new` session commands, Music-Composer +
  Music-Refiner agents, knowledge pack.
- **v5 canonical syntax**: v5 default; v1–v4 deprecated with explicit
  markers; convert via `run.py compile --to v5`. Polyrhythm
  `[C4 E4 G4](3:2)`, Euclidean `E(5,4)` and v3 shorthand (`C4 q`) are
  valid v5. Linter is v5-aware (`run.py check` → at most `I001` on pure
  v5). Example piece: `songs/aurora_nocturne.e`.
- **14 shipped plugins** (drivers): krip, hellgate, llm, eaudio, humanize,
  launcher, learner, lure, openapi, portbaby, radical, talisman,
  tensorsharp, vulkanizer. Example reference plugin moved to
  `examples/plugins/example_plugin.py`.
- **Clean boot log**: "Plugin X present (N files)" with real counts,
  "[encryption] N module(s)", no example-plugin noise.
- **Security posture**: no network backend, no hardcoded endpoints, no
  credentials; opt-in env config (`HF_REGISTRY`, `HF_VERIFY_URL`,
  `HF_VERIFY_TOKEN`, `HF_DEPLOY_*`, LLM keys); local-only plugin integrity
  via `pkglist.json` SHA-256 codes + `tools/verify_integrity.py`;
  `.e_identity/` gitignored.
- **Testing**: per-suite `python3 tests/<name>_test.py`;
  `tests/run_all.py`; `tests/security_hash_test.py` (X/Y);
  `plugins/krip/tests/test_krip.py`; all green.
- **eshell help structure**: built-ins, then plugin-authored help
  sections (plain lines or `(cmd, desc)` pairs), then plugin commands
  grouped by registering plugin with aliases marked `(alias)` and dimmed.

### Earlier milestones (pre-OS)

- LURE LuaJIT accelerator v3.0.0 (sync + async engines, Python fallback).
- GPU math pipeline: Radical (GLSL compute, multi-GPU, VRAM limits),
  TensorSHARP (Tensor Cores), OPENapi (OpenGL), Vulkanizer (Vulkan).
- EAudio low-level audio API; Humanize MoE; Talisman audio culling;
  Portbaby syntax conversion; Learner tutorial; Launcher.
- LLM copilot plugin (`ai` command) with providers and the HELL'S CODE TUI.
- Local ED25519 signing, `sys strict` enforcement, plugin integrity
  manifest (`pkglist.json` verification codes).

---

**HELLFORGE OS v0.1.14.41-beta** — kernel `ep_core` · hypervisor K-rip v1.0.0
