**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](signing/overview.md) | [regas-trust](signing/regas-trust.md) | [tentari-signing](signing/tentari-signing.md) | [key-management](signing/key-management.md) | [verification](signing/verification.md)

## Key Management

### Key Generation

```
piano sign --generate
```

Generates an ed25519 key pair in `~/.piano/keys/`. The private key is encrypted at rest with a user-chosen passphrase.

### Storage

- **Private key**: `~/.piano/keys/<fingerprint>.key` (encrypted)
- **Public key**: `~/.piano/keys/<fingerprint>.pub`
- **Keystore**: `~/.piano/keystore.json` (trusted public key registry)

### Backup

Use the embedded backup system:

```
piano backup --keys
```

This exports keys into a JSON structure that can be restored later. For critical keys, export to a hardware security module or offline storage.

### Rotation

Keys can be rotated with `piano sign --rotate`. Old keys remain in the trust store for verification of previously signed packages.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**