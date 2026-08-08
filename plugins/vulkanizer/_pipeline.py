"""Vulkanizer PipelineAPI — compute/graphics pipelines, shader modules, descriptor sets."""


class PipelineAPI:
    """Vulkan pipeline creation and management."""

    def __init__(self, instance):
        self.instance = instance

    def create_compute_pipeline(self, spirv_code, entry_point="main"):
        """Create a compute pipeline from SPIR-V bytecode.
        Returns pipeline object or None if SPIR-V compilation unavailable."""
        try:
            import vulkan as vk

            shader_module = vk.vkCreateShaderModule(
                self.instance.physical_device,
                vk.VkShaderModuleCreateInfo(
                    sType=vk.VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
                    codeSize=len(spirv_code),
                    pCode=spirv_code,
                )
            )

            # Create pipeline layout (empty for now)
            pipeline_layout = vk.vkCreatePipelineLayout(
                self.instance.physical_device,
                vk.VkPipelineLayoutCreateInfo(
                    sType=vk.VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
                )
            )

            return {
                "shader_module": shader_module,
                "pipeline_layout": pipeline_layout,
                "entry_point": entry_point,
            }
        except Exception as e:
            raise RuntimeError(f"Pipeline creation failed: {e}")

    def destroy_pipeline(self, pipeline):
        import vulkan as vk
        if pipeline:
            vk.vkDestroyShaderModule(self.instance.physical_device, pipeline["shader_module"], None)
            vk.vkDestroyPipelineLayout(self.instance.physical_device, pipeline["pipeline_layout"], None)


class DescriptorAPI:
    """Descriptor set layout, pool, and write management."""

    def __init__(self, instance):
        self.instance = instance

    def create_layout(self, bindings):
        """Create a descriptor set layout from binding descriptions."""
        import vulkan as vk
        layout = vk.vkCreateDescriptorSetLayout(
            self.instance.physical_device,
            vk.VkDescriptorSetLayoutCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
                bindingCount=len(bindings),
                pBindings=bindings,
            )
        )
        return layout

    def create_pool(self, max_sets, pool_sizes):
        """Create a descriptor pool."""
        import vulkan as vk
        pool = vk.vkCreateDescriptorPool(
            self.instance.physical_device,
            vk.VkDescriptorPoolCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
                maxSets=max_sets,
                poolSizeCount=len(pool_sizes),
                pPoolSizes=pool_sizes,
            )
        )
        return pool
