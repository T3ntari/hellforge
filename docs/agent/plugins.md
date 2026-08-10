# Plugin API (ep_core.py `_PluginAPI`) — Drivers & the Hypervisor

HELLFORGE is OS-like: `ep_core.py` is the **kernel**, every plugin is a
**driver**, K-rip (`plugins/krip/`) is the **hypervisor**. Plugins extend
the compiler and eshell; loaded at boot from `plugins/` (single `*.py` or
`dir/__init__.py`). Mods load from `mods/` with an AST security scan and
restricted builtins. Entry point: `def register(api)`. Plugin dependency
`api.require('numpy')` → pip-installed on boot. `ep_core` auto-disables
plugins that crash on load (fatal) and remembers via `.plugin_config.json`.

## The 14 driver plugins

| Driver | One-line purpose |
|---|---|
| `krip/` | **The hypervisor** — GRUB-style boot manager, kernel registry, sandbox layer (mem/CPU/GPU/engine), safe updates |
| `hellgate/` | OpenCode wrapper: boots the TUI inside the repo, provider registry, knowledge pack, Music-Composer/Refiner personas |
| `llm/` | AI copilot — `ai ask/chat/fix/plugin/agent`, JSON-plan agent loop, intent routing, indexing, TUI |
| `eaudio/` | Low-level 3D spatial audio API (devices, PCM buffers, spatial/doppler, effects) |
| `humanize/` | Performance feel — MoE micro-timing + expressive velocity (`@humanize:nn`) |
| `launcher/` | New-window launching & process management (`launcher open/player/compile/...`) |
| `learner/` | Interactive CLI tutorial for E (`learner start/lesson/list/progress`) |
| `lure/` | LuaJIT compile accelerator (5–15× on the hot path; requires `lupa`) |
| `openapi/` | Low-level OpenGL graphics API (context/shader/buffer/... primitives) |
| `portbaby/` | Syntax conversion v1–v4 ↔ v5 — backs `run.py compile --to vN` |
| `radical/` | GPU shader math core (E math AST → GLSL compute shaders) |
| `talisman/` | Audio culling/occlusion + privacy & QOL engine (local-only mode, backups) |
| `tensorsharp/` | NVIDIA Tensor Core math (CuPy, TF32/FP16 mixed precision) |
| `vulkanizer/` | Low-level Vulkan graphics & compute API (instance/pipeline/ray-trace/...) |

The single-file reference plugin lives in `examples/plugins/example_plugin.py`
(`register(api)` + `register_variable_handler` + `register_syntax` demo).

## Registration methods (`api`)

| Method | Purpose |
|---|---|
| `add_command(name, handler, help_text)` | eshell command; handler gets `(args: list[str])`; help groups commands under the registering plugin |
| `add_help_section(title, lines)` | section appended to `help` output |
| `add_keybinding(key, action, desc)` / `set_prompt_renderer(fn)` / `add_output_filter(fn)` | eshell UX |
| `on(event, cb)` | lifecycle hook (events below) |
| `register_syntax(handler)` | extra line parser: `handler(line, ll_state) -> event or None` (tried after machine/human) |
| `register_variable_handler(fn)` | resolves unknown `$vars`: `fn(name) -> value or None` |
| `register_directive(pattern_re, handler)` | custom `@directive`: `handler(match, state)` |
| `register_math_evaluator(name, fn, priority)` | math evaluator: `fn(ast_dict, vars_dict) -> number`; lower priority first |
| `register_gc(name, strategy_fn)` | `@gc:<name>` strategy: `fn(events) -> events` |
| `register_encryptor(name, enc, dec)` | `.ee` encryption methods |
| `require(*pkgs)` | declare pip dependencies (auto-installed) |
| `get_config/set_config/get_all_configs` | persisted config (`.plugin_config.json`) |
| `register_auth_provider(name, cfg)` / `get_auth_token` / `set_auth_token` / `clear_auth_token` | token storage (persisted) |
| `set_theme(**kw)` / `add_boot_step(label, status)` / `log(msg)` | UI cosmetics + boot progress bar |
| `project_dir`, `commands`, `theme` | properties: root path, registered commands, theme dict |

## Event hooks (api.on)

`pre_compile(text)` → transformed text (last wins) · `post_compile(events,
bpm)` → new events (feed-forward) · `pre_play`/`post_play` ·
`pre_render`/`post_render` · `on_load`/`on_unload`/`on_exit`.

## Minimal plugin

```python
def register(api):
    api.add_command("echo", echo_cmd, "print args back")
    api.on("post_compile", after_compile)

def echo_cmd(args):
    print("echo:", " ".join(args))

def after_compile(events, bp):
    print(f"compiled {len(events)} events")
    return events          # None = leave events unchanged
```

## Plugin structure

```
plugins/myplug/__init__.py   # def register(api): ...
plugins/myplug/helper.py     # package modules (optional)
```

Single-file plugins are `plugins/myplug.py`. Name conflicts (file vs dir):
directory wins with a warning. Disable via `plugin remove` / config
`_disabled.plugins`. `pkglist.json` may declare per-plugin deps.

## K-rip — the hypervisor (plugins/krip/)

- **Boot manager**: GRUB-style menu (3s countdown, ↑/↓ select, Enter boot,
  `c` console, `u` update, Esc exit) → boots the kernel → eshell console.
  Kernel registry in `.e_identity/kernels.json`: current + previous
  (normal + safemode entries); booting a previous kernel performs a safe
  update (rollback) to that tag.
- **Sandbox layer**: memory budget (RLIMIT_AS), CPU thread caps + affinity,
  GPU selection (`CUDA_VISIBLE_DEVICES`, single/multi/list/auto), engine
  (vulkan default / opengl), vulkanrt on/off, tensor on/off/auto.
  `krip sandbox run <name> -- <cmd...>` / `list` / `kill` — confined to the
  project root.
- **Config**: `krip.json` at the project root — `krip edit` opens it in nano
  with **live reload**; `krip mem <mb>` / `cpu <n>` / `gpu <spec>` /
  `engine <vulkan|opengl>` / `vulkanrt <on|off>` / `tensor <on|off|auto>` /
  `status` / `os` (kernel · hypervisor · drivers table).
- **Everything launches through krip**: `krip` → menu → console; `krip run
  <cmd>`; `krip eshell|shell`; `krip hellgate`; `krip player <file>`;
  `krip status`. `run.py` re-enters through it. Children get `KRIP_INNER=1`
  (no re-wrap), `KRIP_SANDBOX`, GPU/engine/tensor env; `KRIP_BYPASS=1`
  skips the wrap.

## HellGate — the OpenCode wrapper (plugins/hellgate/)

`run.py hellgate` / `krip hellgate` boots **OpenCode** directly, focused in
the project root, with this knowledge pack fed in:

- Wrapper warning every launch; first-run onboarding on a new machine
  (specs-based: summertime + legal agreements).
- Provider registry (first-available wins the default, Ollama LAST):
  Anthropic, OpenAI, OpenRouter, Google Gemini, custom, Ollama. Ollama asks
  for a model via a select list of every installed model (`/api/tags`).
- HellCode welcome page + loading screen with a real `x/1024` counter.
- Session commands: `Enter`/`$new` relaunch, `$agent` (Music-Composer /
  Music-Refiner / default), `$provider`, `$model`, `$dir`; `q` quits.
- Knowledge pack (`knowledge/`): `full.md` (comprehensive), `core.md`
  (distilled digest), `agents.md` (personas), `samples-index.md`; `current.md`
  is generated at launch (digest for small contexts, full map otherwise).
- All state lands in `hellgate-state/` inside the repo — never touch it.

## X/Y integrity (what every driver runs under)

- `SECURITY_HASH.txt` — committed manifest (SHA-512 per covered file) +
  160-byte triple aggregate (SHA-256 + SHA-512 + BLAKE2b-512).
- **Technique X**: the digest is hidden as rotating random fragments under
  `.e_identity/.integrity` (order file auto-deleted after use, re-randomized
  every init) — an offline proof of the current core state.
- **Technique Y**: per-version key in `ep_compiler/_version_key.py`
  (blake2b512(aggregate + ":" + version tag)), verified online against the
  GitHub copy at the version tag.
- Boot order: X (local) → network probe → Y + version check; offline, X
  alone suffices. Failure → **SAFE MODE** (plugins isolated;
  `status`/`reinstall`/`/safemode exit force`).
- After intentional core changes, regenerate everything together:
  `python3 tools/gen_security_hash.py` and commit the manifest + key + X.
  `tools/verify_integrity.py` verifies locally.

## Mods (secure drop-ins)

`mods/<name>.py` or `mods/<name>/__init__.py` with `def init(api)` (not
`register`). Scanned with `ast_scan`: blocks subprocess/eval/exec/open/
getattr and dangerous dunders; executed with `RESTRICTED_BUILTINS` (no
import, no file I/O). Same `api` otherwise.
