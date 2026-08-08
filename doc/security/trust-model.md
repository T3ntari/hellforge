**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [trust-model](security/trust-model.md) | [strict-enforcement](security/strict-enforcement.md) | [identity-management](security/identity-management.md) | [rate-limiting](security/rate-limiting.md)

## Trust Model

The HELLFORGE trust model defines four levels of package trust:

### REGAS (Level 3)

Server-confirmed identity. The developer's key has been submitted and verified by the oshonet.in backend. Maximum trust.

### TENTARI (Level 2)

Third-party trusted. The developer's key is in the local keystore or community trust network. Trusted but not server-confirmed.

### UNKNOWN (Level 1)

The package is signed but the signing key is not in any trust store. The signature can be verified cryptographically but the identity is unverified.

### UNSIGNED (Level 0)

No signature is present. Trust is based solely on the source and distribution channel.

### Trust Resolution

When a package is loaded, the runtime resolves its trust level by checking:

1. Server REGAS registry
2. Local keystore
3. Embedded public key
4. Absence of signature

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**