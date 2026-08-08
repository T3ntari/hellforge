# HELLFORGE v1.0.0.0 ALPHA — PortBaby Commands

> Navigation: [doc/index.md](../index.md)

## port convert
**Syntax:** `port convert <input> -t <target_format> [--out <output>] [--options <json>]`
**Description:** Convert a composition from one format to another using the PortBaby portable-format engine. Supports cross-platform portability of `.e` files.
**Example:** `port convert lullaby.e -t midi --out lullaby.mid`
**Plugin:** portbaby

## port list
**Syntax:** `port list [--formats] [--presets] [--adapters]`
**Description:** List all supported target formats, conversion presets, or available PortBaby adapters.
**Example:** `port list --formats`
**Plugin:** portbaby

## port info
**Syntax:** `port info [--format <name>] [--version]`
**Description:** Display detailed information about a specific format, the PortBaby plugin version, or conversion pipeline details.
**Example:** `port info --format midi`
**Plugin:** portbaby

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
