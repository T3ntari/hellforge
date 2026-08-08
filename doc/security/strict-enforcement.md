**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [trust-model](security/trust-model.md) | [strict-enforcement](security/strict-enforcement.md) | [identity-management](security/identity-management.md) | [rate-limiting](security/rate-limiting.md)

## Strict Enforcement

The `sys strict` directive controls how strictly the compiler enforces signature verification.

### sys strict 0

Permissive. Unsigned and unknown packages are allowed with a warning. Only explicitly blacklisted packages are rejected.

### sys strict 1

Moderate. Unknown signatures produce an error. Unsigned packages produce a warning. TENTARI and REGAS packages are accepted without issue.

### sys strict 2

Absolute. Only REGAS-signed packages are accepted. Any unsigned, unknown, or TENTARI package produces a hard error and compilation halts.

### Setting

```
// In Piano DSL source
sys strict 1

// Or via CLI
piano compile --strict 2
```

### Use Cases

- `strict 0`: Development and prototyping
- `strict 1`: Team/CI environments
- `strict 2`: Production and distribution builds

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**