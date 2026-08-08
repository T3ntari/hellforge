# HELLFORGE v1.0.0.0 ALPHA — Lure Commands

> Navigation: [doc/index.md](../index.md)

## lure status
**Syntax:** `lure status`
**Description:** Display the current status of the Lure acceleration engine, including accelerator type (CUDA/OpenCL), memory usage, and active acceleration sessions.
**Example:** `lure status`
**Plugin:** lure

## lure benchmark
**Syntax:** `lure benchmark [--size <n>] [--iterations <n>] [--type <cpu|gpu|all>]`
**Description:** Run a benchmark measuring acceleration gain for note generation, comparing CPU vs accelerated performance.
**Example:** `lure benchmark --iterations 10000 --type all`
**Plugin:** lure

## lure async
**Syntax:** `lure async [--submit <file.e>] [--status] [--cancel <id>]`
**Description:** Submit a composition for asynchronous accelerated processing, check status of async jobs, or cancel a running job.
**Example:** `lure async --submit complex_beat.e`
**Plugin:** lure

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
