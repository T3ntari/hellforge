# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## v3 Extended Syntax — Shorthand Notations

Piano DSL v3 introduces compact notation inspired by guitar tabs and trackers.

### Note + Octave

```
C4  D4  E4  F4  G4  A4  B4  C5
C#4  Db4  F#5  Bb3
```

Letter note names with optional accidental (`#` or `b`) and octave number. Middle C = `C4`.

### Duration Codes

| Code | Duration |
|------|----------|
| `w` | Whole note |
| `h` | Half note |
| `q` | Quarter note |
| `e` | Eighth note |
| `s` | Sixteenth note |
| `t` | Thirty-second note |

```
C4q  D4q  E4h  F4e  G4e  A4s  B4s  C5w
```

Dotted durations: `C4q.` (dotted quarter), `F4e..` (double-dotted eighth).

### Tempo Aliases

| Alias | BPM |
|-------|-----|
| `@fast` | 140 |
| `@slow` | 60 |
| `@moderate` | 100 |
| `@allegro` | 120 |
| `@adagio` | 70 |

```
@fast
C4q  E4q  G4q  C5q
```

### Rest Shorthand

```
Rq  Rh  Re
```

`R` followed by a duration code produces a rest.

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
