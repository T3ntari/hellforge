# Testing Conventions

No pytest. Every suite is `tests/<name>_test.py`, self-contained, run
directly with the venv:

```bash
.venv/bin/python tests/v5_statements_test.py   # one suite
.venv/bin/python tests/run_all.py              # everything
```

## Harness (exact)

Every test file defines this at the top (with `passed`/`failed` globals):

```python
def test(name, fn):
    global passed, failed
    try:
        fn(); passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        import traceback; traceback.print_exc()
        print(f"  [FAIL] {name}: {e}")
```

Each test is a plain function asserted with `assert`, registered at module
scope: `test("Name: what it verifies", fn_name)`. A fixture test itself may
raise — the harness catches it and counts a failure.

```python
def test_include_inlines():
    d = tempfile.mkdtemp()
    with open(os.path.join(d, "hook.e"), "w") as f:
        f.write("T0 N60 D500 V80\n")
    ev, _ = compile_source('include "hook.e"\nT100 N64 D500 V80', base_dir=d)
    assert len(ev) == 2, f"expected 2 events, got {len(ev)}"
    assert [e["timestamp"] for e in ev] == [0, 100]
test("Include: inlines file relative to source dir", test_include_inlines)
```

File ends with a summary print and `sys.exit(1)` on failures:

```python
print(f"\n{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
```

## Rules

- Run relevant tests after **every** `.py` change; full suite before
  declaring work done; **never commit unless green**.
- A change that breaks a test is a bug in the change, never in the test.
- New features need **≥2 tests** using the `test(name, fn)` harness.
- Tests import from the repo root (they insert it into `sys.path`), so they
  exercise the real compiler, not mocks.

## Current suites (tests/)

`parse_test.py` (machine/human/version detect), `syntax_test.py` (strict
diagnostics, lexicons), `v5_statements_test.py` (print/assert/include/!fn/
prog/perc/loops/@seed+pick), `piano_features_test.py` (pedal/rest/art/
tuplets/octave/curve/ties), `paths_test.py`, `lint_test.py`,
`cli_commands_test.py`, `async_test.py`, `launch_test.py`, `gpu_test.py`,
`humanize_test.py`, `llm_plugin_test.py` (copilot protocol), `lsp_test.py`,
`verify_signing.py`. `tests/run_all.py` runs every suite, combined report.