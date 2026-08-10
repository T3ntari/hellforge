# v2 Semantic Syntax (legacy)

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

> **LEGACY REFERENCE** — v2 compiles for backward compatibility with a
> deprecation warning. Write v5 (see [overview](overview.md)); convert
> with `run.py compile <old.e> --to v5`.

High-level musical constructs that describe intention rather than raw
notes.

### Section Header

```
[Intro]
[Verse]
[Chorus A]
[Bridge]
[Outro]
```

### Key & Scale Declaration

```
Key: Cmaj
Key: Amin
Key: F#min
```

### `arpeggio()`

```
arpeggio(Cmaj, root, up, 16)
arpeggio(Amin, 1, updown, 8)
```

| Param | Values |
|-------|--------|
| Chord | `Cmaj`, `Amin`, `F#dim`, `G7` |
| Octave | `root`, `1`, `2` |
| Direction | `up`, `down`, `updown`, `random` |
| Steps | Integer count |

### `chromatic_run()`

```
chromatic_run(start=60, steps=8, direction=up)
chromatic_run(72, 4, down)
```

### `walking_bass()`

```
walking_bass(Cmaj, 8)
walking_bass(Amin, 16, pattern=1)
```

---

**HELLFORGE OS v0.1.14.41-beta** — legacy reference
