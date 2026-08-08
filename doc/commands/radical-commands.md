# HELLFORGE v1.0.0.0 ALPHA — Radical Commands

> Navigation: [doc/index.md](../index.md)

## radical status
**Syntax:** `radical status`
**Description:** Display the current status of the Radical GPU compute engine, including GPU model, driver version, and compute mode.
**Example:** `radical status`
**Plugin:** radical

## radical gpu
**Syntax:** `radical gpu [--list] [--select <index>]`
**Description:** List available GPUs or select a specific GPU device for Radical compute operations.
**Example:** `radical gpu --select 0`
**Plugin:** radical

## radical vram
**Syntax:** `radical vram [--stats] [--clear]`
**Description:** Show VRAM usage statistics or clear the VRAM note buffer allocated by Radical.
**Example:** `radical vram --stats`
**Plugin:** radical

## radical benchmark
**Syntax:** `radical benchmark [--iterations <n>] [--size <n>]`
**Description:** Run a GPU compute benchmark to measure FLOPs, memory bandwidth, and note-generation throughput.
**Example:** `radical benchmark --iterations 50000`
**Plugin:** radical

## radical shaders
**Syntax:** `radical shaders list|compile|info [name]`
**Description:** List, compile, or inspect GPU shader programs used for note generation.
**Example:** `radical shaders list`
**Plugin:** radical

## radical info
**Syntax:** `radical info [--detailed]`
**Description:** Display detailed information about the Radical plugin version, supported features, and GPU capabilities.
**Example:** `radical info --detailed`
**Plugin:** radical

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
