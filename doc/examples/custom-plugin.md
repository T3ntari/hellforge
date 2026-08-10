**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [custom-plugin](custom-plugin.md) | [gpu-compute](gpu-compute.md) | [game-engine](game-engine.md)

## Custom Plugin Creation

This guide walks through creating an E plugin (driver) from scratch, based
on the reference plugin at
[`examples/plugins/example_plugin.py`](../../examples/plugins/example_plugin.py).

### Step 1: Start from the reference

Copy the example into `plugins/`:

```bash
cp examples/plugins/example_plugin.py plugins/myplugin.py
```

A plugin is a Python module with a `register(api)` entry point:

```python
def register(api):
    """Called when the plugin is loaded. `api` provides registration functions."""
    api.register_variable_handler(custom_var_handler)
    api.register_syntax(custom_syntax_parser)
    api.log("  > Example plugin registered: $repeat, @shuffle syntax")
```

### Step 2: Add commands, help, boot steps

```python
def register(api):
    api.add_boot_step("MyPlugin v1.0.0", "loading")
    api.add_command("mycmd", _cmd, "MyPlugin: mycmd status|do")
    api.add_help_section("MyPlugin Commands", [
        ("mycmd status", "Show my plugin's status"),
    ])
    api.add_boot_step("MyPlugin ready", "done")
```

Commands appear in `help` grouped under the registering plugin; aliases
are marked `(alias)` and dimmed.

### Step 3: Register in pkglist.json

Add your plugin's SHA-256 verification code to `pkglist.json` so
`tools/verify_integrity.py` can check it (see
[pkglist](../packaging/pkglist.md)). Custom plugin dirs are preserved
across safe updates and registered in `SECURITY_HASH.local`.

### Step 4: Sign (optional)

Signing is opt-in: `sign --setup` once, then `sign <file>` (see
[Signing](../signing/overview.md)).

### Step 5: Publish

Keep the plugin in `plugins/<name>/` in the repo and document it under
`doc/plugins/` + `doc/commands/`. Full API reference:
[Developing Plugins](../plugins/developing-plugins.md).