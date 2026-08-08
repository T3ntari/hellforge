**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [custom-plugin](examples/custom-plugin.md) | [gpu-compute](examples/gpu-compute.md) | [game-engine](examples/game-engine.md)

## GPU Compute with Radical and TensorSHARP

This example shows batch matrix multiplication using Radical compute shaders and TensorSHARP.

### Define the Kernel

```piano
kernel batch_matmul {
    input: matrix[1024, 1024] A
    input: matrix[1024, 1024] B
    output: matrix[1024, 1024] C

    @compute @workgroup(16, 16, 1)
    fn main(@builtin(global_invocation_id) id: vec3u) {
        let row = id.x
        let col = id.y
        C[row][col] = dot(A[row][:], B[:][col])
    }
}
```

### Dispatch

```piano
let A = tensor.randn([1024, 1024])
let B = tensor.randn([1024, 1024])
let C = tensorsharp.matmul(A, B, precision = "tf32")
```

### Performance Notes

- TF32 mode uses Tensor Cores on Ampere+ GPUs
- Falls back to FP32 on non-Tensor Core hardware
- Work group size is auto-tuned for the target GPU

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**