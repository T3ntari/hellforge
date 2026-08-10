# v4 Polyrhythm & Euclidean Rhythm (valid in v5)

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

> **LEGACY REFERENCE** — polyrhythm and Euclidean generators are **valid
> v5** (a superset: no demotion). In v5 use the canonical forms
> `[C4 E4 G4](3:2)` and `E(5,4)`; the v4 generator forms below also
> compile.

### Polyrhythm Declaration

```
polyrhythm(3, 2)
polyrhythm(5, 4, @bpm 120)
polyrhythm(7, 8, @dur 480)
```

`polyrhythm(top, bottom)` — plays `top` notes evenly spaced over `bottom`
beats. Third argument can be `@bpm` or `@dur` to override timing.

v5 canonical form — chord + ratio:

```
[C4 E4 G4](3:2)
```

### Euclidean Rhythm

```
euclidean(steps, pulses)
euclidean(8, 3)
euclidean(16, 7, @offset 2)
```

`euclidean(steps, pulses)` — distributes `pulses` hits evenly across
`steps` positions using Bjorklund's algorithm. Optional `@offset` rotates
the pattern.

v5 canonical form:

```
E(5,4)
```

### Examples

```
@bpm 120

// 3-over-2 polyrhythm (v5 canonical)
[C4 E4 G4](3:2)

// Euclidean hi-hat pattern (v5 canonical)
E(8,3)
```

### Pattern Output

Both generators produce tick-positioned events. Patterns can be assigned
to variables and looped:

```
$hat = euclidean(8, 3)
repeat 4 { $hat }
```

---

**HELLFORGE OS v0.1.14.41-beta** — v4 polyrhythm/Euclidean: valid v5
