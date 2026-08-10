**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [custom-plugin](custom-plugin.md) | [gpu-compute](gpu-compute.md) | [game-engine](game-engine.md)

## Building a Game Engine

This example shows how the low-level graphics/audio drivers compose into a
game engine foundation. The drivers are **APIs, not engines** — a modder
builds the engine on top (see `examples/opengl_engine.py`).

### The drivers

- **OPENapi** — OpenGL: context, shaders, buffers, textures, render,
  window
- **Vulkanizer** — Vulkan: instance, pipelines, commands, ray tracing,
  upscaling
- **EAudio** — audio: devices, PCM buffers, 3D spatial, effects
- **Radical** — GPU shader math for expression evaluation

### Engine loop sketch

```python
# engine code (Python, using the plugin APIs)
ctx = openapi_get_api().context          # GL context + window
audio = eaudio_get_api()                 # device + buffers + spatial

while running:
    openapi.render_frame()               # draw calls, swapchain
    audio.spatial.update(listener)       # 3D listener position
    audio.effects.render()               # reverb/EQ chain
    radical.eval({"$x": ...})            # GPU math when needed
```

### Full pipeline

- Geometry: OPENapi VAO/VBO
- Compute/lighting: Vulkanizer compute + Radical shader math
- Audio: EAudio spatial + DSP, with Talisman culling in front of the
  mixer (`talisman on`)
- Post-FX: Vulkanizer upscale (Tensor Cores when available)

### Accessing the APIs

Plugins expose `get_api()` (e.g. `plugins.openapi.get_api()`) returning
the live API object; boot steps report which drivers are active. Missing
backends (no GPU, no audio device) degrade gracefully — see
[Plugin overview](../plugins/overview.md).