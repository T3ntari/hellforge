# HELLFORGE v1.0.0.0 ALPHA — TensorSharp Commands

> Navigation: [doc/index.md](../index.md)

## tensorsharp status
**Syntax:** `tensorsharp status`
**Description:** Display the current status of the TensorSharp tensor compute engine, including core count, tensor memory pool, and active sessions.
**Example:** `tensorsharp status`
**Plugin:** tensorsharp

## tensorsharp cores
**Syntax:** `tensorsharp cores [--list] [--pin <id>]`
**Description:** List available tensor processing cores or pin a specific core for tensor operations.
**Example:** `tensorsharp cores --list`
**Plugin:** tensorsharp

## tensorsharp benchmark
**Syntax:** `tensorsharp benchmark [--ops <n>] [--dims <n>]`
**Description:** Run a tensor operation benchmark measuring matrix multiply, convolution, and note-tensor conversion throughput.
**Example:** `tensorsharp benchmark --dims 512`
**Plugin:** tensorsharp

## tensorsharp info
**Syntax:** `tensorsharp info [--full]`
**Description:** Display TensorSharp plugin version, supported tensor operations, and hardware acceleration backends.
**Example:** `tensorsharp info --full`
**Plugin:** tensorsharp

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
