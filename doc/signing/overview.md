**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](signing/overview.md) | [regas-trust](signing/regas-trust.md) | [tentari-signing](signing/tentari-signing.md) | [key-management](signing/key-management.md) | [verification](signing/verification.md)

## Signing System Overview

The HELLFORGE signing system provides cryptographic trust for the Piano DSL ecosystem. It is built around four trust levels:

- **REGAS** — Registry-confirmed, highest trust. Key is verified through your private registry (opt-in).
- **TENTARI** — Third-party plugin signing using ed25519. Trusted but not server-confirmed.
- **UNKNOWN** — Signed with a key not in any trust store.
- **UNSIGNED** — No signature present.

The system enforces a strict enforcement policy (`sys strict 0|1|2`) that dictates whether unsigned or unknown packages are rejected at compile time.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**