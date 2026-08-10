"""Vulkanizer CommandAPI — command pools, command buffers, submit, synchronization."""


class CommandAPI:
    """Command pool, command buffers, submit, synchronization."""

    def __init__(self, instance):
        self.instance = instance

    def _dev(self):
        dev = getattr(self.instance, "device", None)
        if dev is not None and getattr(dev, "device", None) is not None:
            return dev.device
        return self._dev()

    def create_pool(self, queue_family_index=0):
        """Create a command pool."""
        from . import _vk as vk
        pool = vk.vkCreateCommandPool(
            self._dev(),
            vk.VkCommandPoolCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                queueFamilyIndex=queue_family_index,
                flags=vk.VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
            )
        )
        return pool

    def allocate_buffer(self, pool, count=1):
        """Allocate command buffers from a pool."""
        from . import _vk as vk
        buffers = vk.vkAllocateCommandBuffers(
            self._dev(),
            vk.VkCommandBufferAllocateInfo(
                sType=vk.VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO,
                commandPool=pool,
                level=vk.VK_COMMAND_BUFFER_LEVEL_PRIMARY,
                commandBufferCount=count,
            )
        )
        return buffers

    def begin(self, cmd_buffer):
        """Begin recording a command buffer."""
        from . import _vk as vk
        vk.vkBeginCommandBuffer(
            cmd_buffer,
            vk.VkCommandBufferBeginInfo(
                sType=vk.VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
                flags=vk.VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
            )
        )

    def end(self, cmd_buffer):
        """End recording a command buffer."""
        from . import _vk as vk
        vk.vkEndCommandBuffer(cmd_buffer)

    def dispatch(self, cmd_buffer, group_count_x, group_count_y=1, group_count_z=1):
        """Record a compute dispatch command."""
        from . import _vk as vk
        vk.vkCmdDispatch(cmd_buffer, group_count_x, group_count_y, group_count_z)

    def pipeline_barrier(self, cmd_buffer):
        """Record a full memory barrier (for shader read-after-write)."""
        from . import _vk as vk
        vk.vkCmdPipelineBarrier(
            cmd_buffer,
            vk.VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
            vk.VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
            0,
            1, [vk.VkMemoryBarrier(
                sType=vk.VK_STRUCTURE_TYPE_MEMORY_BARRIER,
                srcAccessMask=vk.VK_ACCESS_SHADER_WRITE_BIT,
                dstAccessMask=vk.VK_ACCESS_SHADER_READ_BIT,
            )],
            0, None, 0, None,
        )

    def submit(self, cmd_buffer, queue=None, fence=None):
        """Submit a command buffer to a queue."""
        from . import _vk as vk
        _q = queue
        if _q is None:
            _dev = getattr(self.instance, "device", None)
            if _dev is not None and getattr(_dev, "queue", None) is not None:
                _q = _dev.queue
        if _q is None:
            _q = 0
        vk.vkQueueSubmit(
            _q,
            1, [vk.VkSubmitInfo(
                sType=vk.VK_STRUCTURE_TYPE_SUBMIT_INFO,
                commandBufferCount=1,
                pCommandBuffers=[cmd_buffer],
            )],
            fence or vk.VK_NULL_HANDLE,
        )

    def create_fence(self, signaled=False):
        """Create a fence for CPU-GPU synchronization."""
        from . import _vk as vk
        fence = vk.vkCreateFence(
            self._dev(),
            vk.VkFenceCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_FENCE_CREATE_INFO,
                flags=vk.VK_FENCE_CREATE_SIGNALED_BIT if signaled else 0,
            )
        )
        return fence

    def create_semaphore(self):
        """Create a semaphore for GPU-GPU synchronization."""
        from . import _vk as vk
        sem = vk.vkCreateSemaphore(
            self._dev(),
            vk.VkSemaphoreCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
            )
        )
        return sem

    def wait_for_fence(self, fence, timeout_ns=100000000000):
        """Wait for a fence (default 100s timeout)."""
        from . import _vk as vk
        vk.vkWaitForFences(self._dev(), 1, [fence], True, timeout_ns)

    def reset_fence(self, fence):
        from . import _vk as vk
        vk.vkResetFences(self._dev(), 1, [fence])

    def destroy_pool(self, pool):
        from . import _vk as vk
        vk.vkDestroyCommandPool(self._dev(), pool, None)

    def destroy_fence(self, fence):
        from . import _vk as vk
        vk.vkDestroyFence(self._dev(), fence, None)

    def destroy_semaphore(self, sem):
        from . import _vk as vk
        vk.vkDestroySemaphore(self._dev(), sem, None)

    def bind_compute(self, cmd_buffer, pipeline, pipeline_layout, desc_set):
        """Bind a compute pipeline + descriptor set in one call."""
        from . import _vk as vk
        vk.vkCmdBindPipeline(cmd_buffer, vk.VK_PIPELINE_BIND_POINT_COMPUTE, pipeline)
        vk.vkCmdBindDescriptorSets(
            cmd_buffer, vk.VK_PIPELINE_BIND_POINT_COMPUTE, pipeline_layout,
            0, 1, [desc_set], 0, [],
        )
