# Plugin API (ep_core.py `_PluginAPI`)

Plugins extend the compiler and eshell. Loaded at boot from `plugins/`
(single `*.py` or `dir/__init__.py`); mods load from `mods/` with an AST
security scan and restricted builtins. Entry point: `def register(api)`.
Plugin dependency `api.require('numpy')` → pip-installed on boot. `ep_core`
auto-disables plugins that crash on load (fatal) and remembers via
`.plugin_config.json`.

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

## Registration methods (`api`)

| Method | Purpose |
|---|---|
| `add_command(name, handler, help_text)` | eshell command; handler gets `(args: list[str])` |
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
| `set_theme(**kw)` / `add_boot_step(label, status)` / `log(msg)` | UI cosmetics |
| `project_dir`, `commands`, `theme` | properties: root path, registered commands, theme dict |

## Event hooks (api.on)

`pre_compile(text)` → transformed text (last wins) · `post_compile(events,
bpm)` → new events (feed-forward) · `pre_play`/`post_play` ·
`pre_render`/`post_render` · `on_load`/`on_unload`/`on_exit`.

## Plugin structure

```
plugins/myplug/__init__.py   # def register(api): ...
plugins/myplug/helper.py     # package modules (optional)
```
Single-file plugins are `plugins/myplug.py`. Name conflicts (file vs dir):
directory wins with a warning. Disable via `plugin remove` / config
`_disabled.plugins`. `pkglist.json` may declare per-plugin deps.

## eshell integration

`add_command` handlers receive `args` as a list of strings and dispatch from
the same table as built-ins; help sections appear under the plugin's own
header in `help`; output filters run on every printed line.

## Reference example: the llm copilot plugin

`plugins/llm/` — a directory plugin. `register(api)` calls
`api.add_command("ai", handler, ...)` exposing `ai fix/chat/ask/read/plugin/
index/...`; stores provider/model/API key via `api.get_config` +
`api.set_auth_token("llm", key)`; reads `api.project_dir` to scope all edits;
`agent.py`'s `safe_path(project_dir, rel)` enforces project-root-only paths.
Its system prompt (AGENTS.md + RULES.md + TODO.md injected) is the
model-side contract — see copilot.md.

## Mods (secure drop-ins)

`mods/<name>.py` or `mods/<name>/__init__.py` with `def init(api)` (not
`register`). Scanned with `ast_scan`: blocks subprocess/eval/exec/open/
getattr and dangerous dunders; executed with `RESTRICTED_BUILTINS` (no
import, no file I/O). Same `api` otherwise.