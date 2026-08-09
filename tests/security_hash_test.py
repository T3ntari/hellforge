#!/usr/bin/env python3
"""HELLFORGE security digest tests — run with:
    python3 tests/security_hash_test.py
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ep_compiler import security_hash as S

passed = failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except AssertionError as e:
        failed += 1
        print(f"  [FAIL] {name}: {e}")


def test_clean_verify():
    r = S.verify()
    assert r["ok"], f"clean tree must verify: {r['detail']}"
check("clean tree verifies", test_clean_verify)


def test_digest_size():
    r = S.verify()
    b = r["bundle"]
    assert b.count(".") == 2, "triple digest must have 3 parts"
    assert len(b) >= 128, f"digest too small: {len(b)}"
    assert len(b) <= 512, f"digest too large: {len(b)}"
    parts = b.split(".")
    assert len(parts[0]) == 64 and len(parts[1]) == 128 and len(parts[2]) == 128
check("digest is 160 bytes (256+512+512)", test_digest_size)


def test_tamper_flags_file():
    orig = open(os.path.join(ROOT, "eshell.py")).read()
    try:
        with open(os.path.join(ROOT, "eshell.py"), "a") as f:
            f.write("\n# tamper-marker-x\n")
        r = S.verify()
        assert not r["ok"], "tampered tree must be flagged"
        assert "eshell.py" in r["changed"], f"changed list: {r['changed']}"
    finally:
        with open(os.path.join(ROOT, "eshell.py"), "w") as f:
            f.write(orig)
    r = S.verify()
    assert r["ok"], f"restored tree must verify: {r['detail']}"
check("tamper detection flags the exact file", test_tamper_flags_file)


def test_extra_plugin_dir_flags():
    extra = os.path.join(ROOT, "plugins", "unlisted_probe")
    os.makedirs(extra, exist_ok=True)
    try:
        # plugin dir with __init__.py -> enters the local manifest -> aggregate
        # mismatch (the committed manifest does not know it)
        with open(os.path.join(extra, "__init__.py"), "w") as f:
            f.write("probe = 1\n")
        r = S.verify()
        assert not r["ok"], "unlisted plugin dir must be flagged"
        assert "unlisted_probe" in r["changed"] or "unlisted_probe" in r["extra_dirs"], \
            f"changed: {r['changed']}, extra_dirs: {r['extra_dirs']}"
        os.remove(os.path.join(extra, "__init__.py"))
        # plugin dir without __init__.py -> uncovered -> extra_dirs
        r = S.verify()
        assert not r["ok"], "dir without __init__ must be flagged"
        assert "unlisted_probe" in r["extra_dirs"], f"extra_dirs: {r['extra_dirs']}"
    finally:
        try:
            os.remove(os.path.join(extra, "__init__.py"))
        except OSError:
            pass
        try:
            os.rmdir(extra)
        except OSError:
            pass
    r = S.verify()
    assert r["ok"], f"after cleanup must verify: {r['detail']}"
check("unlisted plugin dir (fentclient-style) flags the system", test_extra_plugin_dir_flags)


def test_committed_manifest_exists():
    m, bundle = S.load_committed()
    assert m and bundle, "SECURITY_HASH.txt missing or malformed"
    assert len(m) >= 20, f"manifest too small: {len(m)} entries"
check("committed manifest present", test_committed_manifest_exists)


def test_aggregate_stability():
    m1 = S.compute_manifest()
    m2 = S.compute_manifest()
    assert S.digest_bundle(m1) == S.digest_bundle(m2)
check("aggregate is deterministic", test_aggregate_stability)


print(f"\nSECURITY HASH TESTS: {passed}/{passed + failed} passed")
sys.exit(0 if failed == 0 else 1)
