# **HELLFORGE v1.0.0.0 ALPHA**

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

---

## Comments — `//`, `/* */`, `{expr}`

Three commenting mechanisms with different semantics.

### Single-Line `//`

```
// This is a comment
C4q  E4q  G4q  // inline comment after code
```

Everything from `//` to end of line is ignored by the parser.

### Block Comments `/* */`

```
/*
  Multi-line comment block.
  Useful for disabling sections during testing.
*/
C4q  E4q  G4q
```

Block comments can span multiple lines and are stripped before parsing.

### Expression Inside Braces `{expr}`

```
{ 2 + 2 }                // comment-style, but NOT a comment
C4q  E4q  {$bpm / 2}q    // evaluated expression
```

A bare `{expr}` without `$` prefix is evaluated as a math expression. If the expression is constant, it behaves like a comment with no side effects. If it references variables, it produces a value.

### Nested Block Comments

```
/* outer /* inner */ still works */
```

Block comments are nested safely — the parser tracks depth.

### Comment Caveats

- `//` inside a string literal is treated as content, not a comment.
- `/*` and `*/` inside `{$...}` are parsed as operators (`*` and `/`), not comment delimiters.

---

**HELLFORGE v1.0.0.0 ALPHA** — Piano DSL Syntax Documentation
