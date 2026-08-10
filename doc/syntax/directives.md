# Directives — `@` Prefixed Controls

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

Directives set global or scoped interpreter state. They affect all
subsequent notes and generators.

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
| `@key` | Set key signature | `@key C major` |
| `@scale` | Set scale pattern | `@scale major` |
| `@root` | Set root note | `@root C4` |

### Performance (v5 piano layer)

| Directive | Description | Example |
|-----------|-------------|---------|
| `@vol` | Global volume (0–127) | `@vol 100` |
| `@dur` | Note duration — `:q` `:h` `:e` codes or ticks | `@dur:q` |
| `@vel` | Note velocity — `:mf` `:f` `:p` or 0–127 | `@vel:mf` |
| `@pedal` | Sustain pedal (0–127) | `@pedal:64` |
| `@art` | Articulation (`staccato`, `legato`, …) | `@art:staccato` |
| `@humanize` | MoE performance feel, strength 0–100 | `@humanize:15` |
| `@seed` | Deterministic randomness seed | `@seed 42` |

### Low-level render controls

`@master`, `@gain`, `@sr`, `@bit`, `@quality`, `@gc`, `@mem`, `@sub`,
`@bass_boost`, `@stereo_width`, `@neural` — work end-to-end from source
through MIDI export to WAV rendering.

### System

| Directive | Description | Example |
|-----------|-------------|---------|
| `@gc` | Garbage-collect variable scope | `@gc` |
| `@reset` | Reset all state to defaults | `@reset` |

### Plugin directives

Plugins can register their own `@directive` parsers via
`api.register_directive(pattern, handler)` — the compiler picks them up
like built-ins.

### Scope

Directives respect the same scope stack as variables. A directive inside a
section or loop reverts when the scope exits.

```
@bpm 120
[Verse]
@bpm 140       // overrides within Verse
C4q  E4q  G4q
               // bpm returns to 120 after Verse
```

---

**HELLFORGE OS v0.1.14.41-beta** — v5 directives
