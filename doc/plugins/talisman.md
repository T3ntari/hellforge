# Talisman — Audio Culling, Privacy & QOL

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [humanize](humanize.md) | [eaudio](eaudio.md) | [talisman](talisman.md) | [commands](../commands/talisman-commands.md)

---

## Overview

**Talisman v1.1.0** (author Tentari) is the audio culling, privacy & QOL
engine. On compile it removes inaudible notes (psychoacoustic masking /
occlusion), and it ships local-only mode, auto-backup, device-ID rotation,
event inspection and compile stats.

## Features

- **Culling & occlusion** — a `post_compile` hook removes inaudible /
  occluded events; `talisman on|off` toggles it
- **Local-only mode** — `talisman local` disables backend calls entirely
- **Auto-backup** — `talisman backup on` snapshots every compiled event
  set to timestamped JSON under `.e_backups/`
- **Device-ID rotation** — `talisman rotate-id`
- **Inspection & stats** — `talisman inspect <file.e>`, `talisman stats`
  (compile count, culled/occluded totals)

## Commands

`talisman <on|off|local|backup|rotate-id|inspect|stats|status>` — see
[Talisman commands](../commands/talisman-commands.md).
