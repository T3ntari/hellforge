"""Vulkanizer CommandAPI — command pools, command buffers, submit, synchronization."""


class CommandAPI:
    """Command buffer recording, submission, and synchronization."""

    def __init__(self, instance):
        self.instance = instance

    def create_pool(self, queue_family_index=0):
        """Create a command pool."""
        import vulkan as vk
        pool = vk.vkCreateCommandPool(
            self.instance.physical_device,
            vk.VkCommandPoolCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO,
                queueFamilyIndex=queue_family_index,
                flags=vk.VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT,
            )
        )
        return pool

    def allocate_buffer(self, pool, count=1):
        """Allocate command buffers from a pool."""
        import vulkan as vk
        buffers = vk.vkAllocateCommandBuffers(
            self.instance.physical_device,
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
        import vulkan as vk
        vk.vkBeginCommandBuffer(
            cmd_buffer,
            vk.VkCommandBufferBeginInfo(
                sType=vk.VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO,
                flags=vk.VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT,
            )
        )

    def end(self, cmd_buffer):
        """End recording a command buffer."""
        import vulkan as vk
        vk.vkEndCommandBuffer(cmd_buffer)

    def dispatch(self, cmd_buffer, group_count_x, group_count_y=1, group_count_z=1):
        """Record a compute dispatch command."""
        import vulkan as vk
        vk.vkCmdDispatch(cmd_buffer, group_count_x, group_count_y, group_count_z)

    def pipeline_barrier(self, cmd_buffer):
        """Record a full memory barrier (for shader read-after-write)."""
        import vulkan as vk
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
        import vulkan as vk
        vk.vkQueueSubmit(
            queue or 0,
            1, [vk.VkSubmitInfo(
                sType=vk.VK_STRUCTURE_TYPE_SUBMIT_INFO,
                commandBufferCount=1,
                pCommandBuffers=[cmd_buffer],
            )],
            fence or vk.VK_NULL_HANDLE,
        )

    def create_fence(self, signaled=False):
        """Create a fence for CPU-GPU synchronization."""
        import vulkan as vk
        fence = vk.vkCreateFence(
            self.instance.physical_device,
            vk.VkFenceCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_FENCE_CREATE_INFO,
                flags=vk.VK_FENCE_CREATE_SIGNALED_BIT if signaled else 0,
            )
        )
        return fence

    def create_semaphore(self):
        """Create a semaphore for GPU-GPU synchronization."""
        import vulkan as vk
        sem = vk.vkCreateSemaphore(
            self.instance.physical_device,
            vk.VkSemaphoreCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO,
            )
        )
        return sem

    def wait_for_fence(self, fence, timeout_ns=100000000000):
        """Wait for a fence (default 100s timeout)."""
        import vulkan as vk
        vk.vkWaitForFences(self.instance.physical_device, 1, [fence], True, timeout_ns)

    def reset_fence(self, fence):
        import vulkan as vk
        vk.vkResetFences(self.instance.physical_device, 1, [fence])

    def destroy_pool(self, pool):
        import vulkan as vk
        vk.vkDestroyCommandPool(self.instance.physical_device, pool, None)

    def destroy_fence(self, fence):
        import vulkan as vk
        vk.vkDestroyFence(self.instance.physical_device, fence, None)

    def destroy_semaphore(self, sem):
        import vulkan as vk
        vk.vkDestroySemaphore(self.instance.physical_device, sem, None)
