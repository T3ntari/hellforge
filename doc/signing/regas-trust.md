**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](signing/overview.md) | [regas-trust](signing/regas-trust.md) | [tentari-signing](signing/tentari-signing.md) | [key-management](signing/key-management.md) | [verification](signing/verification.md)

## CORE-EXPANSION: REGAS Trust

REGAS is the highest trust level in the HELLFORGE signing hierarchy. A REGAS signature indicates the plugin author's identity has been confirmed by the private registry (opt-in).

### Characteristics

- Server-confirmed TENTARI identity
- Key fingerprint registered in the global REGAS registry
- Eligible for `sys strict 2` enforcement without warnings
- Automatic trust propagation across projects

### Workflow

1. Developer generates an ed25519 key pair locally
2. Key fingerprint is submitted to the registry (`/verify`)
3. Registry reviews and confirms via `/confirm`
4. Plugin signed with the confirmed key is marked REGAS
5. Downstream consumers see REGAS trust automatically

REGAS trust is the gold standard for distribution. All official HELLFORGE packages are REGAS-signed.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**