# Loops — v5 (`for`, ranges) and legacy (`repeat`, `for $i`)

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

> **v5 note:** canonical loops are the `for` family — scale loops,
> range loops, list/run loops — all with `break`/`continue`. The `while`
> loop and `for $i = 0 to N step S` are **banned in v5** (legacy
> constructs emit warnings; convert with `run.py compile --to v5`).

## v5 `for` loops

Scale loop (v5 statement set):

```
for $n in scale(C major, 4, 1) {
    print $n
    play note($n) @dur:q @vel:mp
}
```

Range loop:

```
for $i in 1..4 {
    assert $i < 5, "too many iterations"
}
```

List/run loops and `break`/`continue`:

```
for $x in [C4, E4, G4] {
    if $x == E4 { continue }
    play note($x) @dur:q
}
for $i in 1..16 {
    play note(C4) @dur:e
    break                     // stop early
}
```

## Legacy `repeat N`

Repeats the block `N` times. No index variable.

```
repeat 4 {
  C4q  E4q  G4q  C5q
}
```

## Legacy `for $i`

Iterates with a counter variable `$i` (starts at 0):

```
for 8 {
  T{$i * 480} N{$i + 60} D240 V100
}
```

Range form (`for $i in 4..12`) is valid v5 as shown above.

## Legacy `while` — banned in v5

```
$pos = 0
while {$pos < 4800} {     // legacy — not v5
  T{$pos} N60 D240 V100
  $pos = {$pos + 480}
}
```

Prefer a range loop with `break` in v5.

## Nested Loops

```
for 4 {        // bars
  for 4 {      // beats
    C4q
  }
}
```

## Variable Increment Inside Loops

```
$octave = 4
repeat 8 {
  C{$octave}q  E{$octave}q  G{$octave}q
  $octave = {$octave + 1}
}
```

---

**HELLFORGE OS v0.1.14.41-beta** — v5 loops canonical
