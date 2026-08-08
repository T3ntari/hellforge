# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## v4 Polyrhythm & Euclidean Rhythm

v4 introduces polyrhythmic generators and Euclidean rhythm patterns.

### Polyrhythm Declaration

```
polyrhythm(3, 2)
polyrhythm(5, 4, @bpm 120)
polyrhythm(7, 8, @dur 480)
```

`polyrhythm(top, bottom)` — plays `top` notes evenly spaced over `bottom` beats. Third argument can be `@bpm` or `@dur` to override timing.

### Euclidean Rhythm

```
euclidean(steps, pulses)
euclidean(8, 3)
euclidean(16, 7, @offset 2)
```

`euclidean(steps, pulses)` — distributes `pulses` hits evenly across `steps` positions using Bjorklund's algorithm. Optional `@offset` rotates the pattern.

### Examples

```
@bpm 120

// 3-over-2 polyrhythm
polyrhythm(3, 2)

// Euclidean hi-hat pattern
euclidean(8, 3)

// Combined
#MACHINE
T0   N60 D120 V100
polyrhythm(4, 3)
euclidean(12, 5)
```

### Pattern Output

Both generators produce tick-positioned events that can feed into any syntax version. Patterns can be assigned to variables and looped:

```
$hat = euclidean(8, 3)
repeat 4 { $hat }
```

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
