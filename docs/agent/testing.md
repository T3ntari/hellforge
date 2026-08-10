# Testing Conventions

No pytest. Every suite is `tests/<name>_test.py`, self-contained, run
directly with the venv:

```bash
.venv/bin/python tests/v5_statements_test.py   # one suite
.venv/bin/python tests/security_hash_test.py   # X/Y integrity suite
.venv/bin/python plugins/krip/tests/test_krip.py  # hypervisor suite
.venv/bin/python tests/run_all.py              # everything (combined run)
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

- `parse_test.py` (machine/human/version detect), `syntax_test.py` (strict
  diagnostics, lexicons), `lint_test.py`, `paths_test.py`
- `v5_statements_test.py` — **the authoritative v5 statement set**: print,
  assert, include, `!fn` macros, prog, perc, list/range/scale/run loops +
  break/continue, repeat, `@seed` + pick/rand, plus backward-compat checks
  (29 tests)
- `piano_features_test.py` (pedal/rest/art/tuplets/octave/curve/ties)
- `cli_commands_test.py`, `async_test.py`, `launch_test.py`, `gpu_test.py`,
  `humanize_test.py`, `llm_plugin_test.py` (copilot protocol),
  `lsp_test.py`, `verify_signing.py`
- `security_hash_test.py` — X/Y integrity: clean embed verifies, rotation
  re-randomizes, tampered covered file and tampered fragments are flagged,
  Y is a deterministic 128-hex per-version key, committed manifest matches
  the clean tree
- `plugins/krip/tests/test_krip.py` — hypervisor: gpu env, mem rlimits,
  engine/vulkanrt/tensor validation, sandbox run/list/kill lifecycle, os
  view, krip.json load/save/reload, boot registry + rollback, boot menu
  selection, safe update notice/choice, hypervisor entry (run/console/
  status/escape)
- `tests/run_all.py` — the combined mega-run (signing, strict enforcement,
  Talisman culling/occlusion, math pipeline, pkglist hash verification)

## What "green" means

A suite is green when its final line reports all tests passed and the exit
code is 0 (e.g. `V5 STATEMENT TESTS: 29/29 passed` +
`ALL V5 STATEMENT TESTS PASSED`). Before declaring work done, run
`tests/run_all.py` and the security/krip suites — all must be green.
