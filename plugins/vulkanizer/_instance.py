"""Vulkanizer VkInstance — Vulkan instance, physical device, logical device, queue management."""

import ctypes
import os


class VkInstance:
    """Vulkan instance and device management. Lowest layer."""

    def __init__(self):
        self.available = False
        self.diagnostic = ""
        self.gpu_info = {
            "name": "Unknown", "vendor": "Unknown",
            "vulkan_version": "N/A", "driver_version": "N/A",
            "api_version": "N/A", "async_compute": 0,
            "extensions": [],
        }
        self.instance = None
        self.physical_device = None
        self._init()

    def _init(self):
        try:
            from . import _vk as vk

            app_info = vk.VkApplicationInfo(
                sType=vk.VK_STRUCTURE_TYPE_APPLICATION_INFO,
                pApplicationName="Vulkanizer",
                applicationVersion=vk.VK_MAKE_VERSION(1, 0, 0),
                pEngineName="E Shell",
                engineVersion=vk.VK_MAKE_VERSION(1, 0, 0),
                apiVersion=vk.VK_MAKE_VERSION(1, 3, 0),
            )

            created = False
            for _major, _minor, _patch in ((1, 3, 0), (1, 2, 0), (1, 0, 0)):
                try:
                    app_info.apiVersion = vk.VK_MAKE_VERSION(_major, _minor, _patch)
                    self.instance = vk.vkCreateInstance(
                        vk.VkInstanceCreateInfo(
                            sType=vk.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                            pApplicationInfo=app_info,
                        )
                    )
                    created = True
                    break
                except Exception:
                    continue
            if not created:
                raise RuntimeError("vkCreateInstance failed on all API versions")

            devices = vk.vkEnumeratePhysicalDevices(self.instance)
            if not devices:
                self.diagnostic = "No Vulkan physical devices"
                self._cleanup()
                return

            best = None
            best_score = -1
            for pd in devices:
                props = vk.vkGetPhysicalDeviceProperties(pd)
                score = 0
                if props.deviceType == vk.VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU:
                    score = 100
                elif props.deviceType == vk.VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU:
                    score = 50
                qfs = vk.vkGetPhysicalDeviceQueueFamilyProperties(pd)
                compute_qs = sum(1 for qf in qfs if qf.queueFlags & vk.VK_QUEUE_COMPUTE_BIT)
                if compute_qs:
                    score += 10 * compute_qs

                # Check ray tracing extension
                ext_props = vk.vkEnumerateDeviceExtensionProperties(pd, None)
                exts = [e.extensionName for e in ext_props]
                if any("ray_tracing" in e for e in exts):
                    score += 50

                score += compute_qs * 10
                if score > best_score:
                    best = (pd, props, qfs, exts)
                    best_score = score

            if not best:
                self.diagnostic = "No suitable Vulkan device"
                self._cleanup()
                return

            pd, props, qfs, exts = best
            self.physical_device = pd

            vendor_map = {0x10DE: "NVIDIA", 0x1002: "AMD", 0x8086: "Intel"}
            self.gpu_info["name"] = props.deviceName
            self.gpu_info["vendor"] = vendor_map.get(props.vendorID, f"0x{props.vendorID:X}")
            ver = f"{vk.VK_VERSION_MAJOR(props.apiVersion)}.{vk.VK_VERSION_MINOR(props.apiVersion)}.{vk.VK_VERSION_PATCH(props.apiVersion)}"
            self.gpu_info["vulkan_version"] = ver
            self.gpu_info["api_version"] = ver
            self.gpu_info["driver_version"] = str(props.driverVersion)
            self.gpu_info["async_compute"] = sum(1 for qf in qfs if qf.queueFlags & vk.VK_QUEUE_COMPUTE_BIT)
            self.gpu_info["extensions"] = exts
            self.available = True
            self.diagnostic = "ready"

        except ImportError:
            self.diagnostic = "vulkan Python package not installed (pip install vulkan)"
        except Exception as e:
            self.diagnostic = f"Vulkan init: {e}"
            self._cleanup()

    def _cleanup(self):
        try:
            from . import _vk as vk
            if self.instance:
                vk.vkDestroyInstance(self.instance, None)
        except Exception:
            pass
        self.instance = None
        self.physical_device = None

    def __del__(self):
        self._cleanup()
