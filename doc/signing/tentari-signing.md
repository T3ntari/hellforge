**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [regas-trust](regas-trust.md) | [tentari-signing](tentari-signing.md) | [key-management](key-management.md) | [verification](verification.md)

## TENTARI Signing

**TENTARI** is the author trust tag used by official HELLFORGE plugins
(`Made by Tentari`), alongside the local ED25519 signing mechanism.

### How it works today

- `sign --setup` generates a local ED25519 keypair under `.e_identity/`
- `sign <file>` signs a file with author metadata using that identity
- Verification is local: signatures are checked against the stored public
  key and the keys in `.e_identity/trusted/`
- Enforcement is `sys strict 0|1|2` (2 = block unsigned plugins)

### TENTARI vs REGAS (legacy)

| Aspect | TENTARI | REGAS |
|---|---|---|
| Server confirmation | Never | Removed (legacy tag only) |
| Trust scope | Local, per machine | — |
| Strict level required | optional (`sys strict` 1–2) | — |
| Key storage | `.e_identity/` (local) | — |

Neither tag implies server-side trust today. The recommended path for a
plugin author: write your driver, add it to `pkglist.json` with a SHA-256
verification code, and sign your files locally if you want the
`sys strict` protections.