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


def _embed():
    from ep_compiler.security_hash import load_version_key
    tag, key = load_version_key()
    SH.x_embed(SH.digest_bundle(SH.compute_manifest()), key or "")


def _fragment_files():
    store = SH.PROJECT_DIR / ".e_identity" / ".integrity" / ".store"
    return [f for d2 in store.iterdir() if d2.is_dir()
            for d3 in d2.iterdir() if d3.is_dir()
            for f in d3.iterdir() if f.is_file()]


def test_x_verify_clean():
    _embed()
    ok, detail = SH.x_verify()
    assert ok, f"X must verify after embed: {detail}"
check("X: clean embed verifies", test_x_verify_clean)


def test_x_rotation_changes_layout():
    _embed()
    before = sorted(str(f) for f in _fragment_files())
    SH.x_verify()  # consumes + re-embeds fresh
    after = sorted(str(f) for f in _fragment_files())
    ok, _ = SH.x_verify()
    assert ok, "rotated X must still verify"
    assert before != after, "rotation must change the hidden layout"
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
    _embed()
check("X: tampered covered file is flagged", test_x_flags_covered_tamper)


def _current_store_dir():
    """The store dir referenced by the CURRENT order file."""
    import ep_compiler.security_hash as S
    of = S._find_order_file()
    assert of is not None, "order file must exist"
    for ln in of.read_text().splitlines():
        if ln.startswith("store="):
            return S.PROJECT_DIR / ln.split("=", 1)[1]
    raise AssertionError("no store= line in order file")


def test_x_flags_fragment_tamper():
    _embed()
    store_dir = _current_store_dir()
    files = [f for f in store_dir.iterdir() if f.is_file()]
    assert files, "fragment files must exist"
    tgt = files[0]
    txt = tgt.read_text()
    m = re.search(r"[0-9a-f.]+", txt)
    assert m, "fragment file should contain a hex chunk"
    tgt.write_text(txt[:m.start()] + "deadbeef" + txt[m.end():])
    ok, _ = SH.x_verify()
    assert not ok, "X must flag altered fragments"
    _embed()
    ok, _ = SH.x_verify()
    assert ok, "re-embedded X must verify"
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


def test_identity_tamper_flags():
    import ep_compiler.security_hash as SHm
    sk = SHm.PROJECT_DIR / ".e_identity" / "secret.key"
    if not sk.is_file():
        check("X: identity tamper flags (no identity present — skipped)", lambda: None)
        return
    SHm.reembed()
    ok, _ = SHm.x_verify()
    assert ok, "precondition: verify passes"
    orig = sk.read_bytes()
    try:
        sk.write_bytes(b"tampered-key-bytes")
        ok, detail = SHm.x_verify()
        assert not ok, "identity tamper must be flagged"
        assert "identity files altered" in detail, detail
    finally:
        sk.write_bytes(orig)
    SHm.reembed()
    ok, _ = SHm.x_verify()
    assert ok, "restored identity must verify again"
check("X: secret.key tamper flags the system, reembed restores", test_identity_tamper_flags)


print(f"\nSECURITY HASH TESTS: {passed}/{passed + failed} passed")
sys.exit(0 if failed == 0 else 1)
