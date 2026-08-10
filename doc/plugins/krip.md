# K-rip — the HELLFORGE Hypervisor

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [krip](krip.md) | [commands](../commands/krip-commands.md)

---

## Overview

**K-rip v1.0.0** (plugin id `krip`, author Tentari) is the hypervisor layer
of HELLFORGE. It sandboxes the entire shell — boot, init and every plugin
run under it get a heavy resource layer on top of the existing plugin
sandbox: memory budgets (`RLIMIT_AS`), CPU caps + affinity, GPU selection
(single/multi/list/auto), the default graphics engine (Vulkan by default,
OpenGL supported), VulkanRT and Tensor support — all via the `krip`
command. Arbitrary processes can be sandboxed too.

## It is the main entry

Everything launches through K-rip:

```
krip                    GRUB menu -> boot kernel -> console (eshell)
krip run <cmd...>       run anything inside the sandbox
krip eshell|shell       the OS console inside the sandbox
krip hellgate           HellGate inside the sandbox
krip player <file>      the player inside the sandbox
krip status|help
```

`run.py` modes and direct `eshell.py` starts re-enter through K-rip
(`KRIP_INNER=1` marks children, `KRIP_BYPASS=1` escapes, `KRIP_NO_MENU=1`
skips the menu). Children inherit the GPU/engine/tensor environment, the
memory budget, CPU affinity and project-root confinement.

## The boot menu (GRUB-style)

Styled with the HELLFORGE banner art, a blue highlight bar for the
selection and mode chips (`[normal]` / `[safemode]`):

- 3-second countdown auto-boots the default kernel; any key stops it
- ↑/↓ select, Enter boots
- `c` — console (eshell), Ctrl+C — console
- `u` — safe update with an animated progress bar when a newer kernel
  exists on GitHub
- Esc — exit K-rip back to the terminal

A footer bar shows the key hints. Kernel entries come from the registry
`.e_identity/kernels.json`: the **current** kernel plus the **previous**
one (seeded from the git tag before the current version), each with a
normal and a safemode entry. Booting a previous kernel runs a safe update
to that tag — a bootable rollback.

## Resource sandbox

| Command | Effect |
|---------|--------|
| `krip mem <mb>` | memory budget, RLIMIT_AS **soft** limit |
| `krip cpu <n>` | CPU affinity to the first n threads |
| `krip gpu <auto\|list\|all\|0,1\|2 3>` | GPU selection; device lists set `CUDA_VISIBLE_DEVICES` (multi-GPU) |
| `krip engine <vulkan\|opengl>` | default graphics engine (vulkan default) |
| `krip vulkanrt <on\|off>` | Vulkan runtime support |
| `krip tensor <on\|off\|auto>` | tensor support |
| `krip sandbox run <name> -- <cmd...>` · `list` · `kill <name>` · `status` | sandbox arbitrary processes (RLIMITs + affinity + GPU env, tracked for kill) |

`krip os` prints the OS view: kernel (`ep_core` — plugin sandbox +
signing + directives), hypervisor (K-rip), drivers (the plugin dirs),
engine and tensor state. `krip kernels` lists the registry.

## Configuration

`krip.json` at the **project root** is the real config file
(`mem_mb`, `cpu_threads`, `gpu`, `engine`, `vulkanrt`, `tensor`,
`sandboxes`), read at initialization. Runtime-saved state and built-in
defaults merge, with the file winning.

- `krip config` — show path + values
- `krip edit` — open the file in `nano` (or `$KRIP_EDITOR`); saving
  auto-reloads K-rip **live** (a watcher re-applies memory/cpu/engine/gpu
  while the editor is open)
- `krip save` / `krip reload` / `krip reset` — persist / re-read / reset

## Safe updates

The menu's `u` key (or the post-boot safe-update prompt) updates to the
GitHub version tag with a progress bar, **preserving everything**: custom
plugins, mods, `.plugin_config.json`, `.env`, `.e_identity` are backed up
and restored, the previous kernel is snapshotted into the registry as a
rollback target, and custom plugin dirs are registered in
`SECURITY_HASH.local`. See [Integrity & safe mode](../commands/integrity-commands.md).

## Boot steps

At kernel boot, K-rip reports:
"K-rip: hypervisor armed from krip.json (mem …, cpu …, gpu …, engine …)"
and "HELLFORGE OS: kernel ep_core · N drivers · hypervisor K-rip v1.0.0".

---

See also: [K-rip commands](../commands/krip-commands.md) · [Integrity & safe mode](../commands/integrity-commands.md)
