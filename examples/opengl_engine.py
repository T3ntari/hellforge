#!/usr/bin/env python3
"""Example: AAA Game Engine built on OPENapi + Vulkanizer + EAudio APIs.
This is NOT part of any plugin — it's a standalone example showing how
third-party modders build game engines ON TOP of these low-level APIs.

Uses:
  - OPENapi: OpenGL context, shaders, buffers, textures, window, input
  - Vulkanizer: Vulkan compute for batch physics, upscaling via Tensor Cores
  - EAudio: 3D spatial audio, effects, streaming

Run: python examples/opengl_engine.py"""

import sys
import os
import time
import math
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import numpy as np
except ImportError:
    np = None


class GameEngine:
    """Example game engine built on low-level APIs.
    This shows the PATTERN third-party modders follow."""

    def __init__(self):
        self.api = None
        self.vk_api = None
        self.audio_api = None
        self.running = False
        self.dt = 0.0
        self.frame_count = 0

    def init(self):
        """Initialize all APIs."""
        print("GameEngine: Initializing...")

        # 1. Init OPENapi (OpenGL)
        from plugins.openapi import get_api as get_openapi
        from plugins.openapi._context import GLContext
        ctx = GLContext(width=1280, height=720, title="Game Engine Demo")
        if not ctx.available:
            print("  FAILED: No OpenGL context")
            return False

        from plugins.openapi._api import OpenGLAPI
        self.api = OpenGLAPI(ctx)
        print(f"  OPENapi: {ctx.gpu_name} ({ctx.gl_version})")

        # 2. Init Vulkanizer (Vulkan compute for physics + upscaling)
        try:
            from plugins.vulkanizer import get_api as get_vkapi
            self.vk_api = get_vkapi()
            if self.vk_api and self.vk_api.available:
                print(f"  Vulkanizer: compute + upscaling available")
                if self.vk_api.raytrace.available:
                    print(f"  Ray tracing: HARDWARE ACCELERATED")
        except Exception:
            pass

        # 3. Init EAudio (3D spatial audio)
        try:
            from plugins.eaudio._device import AudioDeviceAPI
            from plugins.eaudio._buffer import AudioBufferAPI
            from plugins.eaudio._spatial import SpatialAudioAPI
            from plugins.eaudio._effects import AudioEffectsAPI
            ad = AudioDeviceAPI()
            if ad.available:
                self.audio_api = {
                    "device": ad,
                    "buffer": AudioBufferAPI(ad),
                    "spatial": SpatialAudioAPI(ad),
                    "effects": AudioEffectsAPI(ad),
                }
                print(f"  EAudio: {ad.device_count} devices")
        except Exception:
            pass

        # 4. Set up OpenGL shaders
        self._setup_shaders()

        # 5. Set up audio world
        if self.audio_api:
            self._setup_audio()

        self.running = True
        print(f"GameEngine: Ready")
        return True

    def _setup_shaders(self):
        """Compile basic shaders for the game."""
        vertex_src = """
#version 460 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec4 aColor;
uniform mat4 uMVP;
out vec4 vColor;
void main() {
    gl_Position = uMVP * vec4(aPos, 1.0);
    vColor = aColor;
}
"""
        fragment_src = """
#version 460 core
in vec4 vColor;
out vec4 FragColor;
void main() {
    FragColor = vColor;
}
"""
        try:
            self.shader_program = self.api.shader.compile(vertex_src, fragment_src, "basic")
            print(f"  Shaders compiled: program {self.shader_program}")
        except Exception as e:
            print(f"  Shader error: {e}")

    def _setup_audio(self):
        """Set up 3D audio world."""
        spa = self.audio_api["spatial"]
        spa.set_listener([0, 0, 0], velocity=[0, 0, 0])
        buf = self.audio_api["buffer"].create_sine(440, 0.5, amplitude=0.3)
        for i in range(3):
            spa.add_source(f"source_{i}", [random.uniform(-10, 10), 0, random.uniform(-10, 10)])
            spa.set_source_buffer(f"source_{i}", buf)

    def update(self, dt):
        """Game update: physics, AI, audio."""
        self.dt = dt
        self.frame_count += 1

        # Audio sources orbit around listener
        if self.audio_api:
            spa = self.audio_api["spatial"]
            for i in range(3):
                angle = self.frame_count * 0.5 + i * 2.094
                x = math.sin(angle) * 8
                z = math.cos(angle) * 8
                spa.update_source(f"source_{i}", [x, 0, z], [math.cos(angle) * 2, 0, -math.sin(angle) * 2])
                gain = spa.get_spatial_gain(f"source_{i}")
                if gain:
                    self.audio_spatial_gains = gain

    def render(self):
        """Render a frame using OPENapi."""
        if not self.api or not self.api.begin_frame():
            self.running = False
            return

        w, h = self.api.context.width, self.api.context.height
        self.api.render.set_viewport(0, 0, w, h)
        self.api.render.set_depth_test(True)

        # Draw something using the API
        if self.shader_program:
            self.api.shader.use(self.shader_program)
            import numpy as np
            aspect = w / h
            fov = 60.0 * math.pi / 180.0
            proj = self._perspective(fov, aspect, 0.1, 100.0)
            view = self._look_at([0, 2, 5], [0, 0, 0], [0, 1, 0])
            mvp = proj @ view

            self.api.shader.uniform(self.shader_program, "uMVP", mvp.flatten().tolist())

            # Simple triangle
            vao = self.api.buffer.create_vao("triangle")
            self.api.buffer.bind_vao(vao)
            verts = [
                -1, -1, 0,  1, 0, 0, 1,
                 1, -1, 0,  0, 1, 0, 1,
                 0,  1, 0,  0, 0, 1, 1,
            ]
            vbo, _ = self.api.buffer.create_vbo(verts)
            self.api.buffer.vertex_attrib(0, 3, 28, 0)
            self.api.buffer.vertex_attrib(1, 4, 28, 12)
            self.api.render.draw_arrays(4, 0, 3)  # GL_TRIANGLES

        self.api.end_frame()

    def run(self):
        """Main game loop."""
        last_time = time.time()
        while self.running:
            now = time.time()
            dt = now - last_time
            last_time = now
            self.update(dt)
            self.render()
        self.shutdown()

    def shutdown(self):
        if self.api:
            self.api.shutdown()
        print(f"GameEngine: {self.frame_count} frames rendered")

    def _perspective(self, fov, aspect, near, far):
        f = 1.0 / math.tan(fov / 2)
        return np.array([
            [f/aspect, 0, 0, 0],
            [0, f, 0, 0],
            [0, 0, (far+near)/(near-far), 2*far*near/(near-far)],
            [0, 0, -1, 0],
        ], dtype=np.float32)

    def _look_at(self, eye, center, up):
        f = np.array(center) - np.array(eye)
        f = f / np.linalg.norm(f)
        s = np.cross(f, np.array(up))
        s = s / np.linalg.norm(s)
        u = np.cross(s, f)
        return np.array([
            [s[0], s[1], s[2], -np.dot(s, eye)],
            [u[0], u[1], u[2], -np.dot(u, eye)],
            [-f[0], -f[1], -f[2], np.dot(f, eye)],
            [0, 0, 0, 1],
        ], dtype=np.float32)


if __name__ == "__main__":
    engine = GameEngine()
    if engine.init():
        engine.run()
    else:
        print("Game engine failed to initialize")
        print("Install: pip install PyOpenGL glfw numpy")
