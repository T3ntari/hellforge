**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [trust-model](trust-model.md) | [strict-enforcement](strict-enforcement.md) | [identity-management](identity-management.md) | [rate-limiting](rate-limiting.md)

## Strict Enforcement

`sys strict` (eshell) controls how strictly plugin/signing verification is
enforced:

### sys strict 0 — OFF (default)

Permissive. Unsigned plugins load freely.

### sys strict 1 — WARN

Unsigned plugins show a warning but still load.

### sys strict 2 — BLOCK

Unsigned plugins are rejected. This is the strongest enforcement level —
**still entirely local**, there is no server registry involved.

### Setting

```
sys strict 2          (in eshell)
sys strict            (show the current level)
```

### Relationship to the core digest

`sys strict` governs *plugin* signing policy. The **core integrity
sequence** (Technique X/Y, `run.py integrity`) is always active regardless
of the strict level — a flagged core never boots normally; it enters
SAFE MODE.

### Use cases

- `strict 0`: development and prototyping (default)
- `strict 1`: team/CI environments with local signing
- `strict 2`: locked-down deployments

---

See also: [Trust model](trust-model.md) · [Identity](identity-management.md) · [Signing](../signing/overview.md)