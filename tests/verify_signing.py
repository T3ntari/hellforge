#!/usr/bin/env python3
"""HELLFORGE — verify local signing/identity works end-to-end (offline).

Tests the local-only signing model: identity creation, ED25519 sign/verify
round-trips, tamper detection, strict-signing levels, and pkglist integrity
hashes. All paths derive from PROJECT_DIR via __file__ — no hardcoded paths."""
import sys
import os
import json
import tempfile

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from ep_core import (
    verify_signature,
    sign_file,
    identity_exists,
    create_identity,
    load_identity,
    get_public_key,
    get_strict_signing,
    set_strict_signing,
    _STRICT_SIGNING,
    TRUST_REGAS,
    TRUST_TENTARI,
    TRUST_UNKNOWN,
    TRUST_UNSIGNED,
)
from plugins.fentclient.security import (
    compute_plugin_hash,
    load_pkglist_verifications,
)

passed = 0
failed = 0
TMP = tempfile.mkdtemp(prefix="e_signing_test_")


def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        print(f"  [FAIL] {name}: {e}")


# ── Setup: local identity (created by this test if missing) ──
if not identity_exists():
    create_identity("VerifyTester", {})
id = load_identity()
ID_NAME = id.get("name", "local")
ID_PUB = id.get("public_key", "")


def make_file(name, content="test content", mode="w"):
    p = os.path.join(TMP, name)
    with open(p, mode) as f:
        f.write(content)
    return p


# 1. Identity files created
def test_identity_files():
    id_dir = os.path.join(PROJECT_DIR, ".e_identity")
    assert os.path.exists(os.path.join(id_dir, "identity.json")), "identity.json missing"
    assert os.path.exists(os.path.join(id_dir, "secret.key")), "secret.key missing"
check("identity: identity.json + secret.key exist", test_identity_files)

# 2. Identity metadata
def test_identity_meta():
    id_path = os.path.join(PROJECT_DIR, ".e_identity", "identity.json")
    with open(id_path) as f:
        data = json.load(f)
    assert data.get("name"), "no name"
    assert data.get("public_key"), "no public key"
    assert data.get("algorithm") == "ED25519"
check("identity: name/public_key/ED25519 fields", test_identity_meta)

# 3. Public key format
def test_pubkey_format():
    assert ID_PUB and len(ID_PUB) == 64, f"bad public key len {len(ID_PUB)}"
    int(ID_PUB, 16)
check("identity: public key is 64 hex chars", test_pubkey_format)

# 4. load_identity round-trip
def test_load_identity():
    assert load_identity().get("public_key") == ID_PUB
check("identity: load_identity matches", test_load_identity)

# 5. identity_exists
def test_identity_exists():
    assert identity_exists() is True
check("identity: identity_exists() True", test_identity_exists)

# 6. get_public_key() resolves local identity
def test_get_pub_local():
    assert get_public_key() == ID_PUB
    assert get_public_key("local") == ID_PUB
check("identity: get_public_key() == local identity", test_get_pub_local)

# 7. No hardcoded personal trust keys
def test_no_hardcoded_keys():
    assert get_public_key("REGAS") is None, "REGAS key still hardcoded"
    assert get_public_key("Tentari") is None, "Tentari key still hardcoded"
    assert get_public_key("regas") is None, "REGAS key still hardcoded"
check("identity: REGAS/Tentari hardcoded keys removed", test_no_hardcoded_keys)

# 8. Sidecar sign creates .sig
def test_sign_sidecar():
    p = make_file("plugin_side.py", '"""Plugin."""\nVERSION = "1.0.0"\n')
    r = sign_file(p, embed=False)
    assert r is not None
    assert r.get("algorithm") == "ED25519"
    assert r.get("signature"), "no signature in meta"
    assert os.path.exists(p + ".sig"), ".sig not created"
check("sign: sidecar .sig created (ED25519)", test_sign_sidecar)

# 9. .sig metadata author
def test_sig_meta():
    p = os.path.join(TMP, "plugin_side.py")
    with open(p + ".sig") as f:
        meta = json.load(f)
    assert meta.get("author") == ID_NAME, f"author {meta.get('author')} != {ID_NAME}"
    assert meta.get("algorithm") == "ED25519"
    assert meta.get("timestamp", 0) > 0
check("sign: .sig metadata (author/algorithm/timestamp)", test_sig_meta)

# 10. Verify signed file
def test_verify_signed():
    p = os.path.join(TMP, "plugin_side.py")
    v, level, author, detail = verify_signature(p)
    assert v, f"should verify: {detail}"
check("verify: signed file verifies", test_verify_signed)

# 11. Valid local signer trust level
def test_verify_level():
    p = os.path.join(TMP, "plugin_side.py")
    v, level, author, detail = verify_signature(p)
    assert level == TRUST_UNKNOWN, f"expected TRUST_UNKNOWN, got {level}"
    assert author == ID_NAME
check("verify: local signer -> TRUST_UNKNOWN + author", test_verify_level)

# 12. Embedded sign round-trip
def test_embed_roundtrip():
    p = make_file("embed.e", "T0 N60 D500")
    r = sign_file(p, embed=True)
    assert r is not None
    v, level, author, detail = verify_signature(p)
    assert v, f"embedded verify failed: {detail}"
check("sign: embedded round-trip verifies", test_embed_roundtrip)

# 13. Embedded header is JSON
def test_embed_header():
    p = os.path.join(TMP, "embed.e")
    with open(p, "rb") as f:
        first = f.readline()
    meta = json.loads(first.decode())
    assert meta.get("_e_sig", {}).get("algorithm") == "ED25519"
check("sign: embedded header parses as _e_sig JSON", test_embed_header)

# 14. Tamper detection (sidecar)
def test_tamper_sidecar():
    p = make_file("tamper.e", "original")
    sign_file(p)
    with open(p, "a") as f:
        f.write("\ntampered")
    v, level, author, detail = verify_signature(p)
    assert not v, "tampered file must fail"
    assert "mismatch" in detail.lower()
check("verify: tampered file rejected (sidecar)", test_tamper_sidecar)

# 15. Tamper detection (embedded)
def test_tamper_embed():
    p = make_file("tamper_embed.e", "original")
    sign_file(p, embed=True)
    with open(p, "a") as f:
        f.write("\ntampered")
    v, level, author, detail = verify_signature(p)
    assert not v, "tampered embedded file must fail"
check("verify: tampered file rejected (embedded)", test_tamper_embed)

# 16. Unsigned file detection
def test_unsigned():
    p = make_file("unsigned.e", "@bpm 120")
    v, level, author, detail = verify_signature(p)
    assert not v
    assert level == TRUST_UNSIGNED
    assert author == "unsigned"
check("verify: unsigned file -> TRUST_UNSIGNED", test_unsigned)

# 17. Multi-type sign+verify
def test_multi_types():
    types = {".e": "T0 N60 D500", ".py": "print('x')", ".txt": "plain text"}
    for ext, content in types.items():
        p = make_file(f"multi{ext}", content)
        assert sign_file(p) is not None, f"failed to sign {ext}"
        v, l, a, d = verify_signature(p)
        assert v, f"{ext} verify failed: {d}"
check("sign: multi-type (.e/.py/.txt) round-trips", test_multi_types)

# 18. Strict signing default
def test_strict_default():
    assert _STRICT_SIGNING == 0, f"default strict = {_STRICT_SIGNING}"
check("strict: default level is 0 (load anything)", test_strict_default)

# 19. Strict level 0
def test_strict_0():
    set_strict_signing(0)
    assert get_strict_signing() == 0
check("strict: set/get 0", test_strict_0)

# 20. Strict level 1
def test_strict_1():
    set_strict_signing(1)
    assert get_strict_signing() == 1
check("strict: set/get 1", test_strict_1)

# 21. Strict level 2 + reset
def test_strict_2():
    set_strict_signing(2)
    assert get_strict_signing() == 2
    set_strict_signing(0)
    assert get_strict_signing() == 0
check("strict: set/get 2 (reset to 0)", test_strict_2)

# 22. pkglist verification codes present
def test_pkglist_codes():
    codes = load_pkglist_verifications()
    for name in ("fentclient", "lure", "portbaby", "talisman"):
        assert name in codes, f"{name} missing from pkglist"
check("pkglist: verification codes for 4 plugins", test_pkglist_codes)

# 23. fentclient + talisman hashes match
def test_pkglist_hashes_1():
    codes = load_pkglist_verifications()
    for name in ("fentclient", "talisman"):
        h = compute_plugin_hash(name=name)
        assert h == codes[name], f"{name}: {h[:16]} vs {codes[name][:16]}"
check("pkglist: fentclient + talisman hashes match", test_pkglist_hashes_1)

# 24. lure + portbaby hashes match
def test_pkglist_hashes_2():
    codes = load_pkglist_verifications()
    for name in ("lure", "portbaby"):
        h = compute_plugin_hash(name=name)
        assert h == codes[name], f"{name}: {h[:16]} vs {codes[name][:16]}"
check("pkglist: lure + portbaby hashes match", test_pkglist_hashes_2)

# 25. Plugin files may be unsigned at strict 0 (load anything)
def test_plugin_unsigned_ok():
    init_path = os.path.join(PROJECT_DIR, "plugins", "fentclient", "__init__.py")
    v, level, author, detail = verify_signature(init_path)
    assert isinstance(v, bool) and level in (TRUST_UNSIGNED, TRUST_UNKNOWN, TRUST_TENTARI)
    assert detail, "no detail message"
check("verify: plugin unsigned is OK at strict 0", test_plugin_unsigned_ok)

# Cleanup
import shutil
shutil.rmtree(TMP, ignore_errors=True)

print(f"\n{'='*50}")
print(f"SIGNING VERIFICATION: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL LOCAL SIGNING TESTS PASSED (offline)")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
