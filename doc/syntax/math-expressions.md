# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## Math Expressions — `{$expr}`

Any `{$...}` block is evaluated as a mathematical expression at parse time.

### Syntax

```
{$ 2 + 2 }
{$ $bpm / 2 }
{$ pow(3, 4) }
{$ rand(60, 72) }
```

### AST Pipeline

Every expression goes through a four-stage pipeline:

1. **Lexer** — tokenises operators, numbers, identifiers, parentheses
2. **Parser** — builds an Abstract Syntax Tree (AST)
3. **Evaluator Chain** — resolves operators left-to-right with precedence
4. **Reducer** — folds constants, substitutes variables

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

### Usage in Positions

```
T{$ 0 + $pos } N60 D480 V100
T{$ pos + 480 } N64 D240 V80
```

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
