# HELLFORGE — Talisman Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [talisman-commands](talisman-commands.md)

The **talisman** plugin (v1.1.0) is the audio culling, privacy & QOL
engine: it removes inaudible/occluded notes on compile (post-compile hook),
supports a local-only mode, auto-backup of compiled events, device-ID
rotation, event inspection and compile stats.

## talisman on / off
**Syntax:** `talisman on` · `talisman off`
**Description:** Enable/disable audio culling and occlusion on compile.
**Example:** `talisman on`

## talisman local
**Syntax:** `talisman local [on|off]`
**Description:** Toggle local-only mode (backend calls disabled).
**Example:** `talisman local on`

## talisman backup
**Syntax:** `talisman backup [on|off]`
**Description:** Toggle auto-backup of every compiled event set (timestamped JSON under `.e_backups/`).
**Example:** `talisman backup on`

## talisman rotate-id
**Syntax:** `talisman rotate-id`
**Description:** Rotate the device ID.
**Example:** `talisman rotate-id`

## talisman inspect
**Syntax:** `talisman inspect <file.e>`
**Description:** Inspect a source file's events.
**Example:** `talisman inspect song.e`

## talisman stats
**Syntax:** `talisman stats`
**Description:** Compile statistics: compile count, culled/occluded events.
**Example:** `talisman stats`

## talisman status
**Syntax:** `talisman status`
**Description:** Overall plugin state.
**Example:** `talisman status`

---

**Plugin:** talisman · see [Talisman plugin page](../plugins/talisman.md)
