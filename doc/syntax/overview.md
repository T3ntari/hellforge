# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md)

---

## Syntax System Overview

HELLFORGE Piano DSL provides **four syntax versions**, each building on the last. All versions can be freely mixed in a single `.piano` file.

### Version 1 — Machine & Human

| Mode | Description |
|------|-------------|
| `#MACHINE` | Token-based note format: `T<N> N<MIDI> D<DUR> V<VEL>` |
| `#HUMAN` | Natural-language style: `play note()`, `play chord()` with `@dur`, `@vel`, `@ch` |

→ [v1 Machine Reference](v1-machine.md) · [v1 Human Reference](v1-human.md)

### Version 2 — Semantic

High-level musical constructs: `[Section:]`, `Key:`, `arpeggio()`, `chromatic_run()`.

→ [v2 Semantic Reference](v2-semantic.md)

### Version 3 — Extended

Shorthand syntax: `note+octave`, duration codes (`q`, `h`, `e`), tempo aliases (`@fast`, `@slow`).

→ [v3 Extended Reference](v3-extended.md)

### Version 4 — Polyrhythm & Euclidean

Polyrhythm patterns and Euclidean rhythm generators.

→ [v4 Polyrhythm Reference](v4-polyrhythm.md)

### Shared Subsystems

| Topic | Description |
|-------|-------------|
| Math Expressions | `{$expr}` evaluation, AST pipeline, evaluator chain |
| Variables | `$var` definition, scope stack, interpolation |
| Loops | `repeat N`, `for $i`, `while`, nesting, var increment |
| Directives | `@bpm`, `@key`, `@scale`, `@vol`, `@gc`, tempo aliases |
| Comments | `//`, `/* */`, `{expr}` inside braces |
| Shell Commands | Full eshell command reference |

→ [Math](math-expressions.md) · [Variables](variables.md) · [Loops](loops.md) · [Directives](directives.md) · [Comments](comments.md) · [Shell](shell-commands.md)

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
