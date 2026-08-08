# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## Loops — `repeat`, `for`, `while`

Three loop constructs for iterative note generation.

### `repeat N`

Repeats the block `N` times. No index variable.

```
repeat 4 {
  C4q  E4q  G4q  C5q
}
```

### `for $i`

Iterates with a counter variable `$i` (starts at 0).

```
for 8 {
  T{$i * 480} N{$i + 60} D240 V100
}
```

Supports optional range:

```
for $i in 4..12 {
  T{$i * 240} N{$i + 48} D120 V80
}
```

### `while`

Repeats while a condition (inside `{$...}`) is truthy.

```
$pos = 0
while {$pos < 4800} {
  T{$pos} N60 D240 V100
  $pos = {$pos + 480}
}
```

### Nested Loops

```
for 4 {        // bars
  for 4 {      // beats
    C4q
  }
}
```

### Variable Increment Inside Loops

```
$octave = 4
repeat 8 {
  C{$octave}q  E{$octave}q  G{$octave}q
  $octave = {$octave + 1}
}
```

### Break

```
repeat 100 {
  T{$i * 240} N60 D120 V100
  break {$i >= 7}
}
```

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
