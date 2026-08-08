#!/usr/bin/env python3
"""LSP bridge regression tests — unreachable code, comment-aware context,
shared line splitting, module-level docs constant, PEP 8 imports."""
import sys
import os
import re
import inspect
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools"))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lsp_bridge as lb

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        import traceback
        traceback.print_exc()
        print(f"  [FAIL] {name}: {e}")


# === 1. Fatal bug regression: linting must run even when compile succeeds ===

def test_lint_runs_when_compile_ok():
    # Valid compile BUT contains an unrecognized line → linter must flag it
    text = "@bpm 120\nT0 N60 D500 V80\ngarbage line here\nT100 N64 D500 V80"
    diags = lb.get_diagnostics(text)
    assert any("garbage line here" in d["message"] for d in diags), \
        f"lint did not run on successful compile: {diags}"
test("Fatal bug: lint runs even when compile succeeds", test_lint_runs_when_compile_ok)


def test_no_false_positives_on_valid_file():
    text = "@bpm 120\n@key C_Major\nT0 N60 D500 V80\nT500 N64 D500 V80"
    diags = lb.get_diagnostics(text)
    assert not any(d["severity"] in (0, 1) for d in diags), f"valid file flagged: {diags}"
test("Diagnostics: valid file produces no errors", test_no_false_positives_on_valid_file)


def test_compile_error_reported():
    # The real compiler is resilient (never raises on malformed input), so
    # simulate a compile failure to prove the exception→diagnostic path works.
    orig = lb.compile_source
    lb.compile_source = lambda text: (_ for _ in ()).throw(RuntimeError("boom at line 2"))
    try:
        diags = lb.get_diagnostics("@bpm 120\nT0 N60 D500 V80")
    finally:
        lb.compile_source = orig
    assert len(diags) >= 1, "compile error not reported"
    assert any("boom" in d["message"] for d in diags)
test("Diagnostics: compile errors reported", test_compile_error_reported)


# === 2. Comment-aware context (fragile "play chord" check) ===

def test_no_completion_inside_comment():
    # A comment mentioning play chord must NOT trigger chord-quality completions
    items = lb.get_completions("// I need play chord variations here, q", 0, 45)
    labels = [c["label"] for c in items]
    assert not any(q in labels for q in ["major", "minor", "dom7"]), \
        f"comment triggered chord completions: {labels}"
test("Context: comments never trigger chord completions", test_no_completion_inside_comment)


def test_completion_in_real_play_chord():
    items = lb.get_completions("play chord(C, mi", 0, 15)
    labels = [c["label"] for c in items]
    assert "minor" in labels, f"real play chord missed: {labels}"
test("Context: real play chord still suggests qualities", test_completion_in_real_play_chord)


def test_math_func_in_expr_not_in_comment():
    items = lb.get_completions("// sin is great, s", 0, 18)
    assert not any(c["label"].startswith("sin(") for c in items), \
        "math completion triggered inside comment"
test("Context: no math completions inside comments", test_math_func_in_expr_not_in_comment)


# === 3. Shared line splitting (performance) ===

def test_get_symbols_accepts_presplit_lines():
    text = "$note = 60\n#MACHINE\nT0 N{$note} D500 V80"
    lines = lb._split_lines(text)
    syms = lb.get_symbols(text, lines)
    assert any(s["name"] == "$note" for s in syms)
test("Performance: get_symbols accepts pre-split lines", test_get_symbols_accepts_presplit_lines)


def test_token_at_accepts_presplit_lines():
    lines = lb._split_lines("T0 N60 D500 V80")
    tok = lb._token_at(lines, 0, 4)
    assert tok and tok["token"] == "N60"
test("Performance: _token_at accepts pre-split lines", test_token_at_accepts_presplit_lines)


def test_no_internal_resplit_in_completions():
    """get_completions must not call text.split('\n') internally more than once."""
    src = inspect.getsource(lb.get_completions)
    assert "text.split(\"\\n\")" not in src, "get_completions re-splits text!"
    # It uses _split_lines once + passes lines to get_symbols
    assert "lines" in src and "get_symbols(text, lines)" in src
test("Performance: get_completions splits once, reuses lines", test_no_internal_resplit_in_completions)


# === 4. Module-level DOCS constant ===

def test_docs_is_module_constant():
    assert hasattr(lb, "DOCS"), "DOCS must be module-level"
    assert isinstance(lb.DOCS, dict) and len(lb.DOCS) > 30
    # get_hover must NOT contain a local docs dict literal
    src = inspect.getsource(lb.get_hover)
    assert "DOCS" in src and "docs = {" not in src, "get_hover rebuilds docs dict!"
test("Performance: hover docs are module-level constant", test_docs_is_module_constant)


# === 5. Hover still works ===

def test_hover_machine_token():
    r = lb.get_hover("T0 N60 D500 V80", 0, 4)
    assert r and "C4" in r["text"], f"hover N60 failed: {r}"
test("Hover: N60 → note name", test_hover_machine_token)


def test_hover_keyword():
    r = lb.get_hover("play chord(C, major)", 0, 1)
    assert r and "Human-mode command" in r["text"], f"hover play failed: {r}"
test("Hover: play keyword", test_hover_keyword)


# === 6. Misc: completions, definition, format still work ===

def test_completions_directives():
    items = lb.get_completions("@b", 0, 2)
    labels = [c["label"] for c in items]
    assert "@bpm" in labels
test("Completions: @b → @bpm", test_completions_directives)


def test_definition_var():
    text = "$note = 60\nT0 N{$note} D500 V80"
    r = lb.get_definition(text, 1, 8)
    assert r and r["line"] == 0, f"definition failed: {r}"
test("Definition: $note usage → definition", test_definition_var)


def test_format():
    assert lb.get_format("T0   N60  D500    V80") == "T0 N60 D500 V80"
test("Format: machine line normalized", test_format)


def test_pep8_imports():
    src = inspect.getsource(lb)
    header = src.split("def ", 1)[0]
    for mod in ("sys", "os", "json", "re"):
        assert f"import {mod}\n" in header, f"import {mod} not on its own line"
test("PEP 8: imports on individual lines", test_pep8_imports)


# === 7. Named SymbolKind / CompletionItemKind constants (no magic numbers) ===

def test_symbol_kind_constants_defined():
    for name in ("SYMBOL_VARIABLE", "SYMBOL_METHOD", "SYMBOL_MODULE", "SYMBOL_FILE",
                 "ITEM_KEYWORD", "ITEM_FUNCTION", "ITEM_CONSTANT", "ITEM_VARIABLE"):
        assert hasattr(lb, name), f"missing constant {name}"
    assert lb.SYMBOL_VARIABLE == 13
    assert lb.SYMBOL_METHOD == 6
    assert lb.SYMBOL_MODULE == 2
test("Constants: SymbolKind/ItemKind named at module level", test_symbol_kind_constants_defined)


def test_no_raw_kind_numbers_in_symbols():
    src = inspect.getsource(lb.get_symbols)
    assert "\"kind\": 13" not in src and "\"kind\": 6" not in src and "\"kind\": 2" not in src, \
        "raw kind numbers still in get_symbols"
    assert "SYMBOL_VARIABLE" in src and "SYMBOL_METHOD" in src and "SYMBOL_MODULE" in src
test("Constants: get_symbols uses named kinds only", test_no_raw_kind_numbers_in_symbols)


def test_no_raw_kind_numbers_in_completions():
    src = inspect.getsource(lb.get_completions)
    assert '"kind": ' not in src or '"kind": ' in src and not re.search(r'"kind": \d', src), \
        "raw kind numbers still in get_completions"
    assert "ITEM_" in src
test("Constants: get_completions uses named kinds only", test_no_raw_kind_numbers_in_completions)


def test_symbol_kinds_correct_values():
    text = "$note = 60\n#MACHINE\n[Section: Intro]\ninherit \"parts/a.e\""
    syms = lb.get_symbols(text)
    by_name = {s["name"]: s["kind"] for s in syms}
    assert by_name.get("$note") == lb.SYMBOL_VARIABLE
    assert by_name.get("MACHINE") == lb.SYMBOL_METHOD
    assert by_name.get("[Section:") == lb.SYMBOL_MODULE
    assert any(v == lb.SYMBOL_MODULE and "inherit" in k for k, v in by_name.items())
test("Constants: symbol kinds map to correct categories", test_symbol_kinds_correct_values)


# === 8. Imports / splitting hygiene ===

def test_all_public_functions_use_split_lines():
    for fn_name in ("get_symbols", "get_completions", "get_hover", "get_diagnostics",
                    "get_definition", "get_format"):
        src = inspect.getsource(getattr(lb, fn_name))
        assert "text.split(\"\\n\")" not in src, f"{fn_name} re-splits text!"
        assert "_split_lines(" in src or "lines" in src, f"{fn_name} ignores shared lines helper"
test("Hygiene: no inline text.split in any public function", test_all_public_functions_use_split_lines)


# === 9. Column positions forwarded to VS Code ===

def test_diagnostics_have_columns():
    diags = lb.get_diagnostics("@bpm 500\nT0 N200 D500 V80.5\nplay chord(C, bogus)\n")
    by_code = {}
    for d in diags:
        by_code[d["message"].split("]")[0].strip("[")] = d
    e053 = by_code.get("E053")
    assert e053 and e053["char"] == 3, f"E053 should point at N200 col 4: {e053}"
    w019 = by_code.get("W019")
    assert w019 and w019["char"] == 13, f"W019 should point at V80.5: {w019}"
    e059 = by_code.get("E059")
    assert e059 and e059["char"] == 14, f"E059 should point at quality: {e059}"
    assert all(d.get("length", 0) >= 1 for d in diags)
test("Columns: diagnostics carry precise char+length", test_diagnostics_have_columns)


print(f"\n{'='*50}")
print(f"LSP BRIDGE TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LSP BRIDGE TESTS PASSED")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
