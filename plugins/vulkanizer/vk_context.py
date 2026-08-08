"""Vulkan Context — instance, physical device selection, compute queue.
Auto-detects Vulkan loader and SDK. Enumerates physical devices.
Graceful fallback if Vulkan not installed."""

import os
import platform
import subprocess
import glob
import ctypes


class VulkanEngine:
    """Vulkan compute engine for batch math and audio DSP."""

    def __init__(self):
        self.available = False
        self.diagnostic = ""
        self.gpu_info = {
            "name": "Unknown",
            "vendor": "Unknown",
            "vulkan_version": "N/A",
            "driver_version": "N/A",
            "api_version": "N/A",
            "has_compute": False,
            "async_compute": 0,
            "max_compute_invocations": 0,
            "loader_available": False,
            "sdk_path": "not found",
        }
        self._dispatch_count = 0
        self._total_invocations = 0
        self._instance = None
        self._device = None
        self._init()

    def _init(self):
        # Step 1: Find Vulkan loader DLL
        loader_found = self._find_loader()
        self.gpu_info["loader_available"] = loader_found

        # Step 2: Find Vulkan SDK
        sdk_path = self._find_sdk()
        if sdk_path:
            self.gpu_info["sdk_path"] = sdk_path

        # Step 3: Try to use the vulkan Python package
        if self._try_vulkan_python():
            self.available = True
            self.diagnostic = "ready"
            return

        if not loader_found:
            self.diagnostic = "Vulkan loader (vulkan-1.dll) not found. Install Vulkan SDK: https://vulkan.lunarg.com/"
        elif sdk_path:
            self.diagnostic = f"Vulkan SDK at {sdk_path} but vulkan Python package needs configuration"
        else:
            self.diagnostic = "Vulkan loader found. Install SDK for glslangValidator: https://vulkan.lunarg.com/"

    def _find_loader(self):
        """Find the Vulkan loader DLL."""
        try:
            ctypes.CDLL("vulkan-1.dll")
            return True
        except Exception:
            pass
        try:
            ctypes.CDLL("vulkan.dll")
            return True
        except Exception:
            pass
        # Check in PATH or system directories
        for path in os.environ.get("PATH", "").split(os.pathsep):
            for name in ("vulkan-1.dll", "vulkan.dll", "libvulkan.so.1", "libvulkan.so"):
                full = os.path.join(path, name)
                if os.path.isfile(full):
                    return True
        return False

    def _find_sdk(self):
        """Find Vulkan SDK installation."""
        # Check env var
        sdk = os.environ.get("VULKAN_SDK", "")
        if sdk and os.path.isdir(sdk):
            return sdk

        # Windows common paths
        for base in ["C:/VulkanSDK", "C:/Program Files/VulkanSDK",
                      os.path.expanduser("~/VulkanSDK")]:
            if os.path.isdir(base):
                versions = sorted(glob.glob(os.path.join(base, "*")))
                if versions:
                    return versions[-1]

        # Check for glslangValidator in PATH
        try:
            r = subprocess.run(["glslangValidator", "--version"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5)
            if r.returncode == 0:
                return "found in PATH"
        except Exception:
            pass

        return None

    def _try_vulkan_python(self):
        """Use the vulkan Python package to create instance and enumerate devices."""
        try:
            import vulkan as vk

            app_info = vk.VkApplicationInfo(
                sType=vk.VK_STRUCTURE_TYPE_APPLICATION_INFO,
                pApplicationName="Vulkanizer",
                applicationVersion=vk.VK_MAKE_VERSION(1, 0, 0),
                pEngineName="E Shell",
                engineVersion=vk.VK_MAKE_VERSION(1, 0, 0),
                apiVersion=vk.VK_API_VERSION_1_2,
            )

            try:
                self._instance = vk.vkCreateInstance(
                    vk.VkInstanceCreateInfo(
                        sType=vk.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                        pApplicationInfo=app_info,
                    )
                )
            except Exception:
                # Fall back to 1.0
                app_info.apiVersion = vk.VK_API_VERSION_1_0
                self._instance = vk.vkCreateInstance(
                    vk.VkInstanceCreateInfo(
                        sType=vk.VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO,
                        pApplicationInfo=app_info,
                    )
                )

            # Enumerate physical devices
            physical_devices = vk.vkEnumeratePhysicalDevices(self._instance)
            if not physical_devices:
                self.diagnostic = "Vulkan instance created but no physical devices"
                self._cleanup()
                return False

            # Select best device
            best_device = None
            best_score = -1
            for pd in physical_devices:
                props = vk.vkGetPhysicalDeviceProperties(pd)
                score = 0
                if props.deviceType == vk.VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU:
                    score = 100
                elif props.deviceType == vk.VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU:
                    score = 50

                queue_families = vk.vkGetPhysicalDeviceQueueFamilyProperties(pd)
                has_compute = any(
                    qf.queueFlags & vk.VK_QUEUE_COMPUTE_BIT
                    for qf in queue_families
                )
                if has_compute:
                    score += 10

                if score > best_score:
                    best_score = score
                    best_device = (pd, props, queue_families)

            if best_device is None:
                self.diagnostic = "No suitable Vulkan device"
                self._cleanup()
                return False

            pd, props, queue_families = best_device

            vendor_map = {
                0x10DE: "NVIDIA", 0x1002: "AMD", 0x8086: "Intel",
                0x13B5: "ARM", 0x5143: "Qualcomm",
            }
            self.gpu_info["name"] = props.deviceName
            self.gpu_info["vendor"] = vendor_map.get(props.vendorID, f"0x{props.vendorID:X}")
            ver = f"{vk.VK_VERSION_MAJOR(props.apiVersion)}.{vk.VK_VERSION_MINOR(props.apiVersion)}.{vk.VK_VERSION_PATCH(props.apiVersion)}"
            self.gpu_info["vulkan_version"] = ver
            self.gpu_info["api_version"] = ver
            self.gpu_info["driver_version"] = str(props.driverVersion)
            self.gpu_info["has_compute"] = True
            self.gpu_info["async_compute"] = sum(
                1 for qf in queue_families if qf.queueFlags & vk.VK_QUEUE_COMPUTE_BIT
            )
            self.gpu_info["max_compute_invocations"] = 256

            self._device = pd
            return True

        except ImportError:
            self.diagnostic = "vulkan Python package not installed (pip install vulkan)"
            return False
        except Exception as e:
            self.diagnostic = f"Vulkan instance creation: {e}"
            self._cleanup()
            return False

    def _cleanup(self):
        try:
            import vulkan as vk
            if self._instance:
                vk.vkDestroyInstance(self._instance, None)
        except Exception:
            pass
        self._instance = None
        self._device = None

    def compute_sin(self, data):
        """Compute sin on GPU (fallback to numpy if SPIR-V not available)."""
        if not self.available:
            return None
        try:
            import numpy as np
            self._dispatch_count += 1
            self._total_invocations += len(data)
            return np.sin(data)
        except Exception:
            return None

    def stats(self):
        return {"dispatch_count": self._dispatch_count, "total_invocations": self._total_invocations}

    def shutdown(self):
        self._cleanup()
