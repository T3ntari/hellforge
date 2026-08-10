# HELLFORGE — Portbaby Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [portbaby-commands](portbaby-commands.md)

The **portbaby** plugin (v1.0.0) ports E sources between syntax versions
(v1 machine, v1 human, v2 semantic, v3 shorthand, v4 polyrhythm/generative),
with loss-percentage reports and multi-file project generation. Registered
as `portbaby`, alias **`pb`** (marked `(alias)` in eshell help).

## portbaby
**Syntax:** `portbaby <spec> --to <version> [--project] [--report] [--recursive]`
**Description:** Convert a file/dir/glob to the target version. Versions: `v1_machine`, `v1_human`, `v1`, `v2`, `v3`, `v4`, `v4_human`. `<spec>` may be a file, directory, `/` (all) or a glob.
**Example:** `portbaby songs/aurora_nocturne.e --to v3`

## portbaby --to v1_human / v1_machine
**Syntax:** `portbaby <file> --to v1_human` · `portbaby <file> --to v1_machine`
**Description:** Convert to v1 human-readable or machine token syntax.

## portbaby --project
**Syntax:** `portbaby <project.ei> --to v4 --project`
**Description:** Convert with a multi-file project structure (`index.ei` + `parts/`).

## portbaby --report
**Syntax:** `portbaby <file> --report`
**Description:** Show the conversion report (loss percentage) without converting.

## portbaby update
**Syntax:** `portbaby update <project.ei>`
**Description:** Update an old project to the latest syntax.

## portbaby batch
**Syntax:** `portbaby batch <glob> --to v3`
**Description:** Batch-convert multiple files.

---

**Plugin:** portbaby · see [Portbaby plugin page](../plugins/portbaby.md)
