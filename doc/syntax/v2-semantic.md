# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## v2 Semantic Syntax

High-level musical constructs that describe intention rather than raw notes.

### Section Header

```
[Intro]
[Verse]
[Chorus A]
[Bridge]
[Outro]
```

Sections provide structural organisation and can be referenced by loops and directives.

### Key & Scale Declaration

```
Key: Cmaj
Key: Amin
Key: F#min
```

Sets the tonal centre for subsequent semantic generators.

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

Generates a chromatic sequence of `steps` notes starting from MIDI note `start`.

### `walking_bass()`

```
walking_bass(Cmaj, 8)
walking_bass(Amin, 16, pattern=1)
```

Creates chord-tone walking bass lines.

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
