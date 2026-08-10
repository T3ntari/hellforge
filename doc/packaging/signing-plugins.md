**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [pkglist](pkglist.md) | [plugin-management](plugin-management.md) | [embedded-backups](embedded-backups.md) | [signing-plugins](signing-plugins.md)

## Signing Plugins for Distribution

Signing is **optional and opt-in** — it must never be made mandatory.
There is no registry to submit to; trust is local and personal.

### Step 1: Set up your identity (once)

```
sign --setup
```

Creates the local ED25519 keypair under `.e_identity/` (gitignored).
See [Key Management](../signing/key-management.md).

### Step 2: Sign files

```
sign <file>
```

Signs a file with your local identity (author metadata embedded). Verify
locally via `ep_core`'s `verify_signature`.

### Step 3: Publish

Plugins live in `plugins/<name>/` in the repo. For distribution:

1. Add the plugin's **SHA-256 verification code** to `pkglist.json`
   (see [pkglist](pkglist.md)) so `tools/verify_integrity.py` checks it
2. Optionally set `sys strict 1|2` on the consumer side to warn/block
   unsigned plugins (see
   [Strict enforcement](../security/strict-enforcement.md))

### Best practices

- Keep the private seed offline when not signing
- Back up `.e_identity/` yourself (the safe updater preserves it, but it
  is your machine's identity)
- Sign release files with `sign <file>` if you want the `sys strict`
  protections
- Publish hashes: the pkglist verification code is the distribution
  proof, not a server signature

### What was removed

The old server-side REGAS submission flow (`--submit-regas`, `/verify`,
`/confirm` endpoints) is **gone** from the open-source release — registry
auth is not part of the project. See [REGAS trust](../signing/regas-trust.md).