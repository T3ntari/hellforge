# HELLFORGE E Language

A piano-music DSL that behaves like an operating system: **kernel** (`ep_core`),
**drivers** (plugins), and a **hypervisor** (K-rip) that sandboxes and boots
everything.

```
run.py krip
```

## What you get

- **K-rip hypervisor** — a GRUB-style boot menu at every start (3s countdown,
  arrow selection, `c` console, `u` safe-update, `Esc` exit), a heavy sandbox
  layer over the whole shell (memory budgets, CPU affinity, multi-GPU
  selection, graphics-engine default, VulkanRT, Tensor), a real `krip.json`
  config file edited with `krip edit` (nano — live reload on save), and
  sandboxed launches for anything (`krip run <cmd>`).
- **X/Y integrity** — the core digest (per-file SHA-512 manifest + 160-byte
  triple aggregate) is committed (`SECURITY_HASH.txt`) and re-verified at
  every init: technique X hides rotating digest fragments in the core
  (offline proof), technique Y binds the version's key to the live GitHub
  copy. Any tampering drops the system into **SAFE MODE** (isolated shell,
  reinstall preserving everything, or forced exit).
- **Safe updates** — version local = version on GitHub; update at the boot
  menu with a progress bar, keeping custom plugins, mods, configs and
  identity intact (rollback to the previous kernel is one menu entry away).
- **HellGate** — a wrapper that boots OpenCode inside the project with the
  full v5 knowledge pack, Music-Composer / Music-Refiner agents, and a
  provider registry (Anthropic, OpenAI, OpenRouter, Google, custom, Ollama
  last) with an interactive model picker.
- **The v5 language** — canonical v5 syntax (print/assert/include/!fn/prog/
  perc/loops/@seed/pick/rand/pedal/rest/@art/tuplets/ties), polyrhythm
  `[C4 E4 G4](3:2)`, Euclidean `E(5,4)` and shorthand `C4 q` are valid v5;
  v1–v4 are deprecated with a converter (`run.py compile --to v5`).

## Quick start

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
run.py krip            # boot menu -> console (eshell)
run.py krip help       # krip subcommands
run.py integrity --github   # verify the core digest against GitHub
run.py hellgate        # HellGate -> OpenCode wrapper
run.py compile song.e -o song.mid
```

Everything re-enters through K-rip (`run.py <anything>` and direct `eshell.py`
are wrapped automatically; `KRIP_BYPASS=1` escapes).

## CLI

```
run.py play <file>                run.py compile <file> -o <out>
run.py check <file>               run.py stats|tracks|inspect <file>
run.py new <name>                 run.py transpose|tempo|merge ...
run.py shell                      run.py ai (copilot)
run.py hellgate                   run.py krip [run|eshell|hellgate|player|status]
run.py integrity [--github]
```

## Plugins (drivers)

| Plugin | Purpose |
|---|---|
| `krip` | hypervisor — boot menu, sandbox, allocation, kernel registry |
| `hellgate` | OpenCode wrapper with v5 knowledge + music agents |
| `llm` | AI copilot (`ai`): providers, ask/chat/fix/plugin |
| `learner` | lessons (`question`/`quiz`/`test`) |
| `portbaby` | syntax version porting (`pb`) |
| `radical` | GPU shader math core (GLSL compute) |
| `vulkanizer` | low-level Vulkan API |
| `tensorsharp` | GPU tensor core |
| `lure` | async compile pool |
| `talisman` | audio culling & occlusion |
| `eaudio` | audio devices / DSP |
| `humanize` | humanization |
| `launcher` | process launcher |
| `openapi` | OpenAPI status |

Plugins register via `ep_core`'s API (`add_command`, `add_help_section`,
`register_directive`, `add_boot_step`) — `help` groups their commands under
each plugin automatically. Reference plugin:
`examples/plugins/example_plugin.py`.

## Integrity & security

- `SECURITY_HASH.txt` — committed core manifest; `run.py integrity [--github]`
  compares local computation, committed manifest and the live GitHub copy.
- Technique X (hidden rotating fragments, offline) + technique Y (per-version
  key from GitHub) checked at every init; SAFE MODE on failure.
- No backend, no hardcoded endpoints, no credentials in the repo. Opt-in env:
  `HF_REGISTRY`, `HF_VERIFY_URL`, `HF_VERIFY_TOKEN`, `HF_DEPLOY_*`, LLM
  provider keys. Local identity: `.e_identity/` (gitignored, ED25519).
- `tools/verify_integrity.py` — plugin SHA-256 codes vs `pkglist.json`.
- After intentional core changes: `python3 tools/gen_security_hash.py`
  (regenerates manifest + version key + hidden X) and commit together.

## Testing

```
.venv/bin/python tests/run_all.py            # all suites
.venv/bin/python tests/security_hash_test.py # X/Y integrity
.venv/bin/python plugins/krip/tests/test_krip.py
.venv/bin/python tests/v5_statements_test.py # v5 statement set
```

## License

MIT. HELLFORGE launches the official OpenCode CLI (MIT) unmodified via
HellGate — a wrapper, not an official OpenCode product.
