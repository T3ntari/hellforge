# HELLFORGE — Developing Plugins

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [developing-plugins](developing-plugins.md) | [krip](krip.md) | [hellgate](hellgate.md) | [llm](llm.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [humanize](humanize.md) | [talisman](talisman.md) | [lure](lure.md) | [portbaby](portbaby.md) | [learner](learner.md) | [launcher](launcher.md)

---

## Overview

Plugins are Python packages under `plugins/` with a single `register(api)`
entry point. The kernel (`ep_core`) loads them at boot, resolves declared
dependencies, runs their boot steps, and wires their commands into the
eshell console. Start from the reference plugin at
[`examples/plugins/example_plugin.py`](../../examples/plugins/example_plugin.py).

## Writing a plugin

A minimal plugin:

```python
"""My plugin — a HELLFORGE driver."""

VERSION = "1.0.0"
author = "You"
description = "What the plugin does"

def register(api):
    api.add_boot_step(f"MyPlugin v{VERSION}", "loading")
    api.add_command("mycmd", _cmd, "MyPlugin: mycmd status|do")
    api.add_help_section("MyPlugin Commands", [
        ("mycmd status", "Show my plugin's status"),
    ])
    api.add_boot_step("MyPlugin ready", "done")

def _cmd(args):
    if not args or args[0] == "status":
        print("  MyPlugin v1.0.0 — ready")
        return 0
    print("  Usage: mycmd status")
```

Drop it into `plugins/` (e.g. `plugins/myplugin/__init__.py` or a single
`plugins/myplugin.py`) and it is auto-loaded at boot. Custom plugin dirs
are registered in `SECURITY_HASH.local` by the updater so the digest check
accepts them.

## The plugin API (api object)

| Method | Purpose |
|--------|---------|
| `add_command(name, handler, help_text)` | Register an eshell command; help is grouped by the registering plugin (detected from the call stack) and aliases are marked `(alias)` |
| `add_help_section(title, lines)` | Add a section to `help` — lines are plain strings or `(cmd, desc)` pairs |
| `register_directive(pattern, handler)` | Register a `@directive` regex parser; handler gets `(match, state)` |
| `register_math_evaluator(name, fn, priority)` | Register a math evaluator (lower priority = tried first) |
| `on(event, callback)` | Hook compile/play events (`pre_compile`, `post_compile`, `pre_play`, …) |
| `add_boot_step(label, status)` | Add a step to the boot progress bar (`"done"`/`"loading"`/`"skip"`) |
| `require(*packages)` | Declare pip dependencies, installed automatically on boot |
| `register_syntax(handler)` / `register_variable_handler(handler)` | Custom syntax / `$var` handling |
| `register_encryptor(name, enc, dec)` | Add an encryption method |
| `register_gc(name, strategy)` / `add_keybinding(key, action, desc)` / `set_prompt_renderer(fn)` / `add_output_filter(fn)` | Console integration |
| `get_config(key, default)` / `set_config(key, value)` / `get_all_configs()` | Persisted plugin config (`.plugin_config.json`) |
| `register_auth_provider(...)` / `get_auth_token` / `set_auth_token` | Optional auth providers |
| `set_theme(**kwargs)` | Theme tokens (relative palettes only) |
| `api.project_dir` / `api.commands` / `api.theme` | Properties |

Directives registered by plugins are picked up by the compiler the same
way as built-ins (`@myparam 42` → `ll_state["my_param"]`).

## Signing

Signing is **optional and opt-in** — it is never mandatory. `sign --setup`
creates a local ED25519 identity under `.e_identity/`; `sign <file>` signs
a file. `sys strict 0|1|2` controls enforcement (2 = block unsigned
plugins). See [Signing](../signing/overview.md).

## Distributing a plugin

1. Put it under `plugins/<name>/` in the repo
2. Register its files in `pkglist.json` (SHA-256 verification code, see
   [pkglist](../packaging/pkglist.md))
3. Optional: add a `doc/plugins/<name>.md` page and a
   `doc/commands/<name>-commands.md` page with the actual command strings
4. The safe updater preserves custom plugin dirs across version changes

---

**HELLFORGE OS v0.1.14.41-beta** — kernel `ep_core` · 14 drivers · hypervisor K-rip v1.0.0
