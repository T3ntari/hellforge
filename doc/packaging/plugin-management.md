**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [pkglist](pkglist.md) | [plugin-management](plugin-management.md) | [embedded-backups](embedded-backups.md) | [signing-plugins](signing-plugins.md)

## Plugin Management

Plugins are managed from the eshell console. Every command family takes
subcommands:

### plugin

```
plugin list            # installed plugins + versions
plugin avail           # available plugins
plugin scan            # re-scan the plugins directory
plugin update          # update plugin metadata
plugin fetch <name>    # fetch a plugin
plugin remove <name>   # remove a plugin
plugin version         # plugin manager version
```

### mod (mods — userland extensions)

```
mod list | avail | scan | update | fetch <name> | remove <name> | version
```

### pkglist (the package catalog)

```
pkglist show | update | search <q> | version | detail <name>
```

### ezip (packages)

```
ezip install <file.ezip> | ezip list
```

### Boot & sandbox

- At boot, the kernel loads every plugin under `plugins/` with real file
  counts: "Plugin X present (N files)" — plugins can be disabled per
  config; dependencies declared with `api.require()` install
  automatically
- `sys strict 0|1|2` controls unsigned-plugin policy (see
  [Strict enforcement](../security/strict-enforcement.md))
- Everything runs inside the K-rip sandbox (`krip sandbox run <name> -- <cmd>`
  for arbitrary processes)

### Custom plugins & updates

Custom plugin dirs (not shipped upstream) survive safe updates: they are
backed up, restored, and re-registered in `SECURITY_HASH.local` — see
[Safe updates](../commands/integrity-commands.md).

---

**HELLFORGE OS v0.1.14.41-beta** — plugin management