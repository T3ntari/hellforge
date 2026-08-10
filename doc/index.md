# HELLFORGE — Documentation Wiki

> **HELLFORGE OS v0.1.14.41-beta** | kernel `ep_core` · hypervisor K-rip v1.0.0 · 14 driver plugins
>
> [GitHub](https://github.com/tentari/hellforge) | [README](../README.md) | [SYNTAX.md](../SYNTAX.md) | [Getting Started](getting-started.md)

HELLFORGE is an **OS-like system** for composing music with the E language:
`ep_core` is the kernel (plugin API, boot chain, sandbox), every plugin is a
**driver**, and **K-rip** is the hypervisor that boots and sandboxes
everything. Write music as plain text — notes, chords, rhythms, dynamics —
and E turns it into `.mid`, `.wav`, `.mp3`, `.ec`, `.eic` output.

---

## Quick Links

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started.md) | Install, boot through K-rip, first composition |
| [Syntax Reference](syntax/overview.md) | **v5 is the canonical syntax**; v1–v4 are legacy |
| [Command Reference](commands/core-commands.md) | Core eshell + `run.py` commands |
| [K-rip Commands](commands/krip-commands.md) | The hypervisor: mem/cpu/gpu/sandbox/boot |
| [Integrity & Safe Mode](commands/integrity-commands.md) | X/Y digest, `run.py integrity`, SAFE MODE |
| [Plugin Overview](plugins/overview.md) | The 14 shipped driver plugins |
| [Security](security/trust-model.md) | Local-first integrity, opt-in network |

## The OS Layout

| Layer | What it is | Docs |
|-------|-----------|------|
| **Kernel** | `ep_core` — plugin API, boot steps, signing, sandbox | [plugins/overview](plugins/overview.md) |
| **Hypervisor** | **K-rip v1.0.0** — GRUB boot menu, resource sandbox, safe updates | [krip](plugins/krip.md) · [krip commands](commands/krip-commands.md) |
| **Drivers** | 14 plugins under `plugins/` | [plugin overview](plugins/overview.md) |
| **Console** | `eshell` — the interactive OS shell | [shell commands](syntax/shell-commands.md) |

## Plugins (drivers)

| Plugin | Description | Docs |
|--------|-------------|------|
| [K-rip](plugins/krip.md) | Hypervisor — boot manager, resource sandbox, safe updates | [commands](commands/krip-commands.md) |
| [HellGate](plugins/hellgate.md) | Boots OpenCode focused on the project (Music-Composer / Music-Refiner) | [README](../plugins/hellgate/README.md) |
| [LLM](plugins/llm.md) | AI copilot — ask/chat/fix/plugin, providers ollama/openai/anthropic/deepseek/custom | [commands](commands/llm-commands.md) |
| [Radical](plugins/radical.md) | GPU Shader Math Core — GLSL compute shader evaluation | [commands](commands/radical-commands.md) |
| [TensorSHARP](plugins/tensorsharp.md) | NVIDIA Tensor Core acceleration (CuPy, TF32/FP16) | [commands](commands/tensorsharp-commands.md) |
| [OPENapi](plugins/openapi.md) | Low-level OpenGL Graphics API | [commands](commands/openapi-commands.md) |
| [Vulkanizer](plugins/vulkanizer.md) | Low-level Vulkan API — ray tracing detection, upscaling | [commands](commands/vulkanizer-commands.md) |
| [EAudio](plugins/eaudio.md) | Low-level audio API — devices, buffers, 3D spatial, effects | [commands](commands/eaudio-commands.md) |
| [Humanize](plugins/humanize.md) | MoE performance feel — `@humanize:nn` micro-timing | — |
| [Talisman](plugins/talisman.md) | Audio culling, privacy & QOL engine | [commands](commands/talisman-commands.md) |
| [LURE](plugins/lure.md) | LuaJIT runtime accelerator (sync + async compile) | [commands](commands/lure-commands.md) |
| [Portbaby](plugins/portbaby.md) | Syntax version porting (`pb`) | [commands](commands/portbaby-commands.md) |
| [Learner](plugins/learner.md) | Interactive tutorial — lessons, questions, quizzes, tests | — |
| [Launcher](plugins/launcher.md) | New-window launching & process management | — |

The example reference plugin lives at [`examples/plugins/example_plugin.py`](../examples/plugins/example_plugin.py) — copy it to `plugins/` to start your own driver.

## Topics

| Area | Docs |
|------|------|
| **Commands** | [core](commands/core-commands.md) · [krip](commands/krip-commands.md) · [integrity](commands/integrity-commands.md) · [llm](commands/llm-commands.md) + per-plugin pages |
| **Security** | [Trust model](security/trust-model.md) · [Integrity (X/Y)](commands/integrity-commands.md) · [Strict enforcement](security/strict-enforcement.md) · [Identity](security/identity-management.md) · [Rate limiting](security/rate-limiting.md) |
| **Signing** | [Overview](signing/overview.md) · [TENTARI](signing/tentari-signing.md) · [REGAS](signing/regas-trust.md) · [Key management](signing/key-management.md) · [Verification](signing/verification.md) |
| **Syntax** | [Overview](syntax/overview.md) · [v5](syntax/overview.md) · [Directives](syntax/directives.md) · [Loops](syntax/loops.md) · [Math](syntax/math-expressions.md) · [Variables](syntax/variables.md) |
| **GPU** | [Overview](gpu/overview.md) · [Radical](gpu/radical-gpu.md) · [OpenGL API](gpu/opengl-api.md) · [Vulkan API](gpu/vulkan-api.md) · [Tensor Cores](gpu/tensor-cores.md) · [Shaders](gpu/shader-compilation.md) |
| **Audio** | [EAudio API](audio/eaudio-api.md) · [Spatial](audio/spatial-audio.md) · [DSP](audio/dsp-effects.md) · [Devices](audio/device-management.md) |
| **Async** | [Overview](async/overview.md) · [LURE async](async/lure-async.md) · [Fallback chain](async/radical-async.md) |
| **Packaging** | [pkglist.json](packaging/pkglist.md) · [Plugin management](packaging/plugin-management.md) · [Backups](packaging/embedded-backups.md) · [Signing plugins](packaging/signing-plugins.md) |
| **Examples** | [Custom plugin](examples/custom-plugin.md) · [GPU compute](examples/gpu-compute.md) · [Game engine](examples/game-engine.md) |

## Reference

- [Full Syntax Reference](../SYNTAX.md)
- [FAQ](faq.md) · [Contributing](contributing.md) · [Changelog](changelog.md)
- [HELLFORGE v5 tour](syntax/overview.md#version-5--canonical) — the canonical language

---

*HELLFORGE OS v0.1.14.41-beta — kernel `ep_core`, hypervisor K-rip, 14 drivers — built with fury, forged in hell.*
