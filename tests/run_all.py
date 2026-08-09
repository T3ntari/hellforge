#!/usr/bin/env python3
"""Comprehensive test suite for signing, strict enforcement, and Talisman."""
import sys
import os
import json
import tempfile
import shutil
import hashlib
import base64
import time

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

passed = 0
failed = 0
TMP = tempfile.mkdtemp(prefix="e_test_")

def test(name, fn):
    global passed, failed
    try:
        fn()
        passed += 1
        print(f"  \033[92m[PASS]\033[0m {name}")
    except Exception as e:
        failed += 1
        import traceback
        traceback.print_exc()
        print(f"  \033[91m[FAIL]\033[0m {name}: {e}")

# ── Signing Tests ──

from ep_core import (
    ed25519_generate_key, ed25519_sign, ed25519_verify,
    identity_exists, create_identity, load_identity,
    sign_file, verify_signature,
    get_strict_signing, set_strict_signing,
    TRUST_TENTARI, TRUST_UNKNOWN, TRUST_UNSIGNED,
    _STRICT_SIGNING,
)

# Ensure identity exists for signing
if not identity_exists():
    create_identity("TestRunner", {})
id = load_identity()
print(f"[SETUP] Identity: {id.get('name')}")

# 1. Strict signing level control
def test_strict_levels():
    set_strict_signing(0)
    assert get_strict_signing() == 0
    set_strict_signing(1)
    assert get_strict_signing() == 1
    set_strict_signing(2)
    assert get_strict_signing() == 2
    set_strict_signing(1)  # reset
test("Strict signing levels 0/1/2", test_strict_levels)

# 2. Sign a plugin file
def test_sign_plugin():
    p = os.path.join(TMP, "test_plugin.py")
    with open(p, "w") as f:
        f.write('"""Test plugin."""\nVERSION = "1.0.0"\nauthor = "Test"\n')
    result = sign_file(p, embed=False)
    assert result is not None
    assert result["algorithm"] == "ED25519"
    assert os.path.exists(p + ".sig"), "Sidecar .sig should exist"
    v, level, author, detail = verify_signature(p)
    assert v, f"Should verify: {detail}"
test("Sign plugin + verify", test_sign_plugin)

# 3. Verify detection of unsigned file
def test_unsigned():
    p = os.path.join(TMP, "unsigned.e")
    with open(p, "w") as f:
        f.write("@bpm 120")
    v, level, author, detail = verify_signature(p)
    assert not v
    assert level == TRUST_UNSIGNED
test("Unsigned file detection", test_unsigned)

# 4. Tamper detection
def test_tamper():
    p = os.path.join(TMP, "tamper.e")
    with open(p, "w") as f:
        f.write("original")
    sign_file(p)
    with open(p, "a") as f:
        f.write("\ntampered")
    v, level, author, detail = verify_signature(p)
    assert not v, "Tampered should fail verify"
    assert "mismatch" in detail.lower()
test("Tamper detection", test_tamper)

# 5. Multiple file types sign+verify
def test_multi_types():
    types = {".e": "test", ".py": "print('x')", ".mid": b"MIDI", ".txt": "plain"}
    for ext, content in types.items():
        p = os.path.join(TMP, f"multi{ext}")
        mode = "wb" if isinstance(content, bytes) else "w"
        with open(p, mode) as f:
            f.write(content)
        r = sign_file(p)
        assert r is not None, f"Failed to sign {ext}"
        v, l, a, d = verify_signature(p)
        assert v, f"{ext} verify failed: {d}"
test("Multi-type sign+verify", test_multi_types)

# 6. Verify Tentari plugin hashes match pkglist codes
# (fentclient is removed from the open-source release — remaining plugins)
def test_plugin_hashes():
    from ep_compiler.plugin_security import (
        compute_plugin_hash,
        load_pkglist_verifications,
    )
    codes = load_pkglist_verifications()
    for name in ("lure", "portbaby", "talisman"):
        assert name in codes, f"{name} should have verification code"
        h = compute_plugin_hash(name=name)
        assert h == codes[name], f"{name} hash mismatch: {h[:16]} vs {codes[name][:16]}"
    print(f"  Tentari plugin hashes verified against pkglist")
test("Tentari plugin hashes match pkglist", test_plugin_hashes)

# ── Talisman Tests ──

from plugins.talisman import (
    register as _register_talisman,
    cull_and_occlude,
    get_culling_enabled,
    set_culling_enabled,
)

# Register talisman plugin properly (simulates what load_plugins does)
from ep_core import _PluginAPI
_talisman_api = _PluginAPI()
_register_talisman(_talisman_api)

# 7. Talisman culling basic
def test_cull_basic():
    ev = [{"timestamp": 0, "midi": 60, "duration": 500, "velocity": 100},
          {"timestamp": 0, "midi": 64, "duration": 500, "velocity": 5}]
    result, culled, occluded = cull_and_occlude(ev)
    assert culled == 1, f"Expected 1 culled, got {culled}"
    assert len(result) == 1
test("Talisman: quiet note culled", test_cull_basic)

# 8. Talisman occlusion
def test_cull_occlude():
    ev = [{"timestamp": 0, "midi": 60, "duration": 500, "velocity": 100},
          {"timestamp": 0, "midi": 64, "duration": 500, "velocity": 30}]
    result, culled, occluded = cull_and_occlude(ev)
    assert occluded == 1, f"Expected 1 occluded, got {occluded}"
    assert result[1]["velocity"] < 30, "Velocity should be reduced"
test("Talisman: occlusion reduces velocity", test_cull_occlude)

# 9. Talisman toggle
def test_cull_toggle():
    set_culling_enabled(False)
    assert get_culling_enabled() == False
    set_culling_enabled(True)
    assert get_culling_enabled() == True
test("Talisman toggle on/off", test_cull_toggle)

# 10. Compile with culling via post_compile hook
def test_cull_compile():
    set_culling_enabled(True)
    from ep_compiler.compile import compile_source
    from ep_core import trigger_event
    ev, bp = compile_source("T0 N60 D500 V100\nT0 N64 D500 V10")
    # The post_compile hook should trigger talisman culling
    # But the hook fires inside compile_source, so events should already be culled
    # If N64 had V10, it should be culled by talisman
    n64 = [e for e in ev if e["midi"] == 64]
    assert len(n64) == 0, f"N64 should be culled (vel 10), got {len(n64)} events"
test("Compile pipeline triggers talisman culling", test_cull_compile)

# ── Backend Tests ──

# 11. Plugin integrity verification (offline) — fentclient's backend
# integration is removed from the open-source release; the harness remains.
def test_backend_code():
    pass
test("Backend: integrity harness (fentclient removed)", test_backend_code)

# 12. Backend rejects wrong code (local mismatch detection)
def test_backend_wrong_code():
    pass
test("Backend: integrity harness (fentclient removed)", test_backend_wrong_code)

# ── Compiler Math Tests ──

# 13. Math + variables + loop compile
def test_math_pipeline():
    from ep_compiler.compile import compile_source
    source = "$bpm = 120\nfor $i = 0 to 3 {\nT{$i * 250} N{60 + $i} D200 V80\n}"
    ev, bp = compile_source(source)
    assert len(ev) == 4, f"Expected 4 events, got {len(ev)}"
    assert ev[0]["timestamp"] == 0
    assert ev[1]["timestamp"] == 250
    assert ev[2]["timestamp"] == 500
    assert ev[3]["timestamp"] == 750
    assert ev[0]["midi"] == 60
    assert ev[3]["midi"] == 63
test("Math pipeline: for loop + variables", test_math_pipeline)

# 14. Talisman local mode
def test_talisman_local():
    from plugins.talisman import (
        get_local_mode,
        set_local_mode,
    )
    set_local_mode(True)
    assert get_local_mode() == True
    set_local_mode(False)
    assert get_local_mode() == False
test("Talisman local mode toggle", test_talisman_local)

# 15. Talisman auto-backup
def test_talisman_backup():
    from plugins.talisman import (
        get_auto_backup,
        set_auto_backup,
    )
    set_auto_backup(True)
    assert get_auto_backup() == True
    set_auto_backup(False)
    assert get_auto_backup() == False
    # Test that backup dir is created
    import shutil
    import os
    backup_root = os.path.join(os.path.dirname(__file__), "..", ".e_backups")
    if os.path.exists(backup_root):
        shutil.rmtree(backup_root)
    set_auto_backup(True)
    from ep_compiler.compile import compile_source
    ev, bp = compile_source("T0 N60 D500")
    assert os.path.exists(backup_root), "Backup dir should exist"
    files = os.listdir(backup_root)
    assert len(files) > 0, f"Should have backup files, got {files}"
    set_auto_backup(False)
    if os.path.exists(backup_root):
        shutil.rmtree(backup_root)
    print(f"  Backup files created: {len(files)}")
test("Talisman auto-backup", test_talisman_backup)

# 16. Talisman inspect (compile + verify event data accuracy)
def test_talisman_inspect():
    from ep_compiler.compile import compile_source
    ev, bp = compile_source("T0 N60 D500 V100\nT250 N64 D500 V80\nT500 N67 D500 V60")
    assert len(ev) == 3
    vels = [e["velocity"] for e in ev]
    assert min(vels) == 60
    assert max(vels) == 100
    assert sum(vels)//len(vels) == 80
    print(f"  3 events, velocities {min(vels)}-{max(vels)}, avg {sum(vels)//len(vels)}")
test("Talisman inspect data accuracy", test_talisman_inspect)

# 17. Talisman stats
def test_talisman_stats():
    from plugins.talisman import (
        _compile_count,
        _last_compile_events,
    )
    # After previous compilations, count should be > 0
    from ep_compiler.compile import compile_source
    compile_source("T0 N60 D500")
    assert _compile_count > 0, f"Compile count should be > 0, got {_compile_count}"
    assert len(_last_compile_events) > 0, "Should have events"
    print(f"  {_compile_count} compiles tracked")
test("Talisman stats tracking", test_talisman_stats)

# 18. Expression evaluation
def test_expressions():
    from ep_compiler.math_engine import (
        build_ast,
        ast_to_dict,
    )
    from ep_compiler.variables import (
        evaluate_expression,
        Scope,
    )
    scope = Scope()
    scope.set("x", 5)
    val, err = evaluate_expression("$x * 2 + 1", scope)
    assert val == 11
    val2, err2 = evaluate_expression("sin(0) * 100", scope)
    assert val2 is not None and abs(val2) < 0.01
test("Expression evaluation", test_expressions)

# Cleanup
shutil.rmtree(TMP, ignore_errors=True)

print(f"\n{'='*50}")
print(f"TESTS: {passed}/{passed+failed} passed")
if failed == 0:
    print("\033[92mALL TESTS PASSED\033[0m")
else:
    print(f"\033[91m{failed} FAILURES\033[0m")
    sys.exit(1)
