"""Vulkanizer RayTraceAPI — VK_KHR_ray_tracing capability detection.
Hardware acceleration is probed on the Vulkan instance; when the
extensions are absent the API reports available=False and no ray
tracing surface is exposed (callers must gate on `.available`)."""


class RayTraceAPI:
    """VK_KHR_ray_tracing capability probe for the Vulkan instance.
    Available on NVIDIA RTX (Turing+), AMD RX 6000+, Intel Arc A3+.

    The probe is the entire API: there is no software fallback, and
    no BLAS/TLAS/SBT surface is exposed when the extensions are
    missing. Consumers gate on `.available` before building any
    acceleration structure."""

    def __init__(self, instance):
        self.instance = instance
        self.available = False
        self._check_availability()

    def _check_availability(self):
        """Check if ray tracing extensions are available."""
        exts = self.instance.gpu_info.get("extensions", [])
        required = [
            "VK_KHR_acceleration_structure",
            "VK_KHR_ray_tracing_pipeline",
            "VK_KHR_ray_query",
            "VK_KHR_deferred_host_operations",
        ]
        self.available = all(r in exts for r in required)
        if self.available:
            self.acceleration_structure = "VK_KHR_acceleration_structure"
            self.ray_tracing_pipeline = "VK_KHR_ray_tracing_pipeline"
            self.ray_query = "VK_KHR_ray_query"

    @property
    def info(self):
        """Return ray tracing capability info."""
        return {
            "available": self.available,
            "acceleration_structure": self.acceleration_structure if self.available else "N/A",
            "ray_tracing_pipeline": self.ray_tracing_pipeline if self.available else "N/A",
            "ray_query": self.ray_query if self.available else "N/A",
        }
