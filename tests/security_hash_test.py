#!/usr/bin/env python3
"""HELLFORGE X/Y integrity tests — run with:
    python3 tests/security_hash_test.py
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from ep_compiler import security_hash as SH

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


def test_x_verify_clean():
    SH.x_embed(SH.digest_bundle(SH.compute_manifest()))
    ok, detail = SH.x_verify()
    assert ok, f"X must verify after embed: {detail}"
check("X: clean embed verifies", test_x_verify_clean)


def test_x_rotation_changes_layout():
    p1 = open(SH.X_FILE).read()
    SH.x_embed(SH.digest_bundle(SH.compute_manifest()))
    p2 = open(SH.X_FILE).read()
    ok, _ = SH.x_verify()
    assert ok, "rotated X must still verify"
    assert p1 != p2, "rotation must change the hidden layout"
check("X: rotation re-randomizes layout, still verifies", test_x_rotation_changes_layout)


def test_x_flags_covered_tamper():
    orig = open(os.path.join(ROOT, "eshell.py")).read()
    try:
        with open(os.path.join(ROOT, "eshell.py"), "a") as f:
            f.write("\n# tamper-marker-x\n")
        ok, detail = SH.x_verify()
        assert not ok, "X must flag a tampered covered file"
        assert "does not match" in detail
    finally:
        with open(os.path.join(ROOT, "eshell.py"), "w") as f:
            f.write(orig)
    SH.x_embed(SH.digest_bundle(SH.compute_manifest()))
check("X: tampered covered file is flagged", test_x_flags_covered_tamper)


def test_x_flags_fragment_tamper():
    SH.x_embed(SH.digest_bundle(SH.compute_manifest()))
    txt = open(SH.X_FILE).read()
    m = re.search(r'(_x\d+ = ")([0-9a-f]+)(")', txt)
    assert m, "X file should contain fragments"
    open(SH.X_FILE, "w").write(txt[:m.start(2)] + "deadbeef" + txt[m.end(2):])
    ok, _ = SH.x_verify()
    assert not ok, "X must flag altered fragments"
    SH.x_embed(SH.digest_bundle(SH.compute_manifest()))
check("X: altered fragments are flagged", test_x_flags_fragment_tamper)


def test_y_key_structure():
    bundle = SH.digest_bundle(SH.compute_manifest())
    y = SH.y_key(bundle, "v0.1.14.26-beta")
    assert len(y) == 128, f"Y must be 128 hex chars, got {len(y)}"
    assert all(c in "0123456789abcdef" for c in y)
    assert SH.y_key(bundle, "v0.1.14.26-beta") == y, "Y must be deterministic"
check("Y: 128-hex per-version key, deterministic", test_y_key_structure)


def test_y_version_key_committed():
    tag, y = SH.load_version_key()
    assert tag and y, "ep_compiler/_version_key.py must exist (generated)"
    assert len(y) == 128
check("Y: committed version key present", test_y_version_key_committed)


def test_committed_manifest_matches():
    r = SH.verify()
    assert r["ok"], f"clean tree must verify: {r['detail']}"
check("manifest: clean tree verifies", test_committed_manifest_matches)


def test_digest_size():
    b = SH.digest_bundle(SH.compute_manifest())
    assert 128 <= len(b) <= 512, f"digest size out of range: {len(b)}"
    assert b.count(".") == 2
check("digest: 128-512 hex chars, triple", test_digest_size)


print(f"\nSECURITY HASH TESTS: {passed}/{passed + failed} passed")
sys.exit(0 if failed == 0 else 1)
