**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [pkglist](packaging/pkglist.md) | [plugin-management](packaging/plugin-management.md) | [embedded-backups](packaging/embedded-backups.md) | [signing-plugins](packaging/signing-plugins.md)

## How to Sign Plugins for Distribution

### Step 1: Generate a Key

```
piano sign --generate
```

### Step 2: Sign Your Plugin

```
piano sign --plugin ./my-plugin.pkg
```

This creates a `my-plugin.pkg.sig` file alongside the package.

### Step 3: Publish

Upload both the `.pkg` and `.sig` files to your distribution channel. Users will automatically verify the signature upon installation.

### Level Up: REGAS

To achieve REGAS trust:

1. Submit your key fingerprint to the oshonet.in registry
2. Await server review and confirmation
3. Once confirmed, your signatures will be recognized as REGAS globally

```
piano sign --submit-regas
```

### Best Practices

- Keep private keys offline when not signing
- Use a hardware security key for production plugin signing
- Rotate keys annually or after any suspected compromise
- Always verify signatures before publishing

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**