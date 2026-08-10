"""Vulkanizer VulkanAPI — top-level API exposing all Vulkan primitives."""


class VulkanAPI:
    """Low-level Vulkan API. All sub-APIs are accessed as attributes."""

    def __init__(self, instance):
        self.instance = instance
        self.available = instance.available
        if not self.available:
            return

        from ._pipeline import PipelineAPI, DescriptorAPI
        from ._buffer import BufferAPI
        from ._command import CommandAPI
        from ._raytrace import RayTraceAPI
        from ._upscale import UpscaleAPI
        from ._device import DeviceAPI

        self.device = DeviceAPI(instance)
        self.descriptor = DescriptorAPI(self)
        if not self.device.available:
            instance.diagnostic += f" | device: {instance.diagnostic}"
        self.pipeline = PipelineAPI(self)
        self.buffer = BufferAPI(self)
        self.command = CommandAPI(self)
        self.raytrace = RayTraceAPI(instance)
        self.upscale = UpscaleAPI(instance)

    def shutdown(self):
        if getattr(self, "device", None) is not None:
            self.device.destroy()
        self.instance._cleanup()
