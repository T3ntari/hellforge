**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [regas-trust](regas-trust.md) | [tentari-signing](tentari-signing.md) | [key-management](key-management.md) | [verification](verification.md)

## Verification Flow

### File signing (local ED25519)

1. `sign --setup` creates the identity (`identity.json` + `secret.key`
   under `.e_identity/`)
2. `sign <file>` hashes the file, signs with the local seed, and embeds
   author metadata (signature + public key)
3. Verification compares the embedded signature against the stored public
   key (`ep_core` `verify_signature`) — no network involved
4. `sys strict 0|1|2` decides whether unsigned plugins/files are allowed,
   warned or blocked

### Plugin integrity (hash-based, local-first)

1. `pkglist.json` publishes a SHA-256 verification code per shipped plugin
2. `tools/verify_integrity.py` hashes each installed plugin and compares
   codes — local mode works for anyone, no secrets involved
3. `--remote` additionally pulls codes from the registry configured via
   `HF_VERIFY_URL` + `HF_VERIFY_TOKEN` (opt-in; unset = local-only)

### Core integrity (X/Y digest)

1. Every CLI start recomputes the per-file SHA-512 manifest + 160-byte
   triple aggregate (SHA-256 + SHA-512 + BLAKE2b-512)
2. Technique X reconstructs the rotating hidden fragments
   (`.e_identity/.integrity/.store`, order file deleted after use) —
   the offline proof
3. Online: Technique Y compares the per-version key hash
   (`_version_key.py`) against the live `SECURITY_HASH.txt` at the
   version tag on GitHub (peeled commit)
4. Any failure → SAFE MODE (isolated shell: status / reinstall / force
   exit with a risk warning)

Full details: [Integrity commands](../commands/integrity-commands.md).