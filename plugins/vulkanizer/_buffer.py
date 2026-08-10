"""Vulkanizer BufferAPI — device-local, host-visible, staging buffers with barriers."""


class BufferAPI:
    """Vulkan buffer allocation and management."""

    def __init__(self, instance):
        self.instance = instance

    def _dev(self):
        dev = getattr(self.instance, "device", None)
        if dev is not None and getattr(dev, "device", None) is not None:
            return dev.device
        return self.instance.physical_device

    def _phys(self):
        inst = getattr(self.instance, "instance", None) or self.instance
        return inst.physical_device

    def create_device_buffer(self, size, usage):
        """Create a device-local buffer (GPU memory).
        usage: VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, etc."""
        from . import _vk as vk
        buffer, memory = self._create_buffer(
            size,
            usage,
            vk.VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
        )
        return buffer, memory

    def create_host_buffer(self, size, usage):
        """Create a host-visible buffer (CPU-readable).
        usage: VK_BUFFER_USAGE_TRANSFER_SRC_BIT for staging."""
        from . import _vk as vk
        buffer, memory = self._create_buffer(
            size,
            usage,
            vk.VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | vk.VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        )
        return buffer, memory

    def _create_buffer(self, size, usage, memory_properties):
        from . import _vk as vk
        buffer = vk.vkCreateBuffer(
            self._dev(),
            vk.VkBufferCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
                size=size,
                usage=usage,
                sharingMode=vk.VK_SHARING_MODE_EXCLUSIVE,
            )
        )
        mem_reqs = vk.vkGetBufferMemoryRequirements(self._dev(), buffer)
        mem_type = self._find_memory_type(mem_reqs.memoryTypeBits, memory_properties)
        memory = vk.vkAllocateMemory(
            self._dev(),
            vk.VkMemoryAllocateInfo(
                sType=vk.VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
                allocationSize=mem_reqs.size,
                memoryTypeIndex=mem_type,
            )
        )
        vk.vkBindBufferMemory(self._dev(), buffer, memory, 0)
        return buffer, memory

    def _find_memory_type(self, type_filter, properties):
        from . import _vk as vk
        mem_props = vk.vkGetPhysicalDeviceMemoryProperties(self._phys())
        for i in range(mem_props.memoryTypeCount):
            if (type_filter & (1 << i)) and (mem_props.memoryTypes[i].propertyFlags & properties) == properties:
                return i
        raise RuntimeError("Failed to find suitable memory type")

    def upload(self, buffer, memory, data, size):
        """Write bytes directly into a host-visible buffer (map + write)."""
        from . import _vk as vk
        mapped = vk.vkMapMemory(self._dev(), memory, 0, size, 0)
        memoryview(mapped)[:size] = data
        vk.vkUnmapMemory(self._dev(), memory)
        return buffer

    def destroy(self, buffer, memory):
        from . import _vk as vk
        vk.vkDestroyBuffer(self._dev(), buffer, None)
        vk.vkFreeMemory(self._dev(), memory, None)
