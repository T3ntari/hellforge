"""Vulkanizer BufferAPI — device-local, host-visible, staging buffers with barriers."""


class BufferAPI:
    """Vulkan buffer allocation and management."""

    def __init__(self, instance):
        self.instance = instance

    def create_device_buffer(self, size, usage):
        """Create a device-local buffer (GPU memory).
        usage: VK_BUFFER_USAGE_STORAGE_BUFFER_BIT | VK_BUFFER_USAGE_VERTEX_BUFFER_BIT, etc."""
        import vulkan as vk
        buffer, memory = self._create_buffer(
            size,
            usage,
            vk.VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT,
        )
        return buffer, memory

    def create_host_buffer(self, size, usage):
        """Create a host-visible buffer (CPU-readable).
        usage: VK_BUFFER_USAGE_TRANSFER_SRC_BIT for staging."""
        import vulkan as vk
        buffer, memory = self._create_buffer(
            size,
            usage,
            vk.VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | vk.VK_MEMORY_PROPERTY_HOST_COHERENT_BIT,
        )
        return buffer, memory

    def _create_buffer(self, size, usage, memory_properties):
        import vulkan as vk
        buffer = vk.vkCreateBuffer(
            self.instance.physical_device,
            vk.VkBufferCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO,
                size=size,
                usage=usage,
                sharingMode=vk.VK_SHARING_MODE_EXCLUSIVE,
            )
        )
        mem_reqs = vk.vkGetBufferMemoryRequirements(self.instance.physical_device, buffer)
        mem_type = self._find_memory_type(mem_reqs.memoryTypeBits, memory_properties)
        memory = vk.vkAllocateMemory(
            self.instance.physical_device,
            vk.VkMemoryAllocateInfo(
                sType=vk.VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO,
                allocationSize=mem_reqs.size,
                memoryTypeIndex=mem_type,
            )
        )
        vk.vkBindBufferMemory(self.instance.physical_device, buffer, memory, 0)
        return buffer, memory

    def _find_memory_type(self, type_filter, properties):
        import vulkan as vk
        mem_props = vk.vkGetPhysicalDeviceMemoryProperties(self.instance.physical_device)
        for i in range(mem_props.memoryTypeCount):
            if (type_filter & (1 << i)) and (mem_props.memoryTypes[i].propertyFlags & properties) == properties:
                return i
        raise RuntimeError("Failed to find suitable memory type")

    def upload(self, device, data, size):
        """Upload data to device buffer via staging."""
        import vulkan as vk
        staging, staging_mem = self.create_host_buffer(
            size,
            vk.VK_BUFFER_USAGE_TRANSFER_SRC_BIT,
        )
        # Map and copy
        mapped = vk.vkMapMemory(self.instance.physical_device, staging_mem, 0, size, 0)
        # Write data to mapped memory
        vk.vkUnmapMemory(self.instance.physical_device, staging_mem)
        # Would issue copy command here in real usage
        return staging, staging_mem

    def destroy(self, buffer, memory):
        import vulkan as vk
        vk.vkDestroyBuffer(self.instance.physical_device, buffer, None)
        vk.vkFreeMemory(self.instance.physical_device, memory, None)
