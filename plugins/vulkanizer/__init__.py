"""Vulkanizer v1.0.0 — Low-level Vulkan Graphics & Compute API.
Not a game engine. Provides the raw Vulkan building blocks that game engines
and rendering pipelines are built on top of.

Core primitives:
- Instance: Vulkan instance, physical device selection, logical device, queues
- Pipeline: compute/graphics pipelines, shader modules, descriptor sets, push constants
- Buffer: device-local, host-visible, staging, buffer barriers
- Command: command pools, command buffers, submit, sync (semaphores, fences)
- RayTrace: VK_KHR_ray_tracing capability detection
- Upscale: custom temporal upscaling via compute shaders + Tensor Cores

Third-party modders build game engines ON TOP of this API.
Example engine in examples/vulkan_engine.py

Install: pip install vulkan glfw  (requires Vulkan SDK 1.2+)"""

VERSION = "1.0.0"
author = "Tentari"
description = "Low-level Vulkan API — instance, pipeline, buffers, commands, ray tracing, upscaling"

_api = None


def register(api):
    api.add_boot_step(f"Vulkanizer v{VERSION}", "loading")
    global _api

    # Require Radical for GPU detection
    api.require("Radical")

    try:
        from ._instance import VkInstance
        inst = VkInstance()
        if inst.available:
            from ._api import VulkanAPI
            _api = VulkanAPI(inst)
            api.set_config("vulkanizer_available", True)
            api.add_command("vulkanizer", _cmd, "Vulkanizer: vulkanizer status|devices|info")
            api.add_help_section("Vulkanizer (Vulkan API)", [
                "vulkanizer status        Instance + GPU + device status",
                "vulkanizer devices       List physical devices",
                "vulkanizer info          Extensions + raytrace + upscale info",
                "",
                "Low-level Vulkan library the Ninja game engine is built on:",
                "instance/device selection, logical device + queues, buffers,",
                "descriptors, compute pipelines (SPIR-V), dispatch + sync.",
                "Third-party game engines are built on top of this API.",
            ])
            gpu = inst.gpu_info
            api.add_boot_step(
                f"Vulkanizer: Vulkan {gpu.get('vulkan_version', '1.0')} active ({gpu.get('name', 'Unknown GPU')})",
                "done"
            )
        else:
            api.set_config("vulkanizer_available", False)
            api.add_boot_step(f"Vulkanizer: unavailable ({inst.diagnostic})", "skip")
            api.add_command("vulkanizer", _cmd, "Vulkanizer: vulkanizer status|info")
    except Exception as e:
        api.set_config("vulkanizer_available", False)
        api.add_boot_step(f"Vulkanizer: init failed ({e})", "skip")
        api.add_command("vulkanizer", _cmd, "Vulkanizer: vulkanizer status|info")


def get_api():
    """Get the Vulkan API instance. Returns VulkanAPI or None."""
    return _api


def _cmd(args):
    if not args or args[0] == "status":
        if _api and _api.available:
            inst = _api.instance
            g = inst.gpu_info
            print(f"  Vulkanizer v{VERSION} — Vulkan API")
            print(f"  GPU: {g.get('name', 'Unknown')}")
            print(f"  Vulkan: {g.get('vulkan_version', 'N/A')}")
            print(f"  Driver: {g.get('driver_version', 'N/A')}")
            print(f"  Compute queues: {g.get('async_compute', 0)}")
            print(f"  Ray tracing: {'yes' if _api.raytrace.available else 'no'}")
            print(f"  Game engines can be built on this API")
        else:
            print(f"  Vulkanizer v{VERSION}")
            print(f"  Status: inactive")
            print(f"  Install: pip install vulkan glfw + Vulkan SDK")

    elif args[0] == "devices":
        if _api and _api.available:
            inst = _api.instance
            g = inst.gpu_info
            print(f"  Vulkan Device:")
            print(f"    Name: {g.get('name', 'Unknown')}")
            print(f"    Vendor: {g.get('vendor', 'Unknown')}")
            print(f"    Vulkan: {g.get('vulkan_version', 'N/A')}")
            print(f"    Driver: {g.get('driver_version', 'N/A')}")
            print(f"    Compute: {g.get('async_compute', 0)} queues")
            exts = g.get('extensions', [])
            rt_exts = [e for e in exts if 'ray_tracing' in e]
            if rt_exts:
                print(f"    Ray tracing extensions: {len(rt_exts)}")
                for e in rt_exts[:5]:
                    print(f"      {e}")

    elif args[0] == "info":
        print(f"  Vulkanizer v{VERSION} — Low-level Vulkan API")
        print(f"  Provides raw Vulkan primitives for building game engines:")
        print(f"    - VkInstance: device, queues, extensions")
        print(f"    - PipelineAPI: compute/graphics pipelines, descriptors")
        print(f"    - BufferAPI: device buffers, staging, barriers")
        print(f"    - CommandAPI: pools, buffers, submit, sync")
        print(f"    - RayTraceAPI: VK_KHR_ray_tracing capability probe")
        print(f"    - UpscaleAPI: temporal upscaling via compute + Tensor Cores")
        if _api and _api.available:
            print(f"  API status: active — build your engine on top!")
    else:
        print(f"  Usage: vulkanizer status|devices|info")
