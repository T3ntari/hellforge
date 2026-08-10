**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [pkglist](pkglist.md) | [plugin-management](plugin-management.md) | [embedded-backups](embedded-backups.md) | [signing-plugins](signing-plugins.md)

## Package Registry Format (pkglist.json)

`pkglist.json` at the project root is the local package catalog: every
shipped plugin has an entry with a **SHA-256 verification code** — the
hash of its `__init__.py` (via `ep_compiler.plugin_security`).

### Structure

```json
{
  "version": "1.0.0.0",
  "plugins": {
    "talisman": {
      "version": "1.0.0",
      "description": "Audio culling & occlusion engine ...",
      "author": "Tentari",
      "tags": "HELLFORGE,TENTARI,audio,culling,...",
      "url": "file://plugins/talisman/__init__.py",
      "dependencies": [],
      "verification": "c5970a79... (SHA-256)"
    }
  }
}
```

### Verification codes & integrity

Each `verification` field is the SHA-256 of the plugin's `__init__.py`.

```
python3 tools/verify_integrity.py          # local: compare installed plugins
                                           #        against the published codes
python3 tools/verify_integrity.py --remote # also pull codes from the registry
                                           #        configured via HF_VERIFY_URL
                                           #        + HF_VERIFY_TOKEN (opt-in)
```

Local mode works for anyone — no secrets, nothing hardcoded. Unset
`HF_VERIFY_URL` means local-only.

### Registry via environment (opt-in)

- `HF_REGISTRY` — package registry base (empty = local-only)
- `HF_VERIFY_URL` + `HF_VERIFY_TOKEN` — private verification registry
  (empty = local-only)
- `HF_DEPLOY_*` — deploy tooling (only if you use it)

### In the console

`pkglist show|update|search|version|detail` manages the catalog; the
`plugin` command manages plugins (list/avail/scan/update/fetch/remove/
version). See [Plugin Management](plugin-management.md).

---

**HELLFORGE OS v0.1.14.41-beta** — local package catalog