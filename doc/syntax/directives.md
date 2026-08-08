# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## Directives — `@` Prefixed Controls

Directives set global or scoped interpreter state. They affect all subsequent notes and generators.

### Tempo

| Directive | Description | Example |
|-----------|-------------|---------|
| `@bpm` | Beats per minute | `@bpm 120` |
| `@fast` | Alias for 140 BPM | `@fast` |
| `@slow` | Alias for 60 BPM | `@slow` |
| `@moderate` | Alias for 100 BPM | `@moderate` |
| `@allegro` | Alias for 120 BPM | `@allegro` |
| `@adagio` | Alias for 70 BPM | `@adagio` |

### Musical Context

| Directive | Description | Example |
|-----------|-------------|---------|
| `@key` | Set key signature | `@key Cmaj` |
| `@scale` | Set scale pattern | `@scale major` |
| `@root` | Set root note | `@root C4` |

### Performance

| Directive | Description | Example |
|-----------|-------------|---------|
| `@vol` | Global volume (0–127) | `@vol 100` |
| `@ch` | MIDI channel (0–15) | `@ch 1` |
| `@dur` | Default note duration | `@dur 480` |
| `@vel` | Default note velocity | `@vel 90` |
| `@octave` | Default octave offset | `@octave 4` |

### System

| Directive | Description | Example |
|-----------|-------------|---------|
| `@gc` | Garbage-collect variable scope | `@gc` |
| `@reset` | Reset all state to defaults | `@reset` |

### Scope

Directives respect the same scope stack as variables. A directive inside a section or loop reverts when the scope exits.

```
@bpm 120
[Verse]
@bpm 140       // overrides within Verse
C4q  E4q  G4q
               // bpm returns to 120 after Verse
```

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
