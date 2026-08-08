# **HELLFORGE v1.0.0.0 ALPHA — vulkanizer: Vulkan API**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [fentclient](fentclient.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**vulkanizer** provides a full Vulkan 1.3 API surface exposed through five sub-APIs. It integrates with radical for shader module creation and leverages tensorsharp for compute dispatch where beneficial.

## Sub-APIs

### Instance (`vulkanizer.instance`)

Instance and device creation with layer/extension enumeration, physical device selection (discrete GPU preference), and queue family discovery. Manages the `VkInstance` and `VkDevice` handles.

### Pipeline (`vulkanizer.pipeline`)

Pipeline layout, shader stage creation (from radical GLSL via `glslang` or SPIR-V), graphics pipeline, compute pipeline, and ray-tracing pipeline. Pipeline cache with disk serialization.

### Command (`vulkanizer.command`)

Command pool and buffer management, secondary command buffers, render pass barriers, and multi-threaded command recording. Automatic submission batching and timeline semaphore synchronization.

### Raytrace (`vulkanizer.raytrace`)

Top-level and bottom-level acceleration structure building, ray-tracing pipeline creation, shader binding tables, and `VK_KHR_ray_tracing` dispatch. Supports procedural and triangle geometry.

### Upscale (`vulkanizer.upscale`)

VK_KHR_fragment_shader_basic_interlock compute-based upscaler and FSR 2.2 integration. Temporal anti-aliasing and dynamic resolution scaling tied to frame budget feedback.

---

**API Reference:** `#include <vulkanizer/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — vulkanizer: Vulkan API**
