# HELLFORGE v1.0.0.0 ALPHA — Documentation Wiki

> **CORE-EXPANSION: REGAS | Signed: TENTARI**
>
> [GitHub](https://github.com/tentari/hellforge) | [SYNTAX.md](../SYNTAX.md) | [Quick Start](getting-started.md)

HELLFORGE is the E language ecosystem — a music composition language augmented with GPU shader math, Tensor Core acceleration, OpenGL/Vulkan graphics APIs, and 3D spatial audio. This wiki covers everything.

---

## Quick Links

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started.md) | Install, first composition, play your first note |
| [Samples](../samples/) | **35+ code snippets** — learn syntax from scratch with runnable .e files |
| [Syntax Reference](syntax/overview.md) | v1 Machine, v1 Human, v2 Semantic, v3 Shorthand |
| [Math & Variables](syntax/math-expressions.md) | `{$expr}`, `$var`, loops, functions |
| [Command Reference](commands/core-commands.md) | All core + plugin commands documented with examples |
| [Examples](../examples/) | Full compositions, game engine, GPU compute demos |

## Learning Path

Start with the [samples](../samples/01-basics/) in order:

| Step | Directory | What You'll Learn |
|------|-----------|-------------------|
| 1 | [01-basics/](../samples/01-basics/) | First notes, scales, velocity, timing |
| 2 | [02-machine/](../samples/02-machine/) | Machine mode: T N D V format |
| 3 | [03-human/](../samples/03-human/) | Human mode: play note/chord |
| 4 | [04-math/](../samples/04-math/) | $var, {$expr}, math functions |
| 5 | [05-loops/](../samples/05-loops/) | for, repeat, while loops |
| 6 | [06-chords/](../samples/06-chords/) | Chord progressions, arpeggios |
| 7 | [07-advanced/](../samples/07-advanced/) | Nested loops, modulo, BPM changes |
| 8 | [08-features/](../samples/08-features/) | Directives, comments, scale quantization |

## Plugins

| Plugin | Description | Docs |
|--------|-------------|------|
| [Radical](plugins/radical.md) | GPU Shader Math Core — GLSL compute shader evaluation | [README](../plugins/radical/__init__.py) |
| [TensorSHARP](plugins/tensorsharp.md) | NVIDIA Tensor Core acceleration (CuPy + CUDA) | [README](../plugins/tensorsharp/__init__.py) |
| [OPENapi](plugins/openapi.md) | Low-level OpenGL Graphics API | [README](../plugins/openapi/__init__.py) |
| [Vulkanizer](plugins/vulkanizer.md) | Low-level Vulkan API — Ray Tracing + Upscaling | [README](../plugins/vulkanizer/__init__.py) |
| [EAudio](plugins/eaudio.md) | 3D Spatial Audio API — DSP effects | [README](../plugins/eaudio/__init__.py) |
| [LURE](plugins/lure.md) | LuaJIT Runtime Accelerator | [README](../plugins/lure/__init__.py) |
| [Fentclient](plugins/fentclient.md) | Performance, bug fixes, security | [README](../plugins/fentclient/__init__.py) |
| [Portbaby](plugins/portbaby.md) | Syntax version converter | [README](../plugins/portbaby/__init__.py) |
| [Talisman](plugins/talisman.md) | Audio culling + privacy engine | [README](../plugins/talisman/__init__.py) |

## Topics

| Area | Docs |
|------|------|
| **Signing** | [Trust Model](signing/overview.md) · [REGAS Core](signing/regas-trust.md) · [TENTARI](signing/tentari-signing.md) · [Key Management](signing/key-management.md) · [Verification](signing/verification.md) |
| **Async** | [Async Compile](async/overview.md) · [LURE Async](async/lure-async.md) · [FC Async](async/fentclient-async.md) · [Radical Async](async/radical-async.md) |
| **GPU** | [GPU Overview](gpu/overview.md) · [Radical GPU](gpu/radical-gpu.md) · [OpenGL API](gpu/opengl-api.md) · [Vulkan API](gpu/vulkan-api.md) · [Tensor Cores](gpu/tensor-cores.md) · [Shader Compilation](gpu/shader-compilation.md) |
| **Audio** | [EAudio API](audio/eaudio-api.md) · [Spatial Audio](audio/spatial-audio.md) · [DSP Effects](audio/dsp-effects.md) · [Device Management](audio/device-management.md) |
| **Packaging** | [pkglist.json](packaging/pkglist.md) · [Plugin Management](packaging/plugin-management.md) · [Embedded Backups](packaging/embedded-backups.md) · [Signing Plugins](packaging/signing-plugins.md) |
| **Security** | [Trust Model](security/trust-model.md) · [Strict Enforcement](security/strict-enforcement.md) · [Identity](security/identity-management.md) · [Rate Limiting](security/rate-limiting.md) |
| **Backend** | [API Reference](backend/api-reference.md) · [OshoNet Integration](backend/oshonet-integration.md) · [Verification](backend/verification-endpoints.md) |

## Examples

| Example | Description |
|---------|-------------|
| [AAA Game Engine](../examples/opengl_engine.py) | Full game engine built on OPENapi + Vulkanizer + EAudio |
| [Custom Plugin](examples/custom-plugin.md) | How to write and sign your own plugin |
| [GPU Compute](examples/gpu-compute.md) | Using Radical for batch math evaluation |

## Command Reference

| Commands | Doc |
|----------|-----|
| **Core Shell** (cd, ls, compile, play, etc.) | [core-commands.md](commands/core-commands.md) |
| **Radical** (GPU shader math) | [radical-commands.md](commands/radical-commands.md) |
| **TensorSHARP** (Tensor Cores) | [tensorsharp-commands.md](commands/tensorsharp-commands.md) |
| **OPENapi** (OpenGL API) | [openapi-commands.md](commands/openapi-commands.md) |
| **Vulkanizer** (Vulkan API) | [vulkanizer-commands.md](commands/vulkanizer-commands.md) |
| **EAudio** (Audio API) | [eaudio-commands.md](commands/eaudio-commands.md) |
| **LURE** (LuaJIT accelerator) | [lure-commands.md](commands/lure-commands.md) |
| **Fentclient** (security, identity) | [fentclient-commands.md](commands/fentclient-commands.md) |
| **Portbaby** (syntax conversion) | [portbaby-commands.md](commands/portbaby-commands.md) |
| **Talisman** (audio culling) | [talisman-commands.md](commands/talisman-commands.md) |

## Examples

| Example | Description |
|---------|-------------|
| [lullaby.e](../examples/lullaby.e) | Complete lullaby composition (64 bars, C major) |
| [techno_beat.e](../examples/techno_beat.e) | Electronic pattern with loops and math modulation |
| [gpu_demo.e](../examples/gpu_demo.e) | GPU-accelerated math composition (100+ events) |
| [plugin_demo.e](../examples/plugin_demo.e) | Multi-plugin features demo |
| [opengl_engine.py](../examples/opengl_engine.py) | AAA game engine built on OPENapi+Vulkanizer+EAudio |

## Reference

- [Full Syntax Reference](../SYNTAX.md)
- [Troubleshooting Guide](faq.md)
- [FAQ](faq.md)
- [Contributing](contributing.md)
- [Changelog](changelog.md)

---

*HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS — Built with fury, forged in hell.*
