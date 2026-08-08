# **HELLFORGE v1.0.0.0 ALPHA — tensorsharp: Tensor Core Acceleration**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**tensorsharp** accelerates matrix and tensor operations using NVIDIA Tensor Cores and AMD Matrix Cores. It wraps CuPy for GPU-backed array operations with automatic CUDA capability detection.

## CuPy Integration

tensorsharp interfaces with CuPy (`cupy.ndarray`) for all tensor operations. The plugin manages a CuPy memory pool and provides zero-copy views into radical-managed GPU buffers where possible.

## CUDA Detection

On startup, tensorsharp queries:

- CUDA driver version
- CUDA runtime version
- Compute capability (SM version) per device
- Tensor Core availability (SM 7.0+ for NVIDIA)
- cuBLAS and cuDNN versions

If no CUDA-capable device is found, tensorsharp degrades to a CPU-backed NumPy fallback.

## Matmul Benchmarks

tensorsharp runs a microbenchmark on each tensor operation to select the optimal algorithm:

| Matrix Size | Algorithm Selected | TFLOPS (A100) |
|-------------|-------------------|---------------|
| 16×16–64×64 | cuBLAS Lt          | 0.8–1.2       |
| 128×128–512×512 | cuBLAS GemmEx   | 2.4–4.1       |
| 1024×1024+  | cuBLAS + Tensor Core | 9.7–12.3    |

Results are cached per (shape, dtype, device) tuple and invalidated on device change.

---

**API Reference:** `#include <tensorsharp/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — tensorsharp: Tensor Core Acceleration**
