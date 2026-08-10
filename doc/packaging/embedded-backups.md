**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [pkglist](pkglist.md) | [plugin-management](plugin-management.md) | [embedded-backups](embedded-backups.md) | [signing-plugins](signing-plugins.md)

## Embedded Backups

HELLFORGE protects your data in two ways: **safe updates** (kernel-level)
and **Talisman auto-backup** (plugin-level).

### Safe update backup (kernel-level)

Before any update, `ep_compiler/update.py` copies your data out of the
way into `.backup_update/` and restores it after the checkout:

- `.plugin_config.json` — plugin configuration (LLM keys, settings)
- `.env` — your environment (provider keys, HF_* vars)
- `.e_identity/` — identity, trusted keys, kernel registry, X/Y store
- `mods/` — userland mods
- `SECURITY_HASH.local` — the local manifest extension
- custom plugin dirs under `plugins/`

Then uncommitted work is stashed and popped back. Nothing is lost —
`u` in the boot menu, the post-boot prompt, and booting a previous kernel
all use this path. See [Integrity & safe mode](../commands/integrity-commands.md).

### Talisman auto-backup (plugin-level)

With `talisman backup on`, every compile snapshots the rendered event set
to timestamped JSON under `.e_backups/`:

```
talisman backup on     # enable auto-backup
talisman backup off    # disable
```

### Restoring

- After a safe update: automatic (backup → checkout → restore)
- Kernel registry rollback: boot the previous kernel from the K-rip menu
  (`krip kernels` lists the registry)
- Event snapshots: `.e_backups/compile_<timestamp>.json`

---

**HELLFORGE OS v0.1.14.41-beta** — backups