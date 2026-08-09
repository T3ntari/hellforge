"""hellgate.tests.test_summarizer — self-contained tests.

Run with:
    python3 .venv/bin/python plugins/hellgate/tests/test_summarizer.py
Must pass without network (live ollama calls are mocked/skipped).
"""

import os
import shutil
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(_HERE))))

from plugins.hellgate import summarizer as S  # noqa: E402

passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
    except Exception as e:
        failed += 1
        print("FAIL: %s -> %r" % (name, e))


def test_tokens_plausible():
    n = S.tokens("x" * 1000)
    assert 200 <= n <= 300, "expected ~250 for 1000 chars, got %d" % n
    assert S.tokens("") >= 1
    assert S.tokens(None) >= 1
    assert S.tokens("abcd") == S.tokens("abcd")  # deterministic


def test_context_fraction_bounds():
    hist = [{"role": "user", "content": "x" * 10000}]
    frac = S.context_fraction(hist)
    assert 0.0 < frac < 1.0, "frac=%r" % frac
    assert S.context_fraction([]) == 0.0
    assert S.context_fraction(None) == 0.0
    assert S.context_fraction([{"role": "user"}]) == 0.0
    assert S.context_fraction(hist, budget=0) == 0.0
    assert S.context_fraction(hist, budget=-5) == 0.0


def test_needs_digest_thresholds():
    assert S.needs_digest([]) is False
    assert S.needs_digest([{"role": "user", "content": "hi"}]) is False
    # ~100k chars = ~25k tokens = ~19.5% of a 128k-token context:
    assert S.needs_digest([{"role": "user", "content": "x" * 100000}]) is False
    # near-full context (~100k tokens ~= 400k chars) must trigger:
    big = [{"role": "user", "content": "x" * 400000}]
    assert S.needs_digest(big) is True
    frac = S.context_fraction(big)
    assert frac >= 0.75, "frac=%r" % frac
    # threshold override:
    assert S.needs_digest(big, threshold=0.5) is True
    assert S.needs_digest(big, threshold=0.99) is False


def test_make_digest_falls_back_gracefully():
    orig_post = S._http_post_json

    def boom(*a, **k):
        raise RuntimeError("ollama unreachable")

    S._http_post_json = boom
    try:
        d = S.make_digest(max_tokens=50)
        assert isinstance(d, str) and d.strip(), "digest empty"
    finally:
        S._http_post_json = orig_post


def test_make_digest_uses_provided_api():
    calls = []

    class FakeAPI:
        def chat_request(self, provider, base_url, api_key, model, messages,
                         timeout=300):
            calls.append((provider, base_url, model, timeout))
            return "**HELLFORGE**: `@bpm 120` sets tempo.", None

    d = S.make_digest(api=FakeAPI(), max_tokens=50)
    assert "HELLFORGE" in d
    assert calls and calls[0][0] == "ollama"
    assert calls[0][3] == S.TIMEOUT_SEC


def test_build_digest_file_no_clobber():
    orig_make = S.make_digest
    S.make_digest = lambda: "**digest**\n"
    tmp_dir = os.path.join(_HERE, "tmp_build_digest")
    os.makedirs(tmp_dir, exist_ok=True)
    try:
        target = os.path.join(tmp_dir, "core-llm.md")
        path = S.build_digest_file(target)
        assert path == target and os.path.isfile(target), "path=%r" % path
        with open(target, encoding="utf-8") as fh:
            assert "digest" in fh.read()
        assert not os.path.isfile(os.path.join(tmp_dir, "core.md"))
    finally:
        S.make_digest = orig_make
        shutil.rmtree(tmp_dir, ignore_errors=True)


test("tokens() estimates plausibly (~4 chars/token)", test_tokens_plausible)
test("context_fraction() bounds and guards", test_context_fraction_bounds)
test("needs_digest() thresholds", test_needs_digest_thresholds)
test("make_digest() falls back when ollama unreachable", test_make_digest_falls_back_gracefully)
test("make_digest() uses provided api", test_make_digest_uses_provided_api)
test("build_digest_file() writes via temp+rename", test_build_digest_file_no_clobber)

print("passed %d, failed %d" % (passed, failed))
if failed:
    print("HELLGATE SUMMARIZER TESTS FAILED")
    sys.exit(1)
print("ALL HELLGATE SUMMARIZER TESTS PASSED")
sys.exit(0)
