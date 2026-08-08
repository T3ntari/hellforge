**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [pkglist](packaging/pkglist.md) | [plugin-management](packaging/plugin-management.md) | [embedded-backups](packaging/embedded-backups.md) | [signing-plugins](packaging/signing-plugins.md)

## Package Registry Format

The package registry (`pkglist`) is a JSON-based catalog of available Piano DSL plugins.

### Structure

```json
{
  "registry": "<HF_REGISTRY>",
  "packages": {
    "plugin-name": {
      "version": "1.0.0",
      "fingerprint": "a1b2c3d4...",
      "trust": "REGAS",
      "verification": "verified"
    }
  }
}
```

### Verification Codes

| Code | Meaning |
|---|---|
| `verified` | Signature matches registered key |
| `unverified` | No signature present |
| `unknown` | Unknown signing key |
| `tentari_trusted` | TENTARI signature in local keystore |
| `regas_confirmed` | REGAS server-confirmed signature |

The registry is fetched from `HF_REGISTRY` (env, empty = local-only) and cached locally.

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**