# HELLFORGE — E Language

**A domain-specific language for piano music composition.**

Write music as plain text — notes, chords, rhythms, dynamics — and E turns it
into sound. No piano experience needed, no programming experience needed.

```e
@bpm 120
play note(C4) @dur:q @vel:mf
play note(E4) @dur:q @vel:mf
play note(G4) @dur:h @vel:ff
```

That is a complete piece of music — a C major chord. Compile it, play it.

## Highlights

- **Plain text, many outputs** — `.mid`, `.wav`, `.mp3`, `.ec`, `.eic`, `.ee` from one source
- **Precision** — millisecond timing, 0–127 velocity, pitch bend, pan, filters, envelopes
- **v5 syntax** — the canonical version (default always). v5 = v4 + piano performance
  features (sustain pedal, rests, articulations, tuplets, octave shift, velocity
  curves, ties)
- **Low-level controllers** — `@vol`, `@master`, `@gain`, `@sr`, `@bit`, `@quality`,
  `@gc`, `@mem`, `@sub`, `@bass_boost`, `@stereo_width`, `@neural` work end-to-end
  from source through MIDI export to WAV rendering
- **Piano-first features** — sustain pedal, rests, articulations, tuplets, octave
  shifts, velocity curves, ties
- **Musical intelligence** — scale quantization, polyrhythms, Euclidean rhythms,
  tempo curves, ritardando, loop unrolling, math expressions, variables
- **Import** — MIDI and audio (FFT transcription) → E source
- **Plugin ecosystem** — humanize (performance feel), talisman (audio culling),
  eaudio (3D spatial audio), radical (GPU math), lure (LuaJIT acceleration),
  portbaby (syntax conversion), and more
- **Interactive shell** — `eshell.py`: compile, play, lint, generate, convert,
  manage plugins, garbage-collect events, inspect system state

## Install

Requires Python 3.10+.

```bash
python -m venv .venv
.venv/bin/pip install numpy mido scipy pygame pydub psutil
```

Optional accelerators: `lupa` (LURE LuaJIT engine).

## Quick start

```bash
# Compile a composition to MIDI
.venv/bin/python ep.py compile samples/v4-current/basics/hello_world_v4.e -o hello.mid

# Compile everything in a directory (run.py resolves dirs)
.venv/bin/python run.py compile samples/v4-current/basics -o out/

# Lint a file
.venv/bin/python run.py check samples/v4-current/basics/hello_world_v4.e

# Render to WAV (honors @sr/@bit/@quality/... directives)
.venv/bin/python ep.py compile song.e -o song.wav

# Interactive shell
.venv/bin/python eshell.py
```

## Syntax at a glance

Machine mode — absolute timestamps:

```e
T0   N60 D500 V80      // C4 for 500ms at velocity 80
T500 N64 D250 V90      // E4 at 250ms
T750 N67 D250 P[bend:12] S[pan:-0.5]
```

Human mode — readable play statements:

```e
@bpm 90 @key C major @vol:0.7
play note(C4) @dur:q @vel:mf @art:staccato
play chord(C, minor) @dur:h @vel:p
pedal on
play note(E4) @dur:w @vel:f
pedal off
```

The full tutorial and reference live in [`SYNTAX.md`](SYNTAX.md) and the
[`doc/`](doc/index.md) wiki.

## Version policy

v5 is the canonical syntax and the default for all sources. v1, v2, v3 and
v4 sources still compile for backward compatibility but emit deprecation
warnings. Convert old sources with:

```bash
.venv/bin/python run.py compile <old.e> --to v5
```

## Tests

```bash
.venv/bin/python tests/syntax_test.py
.venv/bin/python tests/parse_test.py
.venv/bin/python tests/lint_test.py
.venv/bin/python tests/gpu_test.py
.venv/bin/python tests/paths_test.py
.venv/bin/python tests/run_all.py
```

## License

MIT — see [LICENSE](LICENSE). Contributions welcome; see
[CONTRIBUTING.md](CONTRIBUTING.md).
