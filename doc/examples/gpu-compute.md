**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [custom-plugin](custom-plugin.md) | [gpu-compute](gpu-compute.md) | [game-engine](game-engine.md)

## GPU Compute with Radical and TensorSHARP

This example shows how the GPU math drivers accelerate E expressions.

### The evaluator chain

Every `{$...}` math expression is evaluated by the best available
evaluator: **TensorSHARP** (Tensor Cores, priority 3) → **Radical** (GLSL
compute shaders, priority 5) → **LURE** (LuaJIT, priority 10) → **Python**
(priority 100). You never call the GPU explicitly in E — it happens
underneath.

```e
$result = {$a * $b + 1}          // routed to the best evaluator
$picked = pick(C5 E5 G5)         // v5 deterministic choice (@seed 42)
```

### Managing the GPU

```text
krip gpu list          // which GPUs exist
krip gpu 0,1           // use GPUs 0 and 1 (CUDA_VISIBLE_DEVICES)
krip engine vulkan     // default engine
radical status         // GPU model, VRAM, compute support
radical vram 4096      // cap VRAM
tensorsharp status     // Tensor Cores, precision, GFLOPS
```

### Fallbacks

- No GPU → Radical unavailable at boot, LURE/Python take over
- No Tensor Cores → TensorSHARP skips, Radical handles it
- No lupa → Python pool handles everything

### Performance notes

- TF32 mode uses Tensor Cores on Ampere+ GPUs
- Shader compilation is cached (`radical shaders`)
- `lure benchmark` / `lure async` measure the compile-side speedups

See [GPU overview](../gpu/overview.md) and
[Radical commands](../commands/radical-commands.md).