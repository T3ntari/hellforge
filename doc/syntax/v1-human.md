# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## #HUMAN Mode — Natural-Language Style

Activate with `#HUMAN` (or `#HUM`). Write music in a readable, declarative style.

### Commands

#### `play note()`

```
play note(60) @dur 480 @vel 100
```

- `play note(<midi>)` — play a single note
- `@dur <ticks>` — duration in ticks
- `@vel <0-127>` — velocity

#### `play chord()`

```
play chord(60, 64, 67) @dur 960 @vel 90
```

- `play chord(<midi1>, <midi2>, ...)` — play multiple notes simultaneously
- `@dur` applies to all notes in chord
- `@vel` applies to all notes in chord

#### `@ch` — Channel Selector

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

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
