**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [overview](gpu/overview.md) | [radical-gpu](gpu/radical-gpu.md) | [opengl-api](gpu/opengl-api.md) | [vulkan-api](gpu/vulkan-api.md) | [tensor-cores](gpu/tensor-cores.md) | [shader-compilation](gpu/shader-compilation.md)

## Tensor Core Utilization

TensorSHARP is the Tensor Core abstraction layer within Piano DSL. It provides automatic matrix operation acceleration on NVIDIA hardware.

### Supported Modes

| Mode | Precision | Use Case |
|---|---|---|
| TF32 | 19-bit mantissa | Training, general compute |
| FP16 | 16-bit half | Audio DSP, inference |
| INT8 | 8-bit integer | Quantized inference, UI effects |

### Automatic Selection

The runtime queries the GPU for Tensor Core capabilities and selects the optimal mode based on the operation type:

```piano
// Auto-selected based on GPU and precision hints
let result = tensorsharp.matmul(A, B, precision = "auto")
```

### Fallback

On GPUs without Tensor Cores (or when TensorSHARP is disabled), operations fall back to standard FP32 shader compute through Radical.

---

**HELLFORGE v1.0.0.0 ALPHA — Piano DSL Documentation**