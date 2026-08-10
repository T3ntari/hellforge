**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [regas-trust](regas-trust.md) | [tentari-signing](tentari-signing.md) | [key-management](key-management.md) | [verification](verification.md)

## Key Management

### Key generation

```
sign --setup
```

Generates an ED25519 keypair for this machine. Everything lives under
`.e_identity/` (gitignored):

- `.e_identity/identity.json` — name, public key, social metadata
- `.e_identity/secret.key` — the private seed (never committed)
- `.e_identity/trusted/` — trusted public keys for verifying others

### Trusting keys

Import a peer's public key into `.e_identity/trusted/` to verify their
signatures locally. There is no key server — trust is a personal,
per-machine decision.

### Backup

`.e_identity/` holds your identity. Back it up yourself if you want to
keep it across machines (copy the directory or export the seed); keep the
private key offline when not signing. The safe updater **preserves**
`.e_identity/` across version updates.

### Rotation

Re-run `sign --setup` to create a new identity. Old trusted keys remain in
`.e_identity/trusted/` for verifying previously signed files.

### What is NOT here

- No passphrase-encrypted keystore, no HSM integration, no server-side
  key registry. The model is deliberately simple and local.