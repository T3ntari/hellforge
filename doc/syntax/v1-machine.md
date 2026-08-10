# v1 #MACHINE Mode — Token-Based Note Format (legacy)

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

> **LEGACY REFERENCE** — v1 compiles for backward compatibility with a
> deprecation warning. Machine lines (`T0 N60 D500 V80`) are **not** valid
> v5. Write v5 (see [overview](overview.md)); convert with
> `run.py compile <old.e> --to v5`.

## Grammar

```
T<time> N<midi> D<duration> V<velocity>
```

| Token | Field | Range | Description |
|-------|-------|-------|-------------|
| `T` | Time | `0` – `INT32_MAX` | Tick position (absolute or relative) |
| `N` | Note | `0` – `127` | MIDI note number (60 = Middle C) |
| `D` | Duration | `1` – `INT32_MAX` | Note length in ticks |
| `V` | Velocity | `0` – `127` | Note velocity / volume |

## Examples

```
#MACHINE
T0 N60 D480 V100
T480 N64 D240 V80
T720 N67 D960 V90
```

## Ties & Rests

- Tie into previous note: omit `T`
- Rest: set `N-1`

```
#MACHINE
T0 N60 D480 V100   N64 D240 V80
N-1 D120 V0
```

## Token Reference

| Token | Shorthand | Example |
|-------|-----------|---------|
| `TIME` | `T` | `T0`, `T+480` |
| `NOTE` | `N` | `N60`, `N-1` |
| `DUR` | `D` | `D480`, `D.` (previous) |
| `VEL` | `V` | `V100`, `V.` (previous) |

---

**HELLFORGE OS v0.1.14.41-beta** — legacy reference
