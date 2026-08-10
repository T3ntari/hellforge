# Portbaby — Syntax Version Porting

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [lure](lure.md) | [portbaby](portbaby.md) | [commands](../commands/portbaby-commands.md)

---

## Overview

**Portbaby v1.0.0** (author Tentari) ports E sources between syntax
versions: v1 machine, v1 human, v2 semantic, v3 shorthand and v4
polyrhythm/generative. It reports loss percentage and can generate proper
multi-file project structures (`index.ei` + `parts/` + `project.enx`).

## Version targets

`v1_machine`, `v1_human`, `v1`, `v2`, `v3`, `v4`, `v4_human`.

## Commands

Registered as `portbaby`, alias **`pb`** (`(alias)` in help):

- `portbaby <spec> --to <version> [--project] [--report] [--recursive]`
- `portbaby update <project.ei>` — update an old project to latest syntax
- `portbaby batch <glob> --to <version>` — batch conversion

`<spec>` may be a file, a directory, `/` (all) or a glob. See
[Portbaby commands](../commands/portbaby-commands.md).

## Note

The v5 canonical path is the language's future; portbaby converts legacy
v1–v4 sources, and `run.py compile <old.e> --to v5` is the migration path
(see [Syntax overview](../syntax/overview.md)).
