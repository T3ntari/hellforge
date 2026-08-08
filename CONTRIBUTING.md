# Contributing to HELLFORGE

Thanks for contributing! HELLFORGE is an open-source DSL for piano music
composition. This file covers how to contribute code, tests, and docs.

## Ground rules

- **v5 is canonical.** v5 = v4 + piano performance features + the v5 statement set
  (print, assert, include, `!fn`, prog, perc, scale/range loops, `@seed` +
  pick/rand). New syntax is added to the v5 path (`ep_compiler/`), never by
  reviving v1–v4. Legacy versions are frozen and deprecated.
- **No stubs.** Every advertised feature must work end-to-end: source →
  compile → events → MIDI → render. If a feature is not implemented, it must
  not be advertised.
- **No private dependencies.** The project is fully offline-capable. No
  phone-home, no private servers, no personal trust keys. If you add a network
  feature, gate it behind an explicit opt-in flag.
- **Tests must pass.** Run the test suite before submitting (see below).
- **Keep it portable.** No hardcoded user paths (`C:\Users\...`), no
  Windows-only behavior without a cross-platform fallback.

## Setup

```bash
python -m venv .venv
.venv/bin/pip install numpy mido scipy pygame pydub psutil
# optional accelerators:
.venv/bin/pip install lupa
```

## Test suite

```bash
.venv/bin/python tests/syntax_test.py    # core syntax + math + limits
.venv/bin/python tests/parse_test.py     # parser, v4, memory
.venv/bin/python tests/lint_test.py      # linter diagnostics
.venv/bin/python tests/gpu_test.py       # plugin/GPU APIs
.venv/bin/python tests/paths_test.py     # path resolution + project generation
.venv/bin/python tests/launch_test.py    # launcher/shell commands
.venv/bin/python tests/run_all.py        # signing, GC, humanize, backend
.venv/bin/python tests/verify_signing.py # signature integrity
```

All files must parse under `python -m ast`.

## Adding a feature

1. Design the syntax and document it in `SYNTAX.md` and the ticket/spec.
2. Implement in the compiler (`ep_compiler/`), reusing `syntax_check.py`
   lexicons so the linter and parser never drift apart.
3. Add ≥2 tests per feature in `tests/`, using the existing `test(name, fn)`
   harness.
4. Verify end-to-end (compile a sample to `.mid` and inspect with `mido`).
5. Run the full suite.

## Signing (optional)

HELLFORGE ships with an optional ED25519 file-signing utility for integrity
verification. It is opt-in: plugins load unsigned, and strict enforcement
(`sys strict 2`) is available for users who want it. Do not make signing
mandatory.

## Code style

- Python 3.10+ compatible, f-strings preferred
- `#` comments only where they add real context
- Match surrounding conventions in the file you edit

## Reporting issues

Open an issue with:

- The E source that triggers the problem
- The command you ran (`ep.py compile`, `eshell.py`, …)
- Expected vs actual output
- Python version and OS

## License

MIT. By contributing you agree your contributions are licensed under the
same terms.
