# HELLFORGE — TensorSHARP Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [tensorsharp-commands](tensorsharp-commands.md)

The **tensorsharp** plugin (v1.0.0) accelerates E math on NVIDIA **Tensor
Cores** (CuPy, TF32/FP16 mixed precision). It depends on Radical for the
GPU compute runtime and registers a math evaluator at **priority 3**
(highest). Fallback chain: TensorSHARP → Radical → LURE → Python.
Requires an NVIDIA GPU + CUDA toolkit + `pip install cupy-cuda12x`.

## tensorsharp status
**Syntax:** `tensorsharp status`
**Description:** CUDA availability, Tensor Core count, precision, GPU name, CuPy version, ops executed, total GFLOPS, evaluations — or "inactive" with install hints.
**Example:** `tensorsharp status`

## tensorsharp cores
**Syntax:** `tensorsharp cores`
**Description:** Tensor Core configuration: GPU, compute capability, core count, max precision, FP16/TF32/INT8 support.
**Example:** `tensorsharp cores`

## tensorsharp benchmark
**Syntax:** `tensorsharp benchmark`
**Description:** Tensor operation benchmark (matrix multiply etc.).
**Example:** `tensorsharp benchmark`

## tensorsharp info
**Syntax:** `tensorsharp info`
**Description:** Plugin summary and capabilities.
**Example:** `tensorsharp info`

---

**Plugin:** tensorsharp · see [TensorSHARP plugin page](../plugins/tensorsharp.md) and [GPU docs](../gpu/tensor-cores.md)
