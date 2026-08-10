# Vulkanizer — Low-Level Vulkan API

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [commands](../commands/vulkanizer-commands.md)

---

## Overview

**Vulkanizer v1.0.0** (author Tentari) is a low-level **Vulkan** graphics &
compute API — not a game engine. It provides the raw Vulkan building blocks
for game engines and rendering pipelines. Requires Radical for GPU
detection; `pip install vulkan glfw` + Vulkan SDK 1.2+.

## Core primitives

- **Instance** — Vulkan instance, physical device selection, logical
  device, queues
- **Pipeline** — compute/graphics pipelines, shader modules, descriptor
  sets, push constants
- **Buffer** — device-local, host-visible, staging, buffer barriers
- **Command** — command pools, command buffers, submit, sync (semaphores,
  fences)
- **RayTrace** — `VK_KHR_ray_tracing` capability detection
- **Upscale** — custom temporal upscaling via compute shaders + Tensor
  Cores

Example engine: `examples/vulkan_engine.py`.

## Commands

`vulkanizer status|devices|info` — see
[Vulkanizer commands](../commands/vulkanizer-commands.md).
