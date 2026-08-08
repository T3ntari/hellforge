# HELLFORGE v1.0.0.0 ALPHA — Talisman Commands

> Navigation: [doc/index.md](../index.md)

## talisman on
**Syntax:** `talisman on [--profile <name>]`
**Description:** Enable the Talisman processing engine with an optional optimization profile for note computation culling and core distribution.
**Example:** `talisman on --profile aggressive`
**Plugin:** talisman

## talisman off
**Syntax:** `talisman off`
**Description:** Disable the Talisman processing engine and revert to default note computation behavior.
**Example:** `talisman off`
**Plugin:** talisman

## talisman local
**Syntax:** `talisman local [--force] [--cores <n>]`
**Description:** Constrain Talisman processing to local CPU cores only, optionally specifying the number of cores to use.
**Example:** `talisman local --cores 4`
**Plugin:** talisman

## talisman backup
**Syntax:** `talisman backup [--path <dir>] [--restore <file>]`
**Description:** Backup or restore the current Talisman configuration, including culling rules and core affinity settings.
**Example:** `talisman backup --path ./talisman_backup`
**Plugin:** talisman

## talisman rotate-id
**Syntax:** `talisman rotate-id [--interval <n>] [--mode <round-robin|random|adaptive>]`
**Description:** Configure core rotation settings — rotate processing across available cores at a specified interval and mode.
**Example:** `talisman rotate-id --mode round-robin`
**Plugin:** talisman

## talisman inspect
**Syntax:** `talisman inspect [--verbose] [--output <file>]`
**Description:** Inspect current Talisman processing state, culling statistics, core utilization, and optimization diagnostics.
**Example:** `talisman inspect --verbose`
**Plugin:** talisman

## talisman stats
**Syntax:** `talisman stats [--reset] [--interval <s>]`
**Description:** Display real-time Talisman performance statistics including culling rate, core load balance, and processing throughput.
**Example:** `talisman stats --interval 5`
**Plugin:** talisman

## talisman status
**Syntax:** `talisman status`
**Description:** Display the current operational status of the Talisman engine, including enabled state, active profile, and core configuration.
**Example:** `talisman status`
**Plugin:** talisman

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
