**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](signing/overview.md) | [regas-trust](signing/regas-trust.md) | [tentari-signing](signing/tentari-signing.md) | [key-management](signing/key-management.md) | [verification](signing/verification.md)

## Verification Flow

Signature verification happens at compile time before any Piano DSL code is processed.

### Flow

1. Package manifest is hashed with SHA-512
2. `.sig` file is loaded and the embedded signature is extracted
3. Public key is resolved from keystore, embedded key, or server
4. `ed25519.Verify(publicKey, hash, signature)` is called
5. Trust level (REGAS/TENTARI/UNKNOWN/UNSIGNED) is assigned
6. Enforcement policy (`sys strict`) determines acceptance

### .sig File Anatomy

```
{
  "version": 1,
  "algorithm": "ed25519",
  "fingerprint": "a1b2c3d4...",
  "signature": "base64-encoded-signature",
  "timestamp": "2026-07-30T19:00:00Z",
  "key_source": "local|server|embedded"
}
```

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**