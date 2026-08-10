# Comments — `//`, `/* */`

[Back to doc/index.md](../index.md) · [Syntax Overview](overview.md)

Two commenting mechanisms.

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

### Nested Block Comments

```
/* outer /* inner */ still works */
```

Block comments are nested safely — the parser tracks depth.

### Comment Caveats

- `//` inside a string literal is treated as content, not a comment.
- `/*` and `*/` inside `{$...}` are parsed as operators (`*` and `/`),
  not comment delimiters.
- `@directives` inside comments never take effect (the comment stripper
  runs first — e.g. a doc comment mentioning `@humanize` does not enable
  it).

---

**HELLFORGE OS v0.1.14.41-beta** — v5 comments
