**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [pkglist](packaging/pkglist.md) | [plugin-management](packaging/plugin-management.md) | [embedded-backups](packaging/embedded-backups.md) | [signing-plugins](packaging/signing-plugins.md)

## Embedded Backups

Piano DSL includes an embedded backup system for keys, configurations, and plugin data.

### JSON Backup

```
piano backup --all
piano backup --keys
piano backup --config
```

Backups are written as JSON files containing the full state of the selected subsystem. The JSON structure is human-readable and can be restored with:

```
piano restore --file backup.json
```

### ZIP Backup

```
piano backup --zip --output my_backup.zip
```

ZIP backups include the same data as JSON but additionally compress plugin binaries and shader caches. Ideal for transferring setups between machines.

### Automated Backups

Configure automatic backups:

```
piano config set backup.interval 24h
piano config set backup.destination ~/piano_backups
piano config set backup.include_keys true
```

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**