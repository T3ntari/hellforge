# Variables — `$var`

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

Variables are defined with `$` prefix and can hold integers, floats,
strings, or pattern sequences.

### Definition

```
$bpm = 120
$vel = 100
$notes = [60, 64, 67, 72]
$name = "verse"
$pattern = euclidean(8, 3)
```

### Interpolation

Reference a variable anywhere a value is expected:

```
T{$i * 480} N{$notes[$idx]} D480 V{$vel}
```

### Scope Stack

| Scope | Visibility |
|-------|------------|
| Global | Entire file |
| Section | Within `[SectionName]` block |
| Loop body | Iteration-local, discarded after loop |
| Expression | Temporary within `{$...}` evaluation |

Inner scopes shadow outer ones. Variables are looked up from innermost to
outermost.

### Scope Example

```
$bpm = 120          // global

[Verse]
$bpm = 140          // section-level, shadows global
@bpm {$bpm}

repeat 4 {
  $bpm = 160        // loop-local, shadows section
  @bpm {$bpm}
}
```

### Reassignment

```
$count = 0
repeat 10 {
  $count = {$count + 1}
  T{$count * 240} N60 D120 V100
}
```

### Plugins can handle variables too

Plugins may register custom variable handlers
(`api.register_variable_handler(fn)`) — the reference plugin handles
`$repeat_4` / `$repeat_8` style names (see
[`examples/plugins/example_plugin.py`](../../examples/plugins/example_plugin.py)).

---

**HELLFORGE OS v0.1.14.41-beta** — v5 variables
