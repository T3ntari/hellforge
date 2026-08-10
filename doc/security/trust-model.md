**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [trust-model](trust-model.md) | [strict-enforcement](strict-enforcement.md) | [identity-management](identity-management.md) | [rate-limiting](rate-limiting.md)

## Trust Model

HELLFORGE is **local-first**: no network backend, no hardcoded endpoints,
no credentials anywhere in the repo. Trust is established in layers, from
local cryptographic proofs out to optional opt-in network verification.

### Layer 1 — Core integrity (X/Y digests)

Every CLI start recomputes the core digest over ~56 covered files
(`ep_core.py`, `eshell.py`, `ep_pkg.py`, `pkglist.json`,
`ep_compiler/*.py`, `plugins/*/__init__.py`) and compares it against the
committed `SECURITY_HASH.txt` — a per-file SHA-512 manifest plus a 160-byte
triple aggregate (SHA-256 + SHA-512 + BLAKE2b-512).

- **Technique X** — the offline proof: the aggregate (and version key) is
  split into tiny fragments hidden in a deep gitignored store
  (`.e_identity/.integrity/.store`), with an order file
  (`.e_identity/.integrity/.order`) deleted after use and re-randomized
  every init.
- **Technique Y** — the per-version key hash (blake2b512 of
  aggregate+tag) in `ep_compiler/_version_key.py`, verified against the
  live GitHub copy at the version tag when online.

Boot order: **X first (offline proof) → network → Y + version sync**.
Offline, X alone is the proof. Any failure enters **SAFE MODE**.
See [Integrity commands](../commands/integrity-commands.md).

### Layer 2 — Plugin integrity (local codes)

Every shipped plugin has a **SHA-256 verification code** in
`pkglist.json`. `tools/verify_integrity.py` hashes each installed plugin
and compares against the published codes (local mode, no secrets); the
optional `--remote` flag pulls codes from an opt-in registry configured
via `HF_VERIFY_URL` + `HF_VERIFY_TOKEN` — unset variables mean local-only.
See [pkglist](../packaging/pkglist.md).

### Layer 3 — Local signing (optional)

`sign --setup` creates a local ED25519 identity under `.e_identity/`;
`sign <file>` signs files. Trust levels: signed by a local key vs
unsigned. Enforcement is `sys strict 0|1|2`. There is **no server
registration** — REGAS/TENTARI remain author tags in package metadata.
See [Signing](../signing/overview.md).

### Layer 4 — Safe updates

Updates are version-pinned to GitHub tags: backup → fetch/checkout →
restore `.plugin_config.json`, `.env`, `.e_identity/`, `mods/` and custom
plugins → re-register custom plugins in `SECURITY_HASH.local`. The
previous kernel stays bootable via the kernel registry
(`.e_identity/kernels.json`).

### Trust resolution (summary)

1. Core digest vs committed manifest + X hidden fragments (always,
   offline)
2. Version key vs GitHub at the tag (online only)
3. Plugin hash vs `pkglist.json` codes (local) — registry codes when
   `HF_VERIFY_URL` is set
4. Signature / `sys strict` level for file signing (optional)
5. Everything else is a warning, never silently ignored