"""Vulkanizer _vk — thin compatibility layer over the raw `vulkan` bindings.

The generated python bindings (>= 1.3.250) require an explicit pAllocator
argument on Create/Destroy entry points. This module re-exports everything
from the raw bindings but wraps those entry points so the allocator may be
omitted (None is passed automatically). All vulkanizer modules should
`from . import _vk as vk` instead of `import vulkan as vk`.
"""

import vulkan as _raw

_ALLOCATOR_FUNCS = (
    "vkCreateInstance", "vkDestroyInstance",
    "vkCreateDevice", "vkDestroyDevice",
    "vkCreateBuffer", "vkDestroyBuffer",
    "vkAllocateMemory", "vkFreeMemory",
    "vkCreateCommandPool", "vkDestroyCommandPool",
    "vkCreateFence", "vkDestroyFence",
    "vkCreateShaderModule", "vkDestroyShaderModule",
    "vkCreatePipelineLayout", "vkDestroyPipelineLayout",
    "vkCreatePipelineCache", "vkDestroyPipelineCache",
    "vkCreateComputePipelines", "vkDestroyPipeline",
    "vkCreateDescriptorSetLayout", "vkDestroyDescriptorSetLayout",
    "vkCreateDescriptorPool", "vkDestroyDescriptorPool",
    "vkCreateImage", "vkDestroyImage",
    "vkCreateImageView", "vkDestroyImageView",
    "vkCreateSemaphore", "vkDestroySemaphore",
    "vkCreateEvent", "vkDestroyEvent",
    "vkCreateQueryPool", "vkDestroyQueryPool",
    "vkCreateRenderPass", "vkDestroyRenderPass",
    "vkCreateFramebuffer", "vkDestroyFramebuffer",
    "vkCreateGraphicsPipelines",
)

globals().update({_n: getattr(_raw, _n) for _n in dir(_raw) if _n.startswith(("vk", "Vk", "VK_", "PFN_"))})


def _allocator_wrap(name):
    fn = getattr(_raw, name)

    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except TypeError:
            return fn(*args, None, **kwargs)

    wrapper.__name__ = name
    globals()[name] = wrapper


for _name in _ALLOCATOR_FUNCS:
    if hasattr(_raw, _name):
        _allocator_wrap(_name)
