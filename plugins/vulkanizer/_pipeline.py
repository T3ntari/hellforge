"""Vulkanizer PipelineAPI — compute/graphics pipelines, shader modules, descriptor sets."""


class PipelineAPI:
    """Vulkan pipeline creation and management."""

    def __init__(self, instance):
        self.instance = instance

    def _dev(self):
        dev = getattr(self.instance, "device", None)
        if dev is not None and getattr(dev, "device", None) is not None:
            return dev.device
        return self.instance.physical_device

    def create_compute_pipeline(self, spirv_code, entry_point="main",
                                descriptor_set_layouts=None, push_constant_range=None):
        """Create a compute pipeline from SPIR-V bytecode.
        descriptor_set_layouts: list of VkDescriptorSetLayout for the layout.
        push_constant_range: VkPushConstantRange or None.
        Returns a dict with shader_module / pipeline_layout / pipeline /
        descriptor_set_layouts / push_constant_range."""
        try:
            from . import _vk as vk

            shader_module = vk.vkCreateShaderModule(
                self._dev(),
                vk.VkShaderModuleCreateInfo(
                    sType=vk.VK_STRUCTURE_TYPE_SHADER_MODULE_CREATE_INFO,
                    codeSize=len(spirv_code),
                    pCode=spirv_code,
                )
            )

            pc_ranges = [push_constant_range] if push_constant_range else []
            pipeline_layout = vk.vkCreatePipelineLayout(
                self._dev(),
                vk.VkPipelineLayoutCreateInfo(
                    sType=vk.VK_STRUCTURE_TYPE_PIPELINE_LAYOUT_CREATE_INFO,
                    setLayoutCount=len(descriptor_set_layouts or []),
                    pSetLayouts=descriptor_set_layouts or [],
                    pushConstantRangeCount=len(pc_ranges),
                    pPushConstantRanges=pc_ranges,
                )
            )

            pipeline = None
            if descriptor_set_layouts is not None:
                stage = vk.VkPipelineShaderStageCreateInfo(
                    sType=vk.VK_STRUCTURE_TYPE_PIPELINE_SHADER_STAGE_CREATE_INFO,
                    stage=vk.VK_SHADER_STAGE_COMPUTE_BIT,
                    module=shader_module,
                    pName=entry_point,
                )
                pipeline = vk.vkCreateComputePipelines(
                    self._dev(), None, 1, [vk.VkComputePipelineCreateInfo(
                        sType=vk.VK_STRUCTURE_TYPE_COMPUTE_PIPELINE_CREATE_INFO,
                        stage=stage,
                        layout=pipeline_layout,
                    )]
                )[0]

            return {
                "shader_module": shader_module,
                "pipeline_layout": pipeline_layout,
                "pipeline": pipeline,
                "descriptor_set_layouts": descriptor_set_layouts or [],
                "push_constant_range": push_constant_range,
                "entry_point": entry_point,
            }
        except Exception as e:
            raise RuntimeError(f"Pipeline creation failed: {e}")

    def destroy_pipeline(self, pipeline):
        from . import _vk as vk
        if pipeline:
            if pipeline.get("pipeline"):
                vk.vkDestroyPipeline(self._dev(), pipeline["pipeline"], None)
            vk.vkDestroyShaderModule(self._dev(), pipeline["shader_module"], None)
            vk.vkDestroyPipelineLayout(self._dev(), pipeline["pipeline_layout"], None)
            for layout in pipeline.get("descriptor_set_layouts", []):
                vk.vkDestroyDescriptorSetLayout(self._dev(), layout, None)


class DescriptorAPI:
    """Descriptor set layout, pool, and write management."""

    def __init__(self, instance):
        self.instance = instance

    def _dev(self):
        dev = getattr(self.instance, "device", None)
        if dev is not None and getattr(dev, "device", None) is not None:
            return dev.device
        return self.instance.physical_device

    def create_layout(self, bindings):
        """Create a descriptor set layout from binding descriptions."""
        from . import _vk as vk
        layout = vk.vkCreateDescriptorSetLayout(
            self._dev(),
            vk.VkDescriptorSetLayoutCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_SET_LAYOUT_CREATE_INFO,
                bindingCount=len(bindings),
                pBindings=bindings,
            )
        )
        return layout

    def create_pool(self, max_sets, pool_sizes):
        """Create a descriptor pool."""
        from . import _vk as vk
        pool = vk.vkCreateDescriptorPool(
            self._dev(),
            vk.VkDescriptorPoolCreateInfo(
                sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO,
                maxSets=max_sets,
                poolSizeCount=len(pool_sizes),
                pPoolSizes=pool_sizes,
            )
        )
        return pool

    def allocate_set(self, pool, layout):
        """Allocate a single descriptor set."""
        from . import _vk as vk
        return vk.vkAllocateDescriptorSets(
            self._dev(),
            vk.VkDescriptorSetAllocateInfo(
                sType=vk.VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO,
                descriptorPool=pool,
                descriptorSetCount=1,
                pSetLayouts=[layout],
            )
        )[0]

    def write_buffers(self, desc_set, bindings, buffer_infos):
        """Write storage buffer descriptors. bindings: list of int,
        buffer_infos: list of (buffer, offset, range)."""
        from . import _vk as vk
        writes = [
            vk.VkWriteDescriptorSet(
                sType=vk.VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
                dstSet=desc_set,
                dstBinding=b,
                descriptorCount=1,
                descriptorType=vk.VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                pBufferInfo=[vk.VkDescriptorBufferInfo(
                    buffer=buffer_infos[i][0], offset=buffer_infos[i][1], range=buffer_infos[i][2],
                )],
            )
            for i, b in enumerate(bindings)
        ]
        vk.vkUpdateDescriptorSets(self._dev(), len(writes), writes, 0, [])

    def write_uniform(self, desc_set, bindings, buffer_infos):
        """Write uniform buffer descriptors."""
        from . import _vk as vk
        writes = [
            vk.VkWriteDescriptorSet(
                sType=vk.VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
                dstSet=desc_set,
                dstBinding=b,
                descriptorCount=1,
                descriptorType=vk.VK_DESCRIPTOR_TYPE_UNIFORM_BUFFER,
                pBufferInfo=[vk.VkDescriptorBufferInfo(
                    buffer=buffer_infos[i][0], offset=buffer_infos[i][1], range=buffer_infos[i][2],
                )],
            )
            for i, b in enumerate(bindings)
        ]
        vk.vkUpdateDescriptorSets(self._dev(), len(writes), writes, 0, [])

    def write_storage_images(self, desc_set, bindings, image_views, layouts):
        """Write storage image descriptors. image_views: list of view handles,
        layouts: list of VK_IMAGE_LAYOUT values."""
        from . import _vk as vk
        writes = [
            vk.VkWriteDescriptorSet(
                sType=vk.VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET,
                dstSet=desc_set,
                dstBinding=b,
                descriptorCount=1,
                descriptorType=vk.VK_DESCRIPTOR_TYPE_STORAGE_IMAGE,
                pImageInfo=[vk.VkDescriptorImageInfo(
                    sampler=vk.VK_NULL_HANDLE, imageView=image_views[i],
                    imageLayout=layouts[i],
                )],
            )
            for i, b in enumerate(bindings)
        ]
        vk.vkUpdateDescriptorSets(self._dev(), len(writes), writes, 0, [])
