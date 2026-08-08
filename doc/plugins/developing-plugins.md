# **HELLFORGE v1.0.0.0 ALPHA — Developing Plugins**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

This guide explains how to write, register, sign, and distribute plugins for the HELLFORGE engine.

## Writing a Plugin

Every plugin must implement the `HELLFORGE_Plugin` struct:

```c
typedef struct {
    const char* name;
    uint32_t api_version;
    uint32_t eval_priority;
    bool (*init)(HELLFORGE_Core* core);
    void (*shutdown)(void);
    bool (*eval)(AST_Node* node, EvalResult* out);
} HELLFORGE_Plugin;
```

- `init` — called once during boot. Return `true` on success.
- `shutdown` — called during engine teardown.
- `eval` — called by the evaluator scheduler for each matching AST node.

## Registering a Plugin

Compile your plugin as a shared library (`.dll`, `.so`, `.dylib`) and place it in the `plugins/` directory. The engine scans for exported symbols matching `HELLFORGE_RegisterPlugin`:

```c
HELLFORGE_Export HELLFORGE_Plugin* HELLFORGE_RegisterPlugin(void) {
    static HELLFORGE_Plugin plugin = {
        .name = "myplugin",
        .api_version = HELLFORGE_API_VERSION,
        .eval_priority = 5,
        .init = my_init,
        .shutdown = my_shutdown,
        .eval = my_eval
    };
    return &plugin;
}
```

## Signing a Plugin

Use the `hf-sign` CLI tool bundled with the SDK:

```bash
hf-sign --key mykey.pem --plugin myplugin.dll --output myplugin.signed.dll
```

The engine verifies the embedded signature against the trusted root CA during `init`. Unsigned plugins load only if `@allow-unsigned` is set in the engine config.

## Distributing a Plugin

1. Package the signed plugin binary and a manifest (`plugin.json`) describing dependencies, permissions, and version.
2. Host on any HTTPS server or the HELLFORGE community registry.
3. Users install via `hf install <url>` or drag-and-drop into the plugins directory.

---

**API Reference:** `#include <plugin_sdk/hellforge.h>`

**HELLFORGE v1.0.0.0 ALPHA — Developing Plugins**
