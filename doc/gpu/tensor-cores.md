**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [radical-gpu](radical-gpu.md) | [opengl-api](opengl-api.md) | [vulkan-api](vulkan-api.md) | [tensor-cores](tensor-cores.md) | [shader-compilation](shader-compilation.md)

## Tensor Core Utilization

TensorSHARP (v1.0.0) accelerates E math on NVIDIA **Tensor Cores** via
CuPy with mixed precision — the highest-priority math evaluator
(priority 3).

### Supported Modes

| Mode | Precision | Use Case |
|---|---|---|
| TF32 | 19-bit mantissa | General compute |
| FP16 | 16-bit half | Audio DSP, inference |
| INT8 | 8-bit integer | Quantized inference, UI effects |

### Requirements

NVIDIA GPU + CUDA toolkit + `pip install cupy-cuda12x` (or `pip install
cupy` for auto-detection). The plugin skips at boot with a "requires
Radical" note when the GPU compute runtime is missing.

### Status

```
tensorsharp status     # CUDA, Tensor Cores, precision, GPU, GFLOPS
tensorsharp cores      # compute capability, FP16/TF32/INT8 support
tensorsharp benchmark  # tensor op benchmark
```

### Fallback

On GPUs without Tensor Cores (or when TensorSHARP is unavailable),
operations fall back to Radical's FP32 shader compute, then LURE, then
Python.

---

**HELLFORGE OS v0.1.14.41-beta** — Tensor Cores