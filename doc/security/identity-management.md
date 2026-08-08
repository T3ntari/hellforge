**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [trust-model](security/trust-model.md) | [strict-enforcement](security/strict-enforcement.md) | [identity-management](security/identity-management.md) | [rate-limiting](security/rate-limiting.md)

## Identity Management

### Setup

```
piano sign --setup
```

Walks through key generation, keystore initialization, and optional REGAS registration.

### Login

```
piano sign --login
```

Optionally authenticates with your private registry using your signing key. Creates a session token for subsequent server interactions.

### Key Management

- `piano sign --list` -- Show all keys in the keystore
- `piano sign --export <fingerprint>` -- Export a public key
- `piano sign --import <keyfile>` -- Import a trusted public key
- `piano sign --revoke <fingerprint>` -- Revoke a compromised key

### Sessions

Sessions are cached tokens that allow authenticated communication with the private registry without re-entering credentials.

```
piano sign --session-status
piano sign --logout
```

### REGAS Submission

```
piano sign --submit-regas
```

Submits your key fingerprint for REGAS review. Status can be checked with:

```
piano sign --regas-status
```

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**