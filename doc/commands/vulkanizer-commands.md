# HELLFORGE — Vulkanizer Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [vulkanizer-commands](vulkanizer-commands.md)

The **vulkanizer** plugin (v1.0.0) is a low-level **Vulkan graphics &
compute API** — instance, pipelines, buffers, commands, ray-tracing
capability detection, custom temporal upscaling. Depends on Radical for GPU
detection. Requires `pip install vulkan glfw` + Vulkan SDK 1.2+.

## vulkanizer status
**Syntax:** `vulkanizer status`
**Description:** GPU name, Vulkan version, driver version, async compute queues, ray-tracing availability — or "inactive" with install hints.
**Example:** `vulkanizer status`

## vulkanizer devices
**Syntax:** `vulkanizer devices`
**Description:** Enumerate Vulkan-capable physical devices with details.
**Example:** `vulkanizer devices`

## vulkanizer info
**Syntax:** `vulkanizer info`
**Description:** Describe the sub-APIs: Instance, Pipeline (compute/graphics, shader modules, descriptors, push constants), Command (pools, buffers, submit, sync), RayTrace (VK_KHR_ray_tracing), Upscale (compute-based temporal upscaling).
**Example:** `vulkanizer info`

---

**Plugin:** vulkanizer · see [Vulkanizer plugin page](../plugins/vulkanizer.md) and [GPU docs](../gpu/vulkan-api.md)
