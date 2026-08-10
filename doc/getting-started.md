**HELLFORGE OS v0.1.14.41-beta** — [index](index.md) | [getting-started](getting-started.md) | [contributing](contributing.md) | [changelog](changelog.md) | [faq](faq.md)

## Getting Started

### Installation

Requires Python 3.10+ and a checkout of the repository:

```bash
python -m venv .venv
.venv/bin/pip install numpy mido scipy pygame pydub psutil
```

Optional accelerators: `lupa` (LURE LuaJIT engine), `PyOpenGL`/`glfw` (GPU),
`vulkan` (Vulkanizer), `cupy-cuda12x` (TensorSHARP). Everything degrades
gracefully when an accelerator is missing.

### Boot: everything launches through K-rip

HELLFORGE behaves like an OS — `ep_core` is the kernel, plugins are drivers,
and **K-rip** is the hypervisor. Every launch path re-enters through it
(children are marked `KRIP_INNER=1`; `KRIP_BYPASS=1` escapes it):

```bash
.venv/bin/python run.py krip          # GRUB-style menu -> boot kernel -> console
```

The boot menu shows the HELLFORGE banner with a blue highlight bar, kernel
entries for the **current** and **previous** versions (normal + safe mode),
and a footer bar:

- **3s countdown** auto-boots the default kernel — any key stops it
- **↑/↓** select · **Enter** boots
- **c** drops to the console (eshell)
- **u** runs a **safe update** (with progress bar) when a newer kernel
  exists on GitHub — nothing is lost
- **Esc** exits K-rip back to the terminal

Once booted you land in **eshell**, the console — every start also runs the
integrity sequence first (see [Integrity](commands/integrity-commands.md)).

### The console (eshell)

```text
> compile songs/aurora_nocturne.e -o aurora.mid
> play songs/aurora_nocturne.e
> stats songs/aurora_nocturne.e
> help
```

`help` lists the built-in commands, then plugin-authored help sections
(plain lines or `(cmd, desc)` pairs), then every plugin command grouped by
its registering plugin — aliases are marked `(alias)` and dimmed. See
[Core Commands](commands/core-commands.md) and
[Shell Commands](syntax/shell-commands.md).

### K-rip resource sandbox

The hypervisor applies a heavy resource layer to every process it spawns —
configure it live and persist it to `krip.json` at the project root:

```bash
run.py krip mem 2048        # memory budget (RLIMIT_AS, soft)
run.py krip cpu 4           # CPU affinity (first 4 threads)
run.py krip gpu list        # show detected GPUs
run.py krip gpu 0,1         # multi-GPU via CUDA_VISIBLE_DEVICES
run.py krip engine vulkan   # default graphics engine (vulkan|opengl)
run.py krip vulkanrt on
run.py krip tensor on
run.py krip sandbox run foo -- <cmd...>   # sandbox any process
run.py krip os              # OS view: kernel / hypervisor / drivers
run.py krip edit            # edit krip.json in nano (KRIP_EDITOR); LIVE auto-reload on save
run.py krip config|save|reload|reset
```

See [K-rip commands](commands/krip-commands.md) and the
[K-rip plugin](plugins/krip.md) page.

### `run.py` modes

```bash
run.py play <file> [--gui] [--window] [--detach]
run.py compile <file> -o <out> [--to v5]
run.py check <file>                 # v5-aware linter (pure v5 file -> at most I001)
run.py new <name>                   # scaffold a v5 project
run.py stats|tracks|inspect <file>  # analysis
run.py transpose|tempo|merge <f>    # editing helpers
run.py shell                        # console in a new window
run.py ai <ask|chat|fix|plugin>     # LLM copilot
run.py hellgate                     # HellGate -> OpenCode in this repo
run.py krip                         # the hypervisor entry
```

### Verifying integrity

```bash
run.py integrity              # local: per-file SHA-512 manifest + 160-byte
                              # aggregate (SHA-256+SHA-512+BLAKE2b-512) vs
                              # the committed SECURITY_HASH.txt
run.py integrity --github     # also compare against the live GitHub copy
```

Boot runs this automatically: **Technique X** (rotating hidden digest
fragments, offline proof) first, then — when online — **Technique Y** (the
per-version key hash verified against GitHub at the version tag). Failures
drop you into **SAFE MODE**. Details:
[Integrity & Safe Mode](commands/integrity-commands.md).

### LLM providers (opt-in)

No credentials are bundled. Set your own in `.env` (copy from
`.env.example`): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`,
`OPENROUTER_API_KEY`, `GEMINI_API_KEY`, or use **Ollama** locally
(`ollama serve` running — it is listed last by design). Configure through
the shell or `run.py ai`:

```bash
run.py ai provider ollama
run.py ai model
run.py ai ask "What is a polyrhythm?"
```

HellGate (`run.py hellgate`) offers the same provider registry plus the
`$provider` / `$model` / `$agent` session commands.

### Your first v5 composition

```e
@bpm 120
play note(C4) @dur:q @vel:mf
play note(E4) @dur:q @vel:mf
play note(G4) @dur:h @vel:ff
```

Compile it, play it. The full language reference is in
[SYNTAX.md](../SYNTAX.md); a complete example piece ships at
`songs/aurora_nocturne.e`. **v5 is the canonical syntax** — v1–v4 sources
still compile with deprecation warnings; convert them with
`run.py compile <old.e> --to v5`.

### Next steps

- [Syntax overview](syntax/overview.md) — the v5 language
- [Plugins](plugins/overview.md) — the 14 drivers
- [Security](security/trust-model.md) — the local-first integrity model
- [FAQ](faq.md)

---

**HELLFORGE OS v0.1.14.41-beta** — kernel `ep_core` · hypervisor K-rip v1.0.0
