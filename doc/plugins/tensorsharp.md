# TensorSHARP — NVIDIA Tensor Core Acceleration

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [commands](../commands/tensorsharp-commands.md)

---

## Overview

**tensorsharp v1.0.0** (author Tentari) accelerates E math on NVIDIA
**Tensor Cores** using CuPy with TF32/FP16 mixed precision. It depends on
Radical for the GPU compute runtime and registers a math evaluator at
**priority 3** (highest). Fallback chain: TensorSHARP → Radical → LURE →
Python. Requires an NVIDIA GPU + CUDA toolkit +
`pip install cupy-cuda12x` (or `pip install cupy` for auto-detection).

## Capabilities

- Tensor Core count, compute capability, precision (FP16 / TF32 / INT8)
  reported by `tensorsharp status` / `tensorsharp cores`
- Ops executed, total GFLOPS and evaluation counts tracked per session
- Skipped at boot (with a `requires Radical` note) when Radical is
  unavailable

## Commands

`tensorsharp status|benchmark|cores|info` — see
[TensorSHARP commands](../commands/tensorsharp-commands.md).
