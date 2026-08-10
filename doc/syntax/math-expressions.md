# Math Expressions — `{$expr}`

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

Any `{$...}` block is evaluated as a mathematical expression at parse
time.

### Syntax

```
{$ 2 + 2 }
{$ $bpm / 2 }
{$ pow(3, 4) }
{$ rand(60, 72) }
```

### Evaluator chain

Expressions are evaluated by the registered math evaluators, in priority
order: **TensorSHARP** (Tensor Cores, priority 3) → **Radical** (GPU
shader math, priority 5) → **LURE** (LuaJIT, priority 10) → **Python**
(priority 100, always available). Any GPU/CUDA failures fall back down the
chain automatically.

### Operands

| Operator | Description |
|----------|-------------|
| `+` | Addition |
| `-` | Subtraction / negation |
| `*` | Multiplication |
| `/` | Float division |
| `//` | Integer division |
| `%` | Modulo |
| `^` | Exponentiation |
| `==` | Equality comparison |

### Built-in Functions

| Function | Description |
|----------|-------------|
| `rand(a, b)` | Random integer in `[a, b]` |
| `pow(x, y)` | `x` raised to `y` |
| `sqrt(x)` | Square root |
| `abs(x)` | Absolute value |
| `min(a, b)` | Minimum |
| `max(a, b)` | Maximum |
| `clamp(v, a, b)` | Clamp `v` to range |
| `round(x)` | Round to nearest integer |
| `floor(x)` | Floor |
| `ceil(x)` | Ceiling |

In v5, `pick(...)` and `rand(...)` are deterministic under `@seed 42`.

### Usage in Positions

```
T{$ 0 + $pos } N60 D480 V100
T{$ pos + 480 } N64 D240 V80
```

---

**HELLFORGE OS v0.1.14.41-beta** — v5 math
