**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [regas-trust](regas-trust.md) | [tentari-signing](tentari-signing.md) | [key-management](key-management.md) | [verification](verification.md)

## Signing System Overview

HELLFORGE signing is **local and optional** — it must never be made
mandatory. There is no server registry, no remote identity confirmation,
and no hardcoded trust keys. The system is built around a local ED25519
identity:

- **Local signing** — `sign --setup` creates an ED25519 keypair under
  `.e_identity/`; `sign <file>` signs files with it.
- **Enforcement** — `sys strict 0|1|2` decides whether unsigned plugins
  are allowed (default 0), warned (1) or blocked (2). See
  [Strict enforcement](../security/strict-enforcement.md).
- **Trust tags** — `TENTARI` and `REGAS` remain **author tags** in plugin
  metadata (e.g. `Made by Tentari. Signed: REGAS.`); they no longer imply
  any server-side confirmation. See [TENTARI](tentari-signing.md) and
  [REGAS](regas-trust.md).

Separately, **plugin integrity** is verified by hashes: SHA-256
verification codes in `pkglist.json` checked with
`tools/verify_integrity.py` (with an optional private registry via
`HF_VERIFY_URL` — see [pkglist](../packaging/pkglist.md)), and the core
digest via the committed `SECURITY_HASH.txt` X/Y system (see
[Integrity](../commands/integrity-commands.md)).

---

**HELLFORGE OS v0.1.14.41-beta** — local-first, opt-in, nothing mandatory.