**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [pkglist](packaging/pkglist.md) | [plugin-management](packaging/plugin-management.md) | [embedded-backups](packaging/embedded-backups.md) | [signing-plugins](packaging/signing-plugins.md)

## Plugin Management

### Install

```
piano pkg install plugin-name
piano pkg install ./path/to/plugin.pkg
```

Installation resolves dependencies, verifies signatures, and places files in the Piano DSL plugin directory.

### Update

```
piano pkg update plugin-name
piano pkg update --all
```

Updates check the registry for newer versions, verify the new signature, and apply the update atomically.

### Remove

```
piano pkg remove plugin-name
```

Removal deletes plugin files and updates the local registry. Dependencies shared with other plugins are preserved.

### List

```
piano pkg list
```

Shows installed plugins with version, trust level, and verification status.

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**