# HELLFORGE — Syntax Overview

[Back to doc/index.md](../index.md)

---

## Version 5 — canonical

**v5 is the canonical syntax and the default for all sources.** It is a
superset of v4 plus the piano performance layer (sustain pedal, rests,
articulations, tuplets, octave shift, velocity curves, ties) and the v5
statement set (`print`, `assert`, `include`, `!fn` macros, `prog`,
`perc`, scale/range loops with `break`/`continue`, `@seed` with
`pick`/`rand`).

```e
@bpm 96 @seed 42
play note(C4) @dur:q @vel:mf
for $n in scale(C major, 4, 1) {
    print $n
    play note($n) @dur:q @vel:mp
}
prog(C:q G:q Am:h F:q)
perc(kick)
```

The full reference lives in [`SYNTAX.md`](../../SYNTAX.md). A complete
example piece ships at `songs/aurora_nocturne.e`.

**Valid v5 (no demotion — these were once v3/v4-only):**

| Construct | Example |
|-----------|---------|
| Polyrhythm | `[C4 E4 G4](3:2)` — three notes over two beats |
| Euclidean | `E(5,4)` — five pulses over four steps (Bjorklund) |
| v3 shorthand | `C4 q` — note + octave with a duration code |

**Legacy bans — NOT valid v5** (the v5-aware linter flags them):

- Machine lines: `T0 N60 D500 V80`
- Note ranges: `N60-72`
- Poly shorthand: `CH0 ...`
- `ritard`, roman-numeral chords
- `while` loops, `for $i = 0 to N step S`
- `?0.8` probability suffix, v4 `@curve bpm from`

Lint with `run.py check <file>` — a pure v5 file reports **at most I001**.

### Legacy versions (reference only)

v1, v2, v3 and v4 sources still compile for backward compatibility with
**deprecation warnings** (explicit markers). They are documented for
reference:

| Version | What it is | Page |
|---------|-----------|------|
| v1 | Machine (`#MACHINE` T N D V tokens) + Human (`#HUMAN` play note/chord) | [v1 Machine](v1-machine.md) · [v1 Human](v1-human.md) |
| v2 | Semantic: sections, `Key:`, arpeggio/chromatic/walking-bass generators | [v2 Semantic](v2-semantic.md) |
| v3 | Shorthand: `C4q`, tempo aliases, rest codes — **valid in v5** | [v3 Extended](v3-extended.md) |
| v4 | Polyrhythm + Euclidean generators — **valid in v5** | [v4 Polyrhythm](v4-polyrhythm.md) |

Convert old sources with `run.py compile <old.e> --to v5` (portbaby).

### Shared subsystems

| Topic | Description |
|-------|-------------|
| Math Expressions | `{$expr}` evaluation, AST pipeline, evaluator chain (TensorSHARP → Radical → LURE → Python) |
| Variables | `$var` definition, scope stack, interpolation |
| Loops | v5 `for`/range loops with `break`/`continue`; legacy `repeat`/`for $i`; `while` banned in v5 |
| Directives | `@bpm`, `@key`, `@vol`, `@humanize`, `@pedal`, `@seed`, … |
| Comments | `//`, `/* */`, nested blocks |
| Shell Commands | The eshell console reference |

→ [Math](math-expressions.md) · [Variables](variables.md) · [Loops](loops.md) · [Directives](directives.md) · [Comments](comments.md) · [Shell](shell-commands.md)

---

**HELLFORGE OS v0.1.14.41-beta** — v5 canonical · v1–v4 legacy
