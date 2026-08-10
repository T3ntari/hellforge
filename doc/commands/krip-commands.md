# K-rip — Hypervisor Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [krip-commands](krip-commands.md) | [integrity-commands](integrity-commands.md)

K-rip (plugin id `krip`, **v1.0.0**) is the HELLFORGE hypervisor. It boots
the OS (GRUB-style menu), sandboxes every process (memory, CPU, GPU,
graphics engine), manages the kernel registry, and performs safe updates.
Configuration lives in **`krip.json`** at the project root, read at
initialization.

## Entry points

```bash
run.py krip                        # GRUB menu -> boot kernel -> console
run.py krip run <cmd...>           # run anything inside the sandbox
run.py krip eshell|shell|console   # the OS console inside the sandbox
run.py krip hellgate               # HellGate inside the sandbox
run.py krip player <file>          # the player inside the sandbox
run.py krip status|help
```

All other launch paths (any `run.py` mode, direct `eshell.py`) re-enter
through K-rip. Children get `KRIP_INNER=1` (no re-wrap) plus the memory
budget, CPU affinity, and GPU/engine/tensor environment. `KRIP_BYPASS=1`
escapes the wrapper entirely.

## The boot menu (GRUB-style)

- **3s countdown** auto-boots the default kernel; any key stops it
- **↑/↓** select · **Enter** boots
- **c** drops to the console (eshell)
- **u** safe update (progress bar) when a newer kernel exists on GitHub
- **Esc** exits K-rip back to the terminal
- Styled: banner art, blue highlight bar, mode chips (`[normal]`/`[safemode]`)
- `KRIP_NO_MENU=1` boots straight to the console

## krip status
**Syntax:** `krip status`
**Description:** Show the current allocation: memory (MB), cpu threads, GPU selection → visible devices, engine, VulkanRT, tensor, plus running sandboxes.
**Example:** `krip status`

## krip mem
**Syntax:** `krip mem <mb>`
**Description:** Set the memory budget (RLIMIT_AS, **soft** limit so it can be raised back).
**Example:** `krip mem 2048`

## krip cpu
**Syntax:** `krip cpu <n>`
**Description:** Cap CPU threads via affinity to the first n CPUs.
**Example:** `krip cpu 4`

## krip gpu
**Syntax:** `krip gpu <auto|list|all|0,1|2 3>`
**Description:** GPU selection. `list` shows detected GPUs; a device list like `0,1` or `2 3` sets `CUDA_VISIBLE_DEVICES` for every spawned process (multi-GPU).
**Example:** `krip gpu 0,1`

## krip engine
**Syntax:** `krip engine <vulkan|opengl>`
**Description:** Set the default graphics engine (Vulkan by default).
**Example:** `krip engine opengl`

## krip vulkanrt
**Syntax:** `krip vulkanrt <on|off>`
**Description:** Toggle Vulkan runtime support.
**Example:** `krip vulkanrt on`

## krip tensor
**Syntax:** `krip tensor <on|off|auto>`
**Description:** Toggle tensor support.
**Example:** `krip tensor auto`

## krip sandbox
**Syntax:** `krip sandbox run <name> -- <cmd...>` · `krip sandbox list|status` · `krip sandbox kill <name>`
**Description:** Run an arbitrary command in a K-rip sandbox (project-root confined, memory/CPU/GPU limits applied) and track it for list/kill.
**Example:** `krip sandbox run render -- python3 player.py song.mid`

## krip os
**Syntax:** `krip os`
**Description:** The OS view — kernel (`ep_core`), hypervisor (K-rip v1.0.0), drivers (plugin dirs), engine + tensor state.
**Example:** `krip os`

## krip kernels
**Syntax:** `krip kernels`
**Description:** List the installed kernels from the registry (`.e_identity/kernels.json`): current + previous versions, normal/safemode pairs.
**Example:** `krip kernels`

## krip edit
**Syntax:** `krip edit`
**Description:** Open `krip.json` in `nano` (or `$KRIP_EDITOR`). Saving the file **auto-reloads K-rip live** (memory/cpu/gpu/engine re-applied while the editor is open).
**Example:** `krip edit`

## krip config / save / reload / reset
**Syntax:** `krip config` · `krip save` · `krip reload` · `krip reset`
**Description:** Show the config file path + current values; persist the current allocation to `krip.json`; reload from disk and re-apply; reset to defaults and save.
**Example:** `krip config`

## krip boot
**Syntax:** `krip boot`
**Description:** Run the boot menu manually.
**Example:** `krip boot`

---

See also: [K-rip plugin page](../plugins/krip.md) · [Safe updates](../plugins/krip.md#safe-updates) · [Integrity & safe mode](integrity-commands.md)
