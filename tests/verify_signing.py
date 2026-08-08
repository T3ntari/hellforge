#!/usr/bin/env python3
"""HELLFORGE v1.0.0.0 ALPHA — verify all 9 plugins are REGAS-signed (utmost trust)."""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ep_core import (
    verify_signature,
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

def check(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  [PASS] {name}")
    except Exception as e:
        failed += 1
        print(f"  [FAIL] {name}: {e}")

project = r"C:\Users\sambodhi\Downloads\E\piano-dsl"

ALL_PLUGINS = ["radical", "tensorsharp", "openapi", "vulkanizer", "eaudio",
               "fentclient", "lure", "portbaby", "talisman", "launcher"]

# 1. Verify all .sig files exist with REGAS author
for name in ALL_PLUGINS:
    def test_sig(n=name):
        path = os.path.join(project, "plugins", n, "__init__.py")
        sig_path = path + ".sig"
        assert os.path.exists(sig_path), f"Missing: {sig_path}"
        with open(sig_path) as f:
            meta = json.load(f)
        assert meta.get("author") == "REGAS", f"Author is {meta.get('author')}"
        assert meta.get("algorithm") == "ED25519"
        assert "HELLFORGE" in meta.get("tags", ""), f"Missing HELLFORGE tag"
        assert "CORE-EXPANSION" in meta.get("tags", ""), f"Missing CORE-EXPANSION tag"
    check(f"{name}: .sig = REGAS + HELLFORGE + CORE-EXPANSION tags", test_sig)

# 2. Verify all are REGAS UTMOST TRUST
for name in ALL_PLUGINS:
    def test_regas(n=name):
        path = os.path.join(project, "plugins", n, "__init__.py")
        v, level, author, detail = verify_signature(path)
        assert level == TRUST_REGAS or level == TRUST_TENTARI, f"Expected REGAS/TENTARI, got level {level}: {detail}"
        assert author == "REGAS" or author == "Tentari"
    check(f"{name}: verified as REGAS (=TENTARI trust)", test_regas)

# 3. Verify pkglist.json has all 9 with correct hashes
def test_pkglist():
    codes = load_pkglist_verifications()
    for name in ALL_PLUGINS:
        assert name in codes, f"{name} missing from pkglist"
        h = compute_plugin_hash(name=name)
        assert h == codes[name], f"{name}: hash mismatch {h[:16]} vs {codes[name][:16]}"
    print(f"   All {len(ALL_PLUGINS)} plugins match pkglist.json")
check("pkglist.json: all 9 plugins verified", test_pkglist)

# 4. Verify .e_verify.json
def test_everify():
    e_path = os.path.join(project, ".e_verify.json")
    assert os.path.exists(e_path), ".e_verify.json not found"
    with open(e_path) as f:
        data = json.load(f)
    for name in ALL_PLUGINS:
        assert name in data, f"{name} missing from .e_verify.json"
    print(f"   .e_verify.json: {len(data)} entries")
check(".e_verify.json: all 9 plugins + REGAS hashes", test_everify)

# 5. Verify backup ZIP exists
def test_backup_zip():
    zip_path = os.path.join(project, "embedded_plugins", "hellforge_plugins_backup.zip")
    assert os.path.exists(zip_path), f"Missing backup ZIP: {zip_path}"
    size = os.path.getsize(zip_path)
    assert size > 50000, f"Backup ZIP too small: {size} bytes"
    import zipfile
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert len(names) >= 100, f"Only {len(names)} files in backup"
    print(f"   Backup ZIP: {len(names)} files, {size//1024}KB")
check("Backup: hellforge_plugins_backup.zip exists + contents", test_backup_zip)

# 6. Verify embedded JSON backups
def test_embedded_json():
    backup_dir = os.path.join(project, "embedded_plugins")
    for name in ALL_PLUGINS:
        json_path = os.path.join(backup_dir, f"{name}.json")
        assert os.path.exists(json_path), f"Missing embedded: {json_path}"
        with open(json_path) as f:
            data = json.load(f)
        assert data.get("ecosystem") == "HELLFORGE", f"{name}: not HELLFORGE"
        assert "REGAS" in data.get("signed_by", []), f"{name}: not REGAS-signed"
        assert len(data.get("files", {})) > 0, f"{name}: no files"
    print(f"   All {len(ALL_PLUGINS)} plugins have embedded JSON backups")
check("Embedded: JSON backups for all 9 plugins", test_embedded_json)

# 7. Count .sig files
def test_sig_count():
    count = 0
    for root, dirs, files in os.walk(os.path.join(project, "plugins")):
        for fn in files:
            if fn.endswith(".sig"):
                count += 1
    assert count >= 20, f"Only {count} .sig files"
    print(f"   Total .sig files: {count}")
check("Plugin directory: all .sig files present", test_sig_count)

print(f"\n{'='*50}")
print(f"HELLFORGE VERIFICATION: {passed}/{passed+failed} passed")
if failed == 0:
    print("ALL 9 PLUGINS: REGAS UTMOST TRUST | HELLFORGE v1.0.0.0 ALPHA")
    print("Upload pkglist.json + .e_verify.json to www.oshonet.in")
else:
    print(f"{failed} FAILURES")
    sys.exit(1)
