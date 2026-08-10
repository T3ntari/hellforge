"""NinjaEngine — Vulkan compute renderer for the ninja corridor walker.

Four compute passes over plain storage buffers (no images, no samplers):

    scene       internal res  params / scene_out / history
    upscale     output res    params / scene_out / history / hi_res
    accumulate  output res    params / hi_res / acc        (only when accum_frames > 1)
    sharpen     output res    params / hi_res / final8     (uint8 RGBA readback)

Params buffer is 512 bytes of float32 (128 floats) shared by every pass;
sizes / render scale are stamped by the engine (37,38,64-67) so the shader
contract can never drift from the buffers it is dispatched against. All
buffers are host-visible + coherent: readback is a fence, a map and a copy.

The engine owns its VkInstance + VulkanAPI when none is injected; when a
pre-built VulkanAPI is passed in, shutdown() leaves it to the caller.
"""

import time
from pathlib import Path

import numpy as np

from plugins.vulkanizer import _vk as vk

PARAMS_BYTES = 512
PARAMS_FLOATS = PARAMS_BYTES // 4


class NinjaEngine:
    """Vulkan compute engine: dispatch, readback, FSR presets, TAA/accum setters."""

    FSR_PRESETS = {"native": 1.0, "quality": 0.77, "balanced": 0.67, "performance": 0.5}

    def __init__(self, instance=None, width=960, height=540, render_scale=0.67,
                 seed=1.0, shader_dir=None):
        if instance is not None and not (
                hasattr(instance, "device") and hasattr(instance, "buffer")):
            # NinjaGame calls NinjaEngine(width, height, render_scale, seed)
            # positionally — reinterpret so both call styles work.
            width, height, render_scale, seed = instance, width, height, render_scale
            instance = None
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.render_scale = float(render_scale)
        self.seed = float(seed)
        self._scale = self.render_scale
        self._preset = None
        self._shader_dir = Path(shader_dir) if shader_dir else (
            Path(__file__).resolve().parent / "shaders")
        self._owns_api = instance is None
        self._api = instance if instance is not None else self._build_api()
        if self._api.device is None or getattr(self._api.device, "device", None) is None:
            diag = getattr(self._api.instance, "diagnostic", "no logical device")
            raise RuntimeError(f"Ninja: device unavailable ({diag})")

        self._pipelines = {}
        self._sets = {}
        self._buffers = {}
        self._pool = None
        self._cmd_pool = None
        self._cmd_buf = None
        self._fence = None
        self._ready = False
        self._dead = False
        self._sharp_in = None
        self.last_frame_ms = 0.0
        self._params = self._default_params()
        self._params_dirty = True

    # ── lifecycle ──

    def _build_api(self):
        from plugins.vulkanizer._instance import VkInstance
        from plugins.vulkanizer._api import VulkanAPI
        inst = VkInstance()
        if not inst.available:
            raise RuntimeError(f"Ninja: Vulkan unavailable ({inst.diagnostic})")
        return VulkanAPI(inst)

    def init(self):
        """Create pipelines, buffers, descriptor sets, command pool. Idempotent."""
        if self._ready:
            return
        api = self._api

        spv = {}
        for name in ("scene", "upscale", "accumulate", "sharpen"):
            path = self._shader_dir / f"{name}.spv"
            try:
                spv[name] = path.read_bytes()
            except OSError as e:
                raise RuntimeError(
                    f"Ninja: shader missing ({path}: {e}) — run tools/build_shaders.py")

        iw, ih = self._internal_res()
        ow, oh = self.width, self.height

        def make(name, size):
            self._buffers[name] = api.buffer.create_host_buffer(
                size, vk.VK_BUFFER_USAGE_STORAGE_BUFFER_BIT)

        make("params", PARAMS_BYTES)
        make("scene_out", iw * ih * 4 * 4)
        make("history", iw * ih * 4 * 4)
        make("hi_res", ow * oh * 4 * 4)
        make("acc", ow * oh * 4 * 4)
        make("final8", ow * oh * 4)

        def binding(i):
            return vk.VkDescriptorSetLayoutBinding(
                binding=i,
                descriptorType=vk.VK_DESCRIPTOR_TYPE_STORAGE_BUFFER,
                descriptorCount=1,
                stageFlags=vk.VK_SHADER_STAGE_COMPUTE_BIT,
                pImmutableSamplers=None)

        lay_scene = api.descriptor.create_layout([binding(0), binding(1), binding(2)])
        lay_up = api.descriptor.create_layout([binding(0), binding(1), binding(2), binding(3)])
        lay_acc = api.descriptor.create_layout([binding(0), binding(1), binding(2)])
        lay_sharp = api.descriptor.create_layout([binding(0), binding(1), binding(2)])

        self._pool = api.descriptor.create_pool(4, [vk.VkDescriptorPoolSize(
            type=vk.VK_DESCRIPTOR_TYPE_STORAGE_BUFFER, descriptorCount=13)])

        self._sets["scene"] = api.descriptor.allocate_set(self._pool, lay_scene)
        self._sets["upscale"] = api.descriptor.allocate_set(self._pool, lay_up)
        self._sets["accumulate"] = api.descriptor.allocate_set(self._pool, lay_acc)
        self._sets["sharpen"] = api.descriptor.allocate_set(self._pool, lay_sharp)

        for name, layout in (("scene", lay_scene), ("upscale", lay_up),
                             ("accumulate", lay_acc), ("sharpen", lay_sharp)):
            self._pipelines[name] = api.pipeline.create_compute_pipeline(
                spv[name], descriptor_set_layouts=[layout])

        self._write_sets()

        self._cmd_pool = api.command.create_pool(api.device.queue_family_index)
        self._cmd_buf = api.command.allocate_buffer(self._cmd_pool, 1)[0]
        self._fence = api.command.create_fence(signaled=True)

        self._ready = True
        self._zero_buffer("acc")
        self._zero_buffer("history")
        self._upload_params()

    def shutdown(self):
        """Destroy everything in reverse creation order. Idempotent; every
        destroy is guarded so a mid-teardown error never crashes the shell."""
        if self._dead:
            return
        self._dead = True
        api = self._api
        if api is None:
            return
        try:
            api.device.wait_idle()
        except Exception:
            pass
        try:
            if self._fence is not None:
                api.command.destroy_fence(self._fence)
        except Exception:
            pass
        self._fence = None
        try:
            if self._cmd_pool is not None:
                api.command.destroy_pool(self._cmd_pool)
        except Exception:
            pass
        self._cmd_pool = self._cmd_buf = None
        for name in ("sharpen", "accumulate", "upscale", "scene"):
            pipe = self._pipelines.pop(name, None)
            if pipe is not None:
                try:
                    api.pipeline.destroy_pipeline(pipe)
                except Exception:
                    pass
        try:
            if self._pool is not None:
                vk.vkDestroyDescriptorPool(api.device.device, self._pool, None)
        except Exception:
            pass
        self._pool = None
        for name in ("final8", "acc", "hi_res", "history", "scene_out", "params"):
            buf = self._buffers.pop(name, None)
            if buf is not None:
                try:
                    api.buffer.destroy(*buf)
                except Exception:
                    pass
        if self._owns_api:
            try:
                api.device.destroy()
            except Exception:
                pass
            try:
                api.instance._cleanup()
            except Exception:
                pass
        self._ready = False

    # ── params ──

    def _default_params(self):
        p = np.zeros(PARAMS_FLOATS, dtype=np.float32)
        p[0:3] = (0.0, 0.0, 0.0)          # cam xyz — cam_y is GROUND; eye_height added by scene
        p[3] = 0.0                        # yaw
        p[4] = 0.0                        # pitch
        p[5] = 1.047                      # fov_rad
        p[6] = 0.0                        # t
        p[7] = self.seed
        p[8:10] = (0.0, 0.0)              # jitter xy (px)
        p[10] = self.render_scale
        p[11] = 1.7                       # eye_height
        p[12] = 2.75                      # corridor_halfwidth
        p[13] = 50.0                      # corridor_len
        p[14] = 20.0                      # stair_z0
        p[15] = 6.0                       # stair_len
        p[16] = 1.8                       # stair_height
        p[17] = 2.0                       # brazier_spacing
        p[18] = 1.0                       # brazier_first_z
        p[19] = 4.0                       # ceiling_height
        p[20:23] = (1.3, 1.0, 0.4)        # fire freq / amp / wind
        p[23] = 0.0                       # palette_shift
        p[24:34] = 0.0                    # per-brazier phase (10)
        p[34] = 0.0                       # taa_on
        p[35] = 1.0                       # accum_frames
        p[36] = 0.0                       # fire_shape
        p[68] = 0.6                       # sharpen
        p[69] = 1.0                       # tonemap_exposure
        return p

    def _stamp_sizes(self):
        iw, ih = self._internal_res()
        p = self._params
        p[10] = self._scale
        p[37] = float(iw)
        p[38] = float(ih)
        p[64] = float(iw)
        p[65] = float(ih)
        p[66] = float(self.width)
        p[67] = float(self.height)

    def _upload_params(self):
        if not self._ready:
            return
        buf, mem = self._buffers["params"]
        self._api.buffer.upload(buf, mem, self._params.tobytes(), PARAMS_BYTES)
        self._params_dirty = False

    def _zero_buffer(self, name):
        buf, mem = self._buffers[name]
        size = self.width * self.height * 4 * 4
        if name in ("scene_out", "history"):
            iw, ih = self._internal_res()
            size = iw * ih * 4 * 4
        elif name == "final8":
            size = self.width * self.height * 4
        self._api.buffer.upload(buf, mem, b"\x00" * size, size)

    def set_params(self, np_array128):
        a = np.asarray(np_array128, dtype=np.float32)
        if a.size < PARAMS_FLOATS:
            raise ValueError(f"params array must have >= {PARAMS_FLOATS} floats, got {a.size}")
        self._params[:] = a[:PARAMS_FLOATS]
        self._stamp_sizes()
        self._params_dirty = True
        self._upload_params()

    def set_taa(self, on):
        self._params[34] = 1.0 if on else 0.0
        self._upload_params()

    def set_accumulation(self, frames):
        self._params[35] = float(max(1, int(frames)))
        self._upload_params()

    def set_sharpen(self, x):
        self._params[68] = float(x)
        self._upload_params()

    def set_exposure(self, x):
        self._params[69] = float(x)
        self._upload_params()

    # ── resolution / FSR ──

    def _internal_res(self):
        iw = max(1, round(self.width * self._scale))
        ih = max(1, round(self.height * self._scale))
        return iw, ih

    @property
    def internal_w(self):
        return self._internal_res()[0]

    @property
    def internal_h(self):
        return self._internal_res()[1]

    def set_fsr_preset(self, name):
        if name not in self.FSR_PRESETS:
            raise ValueError(f"unknown FSR preset {name!r} "
                             f"(one of {', '.join(self.FSR_PRESETS)})")
        self._scale = self.FSR_PRESETS[name]
        self.render_scale = self._scale
        self._preset = name
        if not self._ready:
            return
        api = self._api
        iw, ih = self._internal_res()
        old_so = self._buffers.pop("scene_out")
        old_hist = self._buffers.pop("history")
        api.buffer.destroy(*old_so)
        api.buffer.destroy(*old_hist)
        self._buffers["scene_out"] = api.buffer.create_host_buffer(
            iw * ih * 4 * 4, vk.VK_BUFFER_USAGE_STORAGE_BUFFER_BIT)
        self._buffers["history"] = api.buffer.create_host_buffer(
            iw * ih * 4 * 4, vk.VK_BUFFER_USAGE_STORAGE_BUFFER_BIT)
        self._write_sets()
        self._zero_buffer("history")
        self._stamp_sizes()
        self._upload_params()

    # ── descriptors ──

    def _write_sets(self):
        api = self._api
        b = self._buffers
        iw, ih = self._internal_res()
        int_bytes = iw * ih * 4 * 4
        out_bytes = self.width * self.height * 4 * 4
        api.descriptor.write_buffers(
            self._sets["scene"], [0, 1, 2],
            [(b["params"][0], 0, PARAMS_BYTES), (b["scene_out"][0], 0, int_bytes),
             (b["history"][0], 0, int_bytes)])
        api.descriptor.write_buffers(
            self._sets["upscale"], [0, 1, 2, 3],
            [(b["params"][0], 0, PARAMS_BYTES), (b["scene_out"][0], 0, int_bytes),
             (b["history"][0], 0, int_bytes), (b["hi_res"][0], 0, out_bytes)])
        api.descriptor.write_buffers(
            self._sets["accumulate"], [0, 1, 2],
            [(b["params"][0], 0, PARAMS_BYTES), (b["hi_res"][0], 0, out_bytes),
             (b["acc"][0], 0, out_bytes)])
        # Sharpen consumes the accumulated image when accumulation is active,
        # else the raw upscaled frame (accumulate.comp only writes acc).
        sharp_in = "acc" if self._params[35] > 1.0 else "hi_res"
        api.descriptor.write_buffers(
            self._sets["sharpen"], [0, 1, 2],
            [(b["params"][0], 0, PARAMS_BYTES), (b[sharp_in][0], 0, out_bytes),
             (b["final8"][0], 0, self.width * self.height * 4)])

    # ── frame ──

    def _barrier(self, cb):
        vk.vkCmdPipelineBarrier(
            cb,
            vk.VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
            vk.VK_PIPELINE_STAGE_ALL_COMMANDS_BIT,
            0,
            1, [vk.VkMemoryBarrier(
                sType=vk.VK_STRUCTURE_TYPE_MEMORY_BARRIER,
                srcAccessMask=vk.VK_ACCESS_SHADER_WRITE_BIT | vk.VK_ACCESS_SHADER_READ_BIT,
                dstAccessMask=vk.VK_ACCESS_SHADER_WRITE_BIT | vk.VK_ACCESS_SHADER_READ_BIT)],
            0, [], 0, [])

    def _dispatch_pass(self, name, gx, gy):
        api = self._api
        pipe = self._pipelines[name]
        api.command.bind_compute(self._cmd_buf, pipe["pipeline"],
                                 pipe["pipeline_layout"], self._sets[name])
        api.command.dispatch(self._cmd_buf, gx, gy)

    def render(self, demo_overlay=None):
        """Render one frame, return uint8 RGBA (height, width, 4) and store
        frame time in last_frame_ms. Optional overlay: same-size uint8 RGBA,
        copied in where alpha > 0."""
        if not self._ready:
            self.init()
        api = self._api
        t0 = time.perf_counter()

        api.command.wait_for_fence(self._fence)
        api.command.reset_fence(self._fence)
        api.command.begin(self._cmd_buf)
        if self._params_dirty:
            self._upload_params()

        # Sharpen consumes the accumulated image whenever accumulation is
        # active (accumulate.comp writes acc, not its input). Rebind on state
        # change — the menu toggles accumulation via params, not the setters.
        sharp_in = "acc" if self._params[35] > 1.0 else "hi_res"
        if sharp_in != self._sharp_in:
            self._sharp_in = sharp_in
            self._write_sets()
            if sharp_in == "acc":
                self._zero_buffer("acc")

        iw, ih = self._internal_res()
        ow, oh = self.width, self.height
        self._dispatch_pass("scene", (iw + 7) // 8, (ih + 7) // 8)
        self._barrier(self._cmd_buf)
        self._dispatch_pass("upscale", (ow + 7) // 8, (oh + 7) // 8)
        self._barrier(self._cmd_buf)
        if self._params[35] > 1.0:
            self._dispatch_pass("accumulate", (ow + 7) // 8, (oh + 7) // 8)
            self._barrier(self._cmd_buf)
        self._dispatch_pass("sharpen", (ow + 7) // 8, (oh + 7) // 8)

        api.command.end(self._cmd_buf)
        api.command.submit(self._cmd_buf, fence=self._fence)
        api.command.wait_for_fence(self._fence)

        frame = self._readback()
        if demo_overlay is not None:
            self._apply_overlay(frame, demo_overlay)
        self.last_frame_ms = (time.perf_counter() - t0) * 1000.0
        return frame

    def _readback(self):
        api = self._api
        buf, mem = self._buffers["final8"]
        n = self.width * self.height * 4
        mapped = vk.vkMapMemory(api.device.device, mem, 0, n, 0)
        try:
            arr = np.frombuffer(mapped, dtype=np.uint8, count=n).copy()
        finally:
            vk.vkUnmapMemory(api.device.device, mem)
        return arr.reshape(self.height, self.width, 4)

    def _apply_overlay(self, frame, overlay):
        ov = np.asarray(overlay)
        if ov.shape == frame.shape:
            mask = ov[..., 3] > 0
            if mask.any():
                frame[mask] = ov[mask]
        elif ov.shape == (self.height, self.width, 3):
            frame[..., :3] = ov
        else:
            raise ValueError(f"overlay shape {ov.shape} does not match "
                             f"frame {(self.height, self.width, 4)}")

    # ── info ──

    def gpu_info(self):
        g = self._api.instance.gpu_info
        iw, ih = self._internal_res()
        fps = 1000.0 / self.last_frame_ms if self.last_frame_ms > 0.0 else 0.0
        return {
            "name": g.get("name", "Unknown GPU"),
            "vendor": g.get("vendor", "Unknown"),
            "fps": fps,
            "internal_w": iw,
            "internal_h": ih,
            "output_w": self.width,
            "output_h": self.height,
            "frame_ms": self.last_frame_ms,
            "fsr_preset": self._preset,
            "render_scale": self._scale,
        }
