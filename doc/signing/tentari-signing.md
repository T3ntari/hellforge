**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](signing/overview.md) | [regas-trust](signing/regas-trust.md) | [tentari-signing](signing/tentari-signing.md) | [key-management](signing/key-management.md) | [verification](signing/verification.md)

## TENTARI Signing

TENTARI signing is the mechanism for third-party plugin authors to cryptographically sign their Piano DSL packages using ed25519.

### How It Works

- A plugin author generates an ed25519 key pair
- The private key signs the package manifest
- The public key is embedded in the package or published to a key server
- Consumers verify the signature against the public key

### TENTARI vs REGAS

| Aspect | TENTARI | REGAS |
|---|---|---|
| Server confirmation | No | Yes |
| Trust scope | Local/community | Global |
| Strict level required | 1 | 2 |
| Key storage | Local keystore | Server registry |

TENTARI is the recommended starting point for plugin authors before pursuing REGAS status.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**