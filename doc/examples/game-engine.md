**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [custom-plugin](examples/custom-plugin.md) | [gpu-compute](examples/gpu-compute.md) | [game-engine](examples/game-engine.md)

## Building a Game Engine

This example demonstrates combining OPENapi, Vulkanizer, and EAudio to build the foundation of a game engine.

### Setup

```piano
openapi.init(context = "game")
vulkanizer.init(raytracing = true)
eaudio.init()
```

### Rendering Loop

```piano
loop {
    // OPENapi handles forward rendering
    openapi.clear(vec4(0.1, 0.1, 0.1, 1.0))
    openapi.draw(mesh)

    // Vulkanizer handles compute and post-processing
    vulkanizer.compute.dispatch("post_process", params)
    vulkanizer.upscale(input, output)

    // EAudio renders spatial audio
    eaudio.listener.update(camera.position, camera.orientation)
    eaudio.render()

    openapi.swap()
}
```

### Full Pipeline

- Geometry: OPENapi VAO/VBO
- Lighting: Vulkanizer compute
- Audio: EAudio spatial + DSP
- Post-FX: Vulkanizer upscale

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**