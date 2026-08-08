"""Vulkanizer VulkanAPI — top-level API exposing all Vulkan primitives."""


class VulkanAPI:
    """Low-level Vulkan API. All sub-APIs are accessed as attributes."""

    def __init__(self, instance):
        self.instance = instance
        self.available = instance.available
        if not self.available:
            return

        from ._pipeline import PipelineAPI
        from ._buffer import BufferAPI
        from ._command import CommandAPI
        from ._raytrace import RayTraceAPI
        from ._upscale import UpscaleAPI

        self.pipeline = PipelineAPI(instance)
        self.buffer = BufferAPI(instance)
        self.command = CommandAPI(instance)
        self.raytrace = RayTraceAPI(instance)
        self.upscale = UpscaleAPI(instance)

    def shutdown(self):
        self.instance._cleanup()
