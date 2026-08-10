# v1 #HUMAN Mode — Natural-Language Style (legacy)

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

> **LEGACY REFERENCE** — v1 human mode compiles for backward
> compatibility with a deprecation warning. Write v5 (see
> [overview](overview.md)); convert with `run.py compile <old.e> --to v5`.

## Commands

### `play note()`

```
play note(60) @dur 480 @vel 100
```

- `play note(<midi>)` — play a single note
- `@dur <ticks>` — duration in ticks
- `@vel <0-127>` — velocity

### `play chord()`

```
play chord(60, 64, 67) @dur 960 @vel 90
```

- `play chord(<midi1>, <midi2>, ...)` — play multiple notes simultaneously
- `@dur` / `@vel` apply to all notes in the chord

### `@ch` — Channel Selector

```
play note(60) @ch 1
play note(72) @ch 2
```

Attach `@ch <0-15>` to route to a specific MIDI channel.

### Globals

Set once, affect all subsequent notes until changed:

```
@dur 480
@vel 100
@ch 0

play note(60)
play note(64)
play note(67)
```

> v5 note: `@dur:q @vel:mf` style (named durations and dynamic markings)
> is the canonical modern form.

---

**HELLFORGE OS v0.1.14.41-beta** — legacy reference
