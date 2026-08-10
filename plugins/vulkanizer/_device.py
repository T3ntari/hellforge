"""Vulkanizer DeviceAPI — real logical device + queue creation.

VkInstance picks the physical device; DeviceAPI creates the logical
device (vkCreateDevice) and exposes the queue. The rest of vulkanizer
falls back to the physical device handle when no logical device exists,
so this layer is fully optional — but game/render work must have it.
"""


class DeviceAPI:
    """Logical device + queue. Created against the instance's physical device."""

    def __init__(self, instance):
        self.instance = instance
        self.device = None
        self.queue_family_index = None
        self.queue = None
        self._init()

    def _init(self):
        try:
            from . import _vk as vk
            if not self.instance.physical_device:
                self.instance.diagnostic = "DeviceAPI: no physical device"
                return
            qfs = vk.vkGetPhysicalDeviceQueueFamilyProperties(self.instance.physical_device)
            index = None
            for i, qf in enumerate(qfs):
                if qf.queueFlags & vk.VK_QUEUE_COMPUTE_BIT:
                    index = i
                    break
            if index is None:
                self.instance.diagnostic = "DeviceAPI: no compute queue family"
                return

            self.queue_family_index = index
            priorities = [1.0]
            queue_info = vk.VkDeviceQueueCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO,
                queueFamilyIndex=index,
                queueCount=1,
                pQueuePriorities=priorities,
            )
            self.device = vk.vkCreateDevice(
                self.instance.physical_device,
                vk.VkDeviceCreateInfo(
                    sType=vk.VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO,
                    queueCreateInfoCount=1,
                    pQueueCreateInfos=[queue_info],
                )
            )
            self.queue = vk.vkGetDeviceQueue(self.device, index, 0)
        except Exception as e:
            self.instance.diagnostic = f"DeviceAPI: {e}"
            self.device = None

    @property
    def available(self):
        return self.device is not None

    def wait_idle(self):
        from . import _vk as vk
        if self.device:
            vk.vkDeviceWaitIdle(self.device)

    def destroy(self):
        from . import _vk as vk
        if self.device:
            try:
                vk.vkDestroyDevice(self.device, None)
            except Exception:
                pass
            self.device = None
