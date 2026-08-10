**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [trust-model](trust-model.md) | [strict-enforcement](strict-enforcement.md) | [identity-management](identity-management.md) | [rate-limiting](rate-limiting.md)

## Identity Management

HELLFORGE identity is **local and optional**. There is no remote account,
no login server, no session tokens: `sign --setup` creates an ED25519
keypair on this machine, and `sign <file>` signs files with it.

### Setup

```
sign --setup
```

Creates the local ED25519 keypair and identity under `.e_identity/`
(gitignored):

- `.e_identity/identity.json` — name, public key, social metadata
- `.e_identity/secret.key` — the private seed (never committed)
- `.e_identity/trusted/` — trusted public keys you add
- `.e_identity/kernels.json` — the K-rip kernel registry (current +
  previous kernels)

### Signing files

```
sign <file>
```

Signs a file with author metadata using the local identity
(`sys strict 0|1|2` controls enforcement). Verification is done locally
against the stored public key — see
[Verification](../signing/verification.md).

### Key management

- `sign --setup` — (re)create the identity
- Trusted keys: imported public keys land in `.e_identity/trusted/`
- Key material lives only on this machine; back it up yourself if needed

### What is NOT here

- No server-side identity confirmation (REGAS registry submission was
  removed from the open-source release — registry auth is not part of the
  project anymore)
- No sessions, no tokens, no remote identity endpoints of any kind
- No hardcoded keys or credentials of any kind

### Related

The **K-rip kernel registry** (`.e_identity/kernels.json`) records which
kernel versions are bootable — current + previous, normal/safemode
entries — for bootable rollback via safe updates. The **X/Y integrity
store** (`.e_identity/.integrity/`) holds the rotating hidden digest
fragments (gitignored, re-randomized every init).