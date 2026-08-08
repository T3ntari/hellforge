#!/usr/bin/env python3
"""HELLFORGE v1.0.0.0 ALPHA — Master signing + backup tool.
CORE-EXPANSION: REGAS — signs all core plugins with the REGAS key (utmost trust).
Also signs with TENTARI for third-party compatibility.
Generates embedded backup ZIP + JSON for all plugins."""

import sys
import os
import json
import hashlib
import time
import zipfile
import io
import base64

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from ep_core import (
    ed25519_sign, ed25519_verify,
    get_public_key, verify_signature,
    TRUST_REGAS, TRUST_TENTARI, TRUST_UNKNOWN, TRUST_UNSIGNED,
    save_identity_public_key,
)

# ── Keys ──
REGAS_SEED = "f4276ed787249144b874645205db461da959cd647af62902b7e0265a9a4f395c"
REGAS_PUB = "30722097f094e43f014548f39851710c5f6af87d586448caa4c1f3d21284ff2e"
TENTARI_SEED = "06000c1b473f5c92a4c8b5c9012eaf1d766340b03f28e99ac999b05024c3e3d6"

# Verify keys match
assert get_public_key("REGAS") == REGAS_PUB, "REGAS pub key mismatch!"
pub_tentari = get_public_key("Tentari")
assert pub_tentari, "Tentari key missing!"

# Save REGAS as trusted key for runtime verification
save_identity_public_key("REGAS", REGAS_PUB)

# ── All core plugins ──
ALL_PLUGINS = {
    "radical": "plugins/radical",
    "tensorsharp": "plugins/tensorsharp",
    "openapi": "plugins/openapi",
    "vulkanizer": "plugins/vulkanizer",
    "eaudio": "plugins/eaudio",
    "fentclient": "plugins/fentclient",
    "lure": "plugins/lure",
    "portbaby": "plugins/portbaby",
    "talisman": "plugins/talisman",
}

TAGS = "HELLFORGE,CORE-EXPANSION:REGAS,TENTARI"

def get_all_py_files(plugin_dir):
    """Get all .py files in a plugin directory, sorted."""
    files = []
    for root, dirs, fnames in os.walk(plugin_dir):
        for fn in sorted(fnames):
            if fn.endswith(".py"):
                files.append(os.path.join(root, fn))
    return files

def sign_file_with_key(filepath, seed, author):
    """Sign a file with the given key and write .sig sidecar."""
    with open(filepath, "rb") as f:
        data = f.read()
    sig = ed25519_sign(data, seed)
    meta = {
        "algorithm": "ED25519",
        "signature": sig,
        "timestamp": time.time(),
        "file": os.path.basename(filepath),
        "author": author,
        "tags": TAGS,
        "social": {"Instagram": "@hellforge", "Discord": "@hellforge-core"},
    }
    sig_path = filepath + ".sig"
    with open(sig_path, "w") as f:
        json.dump(meta, f, indent=2)
    return sig

def verify_file(filepath):
    """Verify a file's signature. Returns (is_valid, trust_level, author, detail)."""
    v, level, author, detail = verify_signature(filepath)
    return v, level, author, detail

# ── Phase 1: Sign all plugins with REGAS (core) key ──

print("=" * 60)
print("HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS")
print("=" * 60)
print(f"\nPhase 1: Signing all plugins with REGAS key (utmost trust)...\n")

signed_regas = 0
signed_tentari = 0
failed = 0

for name, rel_dir in sorted(ALL_PLUGINS.items()):
    plugin_dir = os.path.join(PROJECT, rel_dir)
    if not os.path.isdir(plugin_dir):
        print(f"  [SKIP] {name}: dir not found")
        continue

    py_files = get_all_py_files(plugin_dir)
    if not py_files:
        print(f"  [SKIP] {name}: no .py files")
        continue

    # Sign with TENTARI first (compatibility)
    for fp in py_files:
        sign_file_with_key(fp, TENTARI_SEED, "Tentari")
    signed_tentari += 1

    # Sign with REGAS LAST (overwrites .sig — highest trust for verification)
    for fp in py_files:
        sign_file_with_key(fp, REGAS_SEED, "REGAS")
    signed_regas += 1

    # Verify REGAS signature
    init_path = os.path.join(plugin_dir, "__init__.py")
    if os.path.exists(init_path):
        v, level, author, detail = verify_file(init_path)
        if level == TRUST_REGAS:
            print(f"  [REGAS] {name}: {author} (UTMOST TRUST)")
        elif level == TRUST_TENTARI:
            print(f"  [TENTARI] {name}: {author} (TRUSTED)")
        else:
            print(f"  [WARN] {name}: {author} ({detail})")
            failed += 1

print(f"\n  REGAS signed: {signed_regas}/{len(ALL_PLUGINS)}")
print(f"  TENTARI signed: {signed_tentari}/{len(ALL_PLUGINS)}")
print(f"  Failed: {failed}")

# ── Phase 2: Compute verification hashes ──

print(f"\nPhase 2: Computing verification hashes...\n")

from plugins.fentclient.security import compute_plugin_hash

hashes = {}
for name in sorted(ALL_PLUGINS.keys()):
    h = compute_plugin_hash(name=name)
    if h:
        hashes[name] = h
        print(f"  {name}: {h[:16]}...")
    else:
        print(f"  [ERR] {name}: hash failed")

# ── Phase 3: Update pkglist.json ──

print(f"\nPhase 3: Updating pkglist.json...\n")

pkglist_path = os.path.join(PROJECT, "pkglist.json")
with open(pkglist_path, "r") as f:
    pkglist = json.load(f)

pkglist["version"] = "1.0.0.0"
pkglist["ecosystem"] = "HELLFORGE"
pkglist["core_expansion"] = "REGAS"
pkglist["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")

plugin_descriptions = {
    "radical": "GPU Shader Math Core — GLSL compute shader evaluation, multi-GPU, VRAM control",
    "tensorsharp": "NVIDIA Tensor Core acceleration — mixed-precision matrix math via CuPy",
    "openapi": "Low-level OpenGL Graphics API — context, shaders, buffers, textures, render pipeline",
    "vulkanizer": "Low-level Vulkan API — compute, ray tracing (VK_KHR), custom temporal upscaling",
    "eaudio": "Low-level Audio API — device management, PCM buffers, 3D spatial, DSP effects",
    "fentclient": "Performance accelerator, bug fixes, enhanced syntax, FluidSynth, arpeggiator, cache",
    "lure": "Lua Runtime Accelerator — LuaJIT-powered hot-path parsing, async compile",
    "portbaby": "Syntax version porting — convert between v1/v2/v3/v4 with loss reporting",
    "talisman": "Audio culling & occlusion engine — psychoacoustic masking, privacy mode",
}

plugin_tags = {
    "radical": TAGS + ",gpu,compute,shader,glsl,math",
    "tensorsharp": TAGS + ",cuda,tensorcore,nvidia,matmul",
    "openapi": TAGS + ",opengl,graphics,rendering,api",
    "vulkanizer": TAGS + ",vulkan,compute,raytracing,upscaling",
    "eaudio": TAGS + ",audio,spatial,dsp,effects,3d",
    "fentclient": TAGS + ",performance,acceleration,bugfix,soundfont",
    "lure": TAGS + ",luajit,jit,compiler,acceleration,async",
    "portbaby": TAGS + ",conversion,syntax,porting,v1,v2,v3,v4",
    "talisman": TAGS + ",audio,culling,occlusion,masking,privacy",
}

for name in sorted(ALL_PLUGINS.keys()):
    if name in hashes:
        if name in pkglist.get("plugins", {}):
            pkglist["plugins"][name]["verification"] = hashes[name]
            pkglist["plugins"][name]["tags"] = plugin_tags.get(name, TAGS)
        else:
            info = {
                "version": "1.0.0.0",
                "description": plugin_descriptions.get(name, f"HELLFORGE plugin: {name}"),
                "author": "REGAS",
                "tags": plugin_tags.get(name, TAGS),
                "url": f"file://plugins/{name}/__init__.py",
                "update_url": "",
                "dependencies": [],
                "verification": hashes[name],
                "verification_domain": "www.oshonet.in",
            }
            if "plugins" not in pkglist:
                pkglist["plugins"] = {}
            pkglist["plugins"][name] = info
        print(f"  {name}: updated in pkglist")

with open(pkglist_path, "w") as f:
    json.dump(pkglist, f, indent=2)
print(f"  -> pkglist.json saved ({len(pkglist.get('plugins', {}))} plugins)")

# ── Phase 4: Generate .e_verify.json ──

print(f"\nPhase 4: Generating .e_verify.json...\n")

everify = {}
for name, h in hashes.items():
    everify[name] = h

everify_path = os.path.join(PROJECT, ".e_verify.json")
with open(everify_path, "w") as f:
    json.dump(everify, f, indent=2)
print(f"  -> .e_verify.json saved ({len(everify)} entries)")

# ── Phase 5: Create embedded backup ZIP ──

print(f"\nPhase 5: Creating embedded backup ZIP...\n")

backup_dir = os.path.join(PROJECT, "embedded_plugins")
os.makedirs(backup_dir, exist_ok=True)

zip_path = os.path.join(backup_dir, "hellforge_plugins_backup.zip")
all_files = []
for name, rel_dir in sorted(ALL_PLUGINS.items()):
    plugin_dir = os.path.join(PROJECT, rel_dir)
    if os.path.isdir(plugin_dir):
        for root, dirs, fnames in os.walk(plugin_dir):
            for fn in fnames:
                if not fn.endswith(".pyc") and "__pycache__" not in root:
                    fp = os.path.join(root, fn)
                    arcname = os.path.relpath(fp, PROJECT)
                    all_files.append((fp, arcname))

with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for fp, arcname in sorted(all_files):
        zf.write(fp, arcname)

zip_size = os.path.getsize(zip_path)
print(f"  -> hellforge_plugins_backup.zip: {len(all_files)} files, {zip_size//1024}KB")

# ── Phase 6: Generate embedded JSON backups ──

print(f"\nPhase 6: Generating embedded JSON backups...\n")

for name, rel_dir in sorted(ALL_PLUGINS.items()):
    plugin_dir = os.path.join(PROJECT, rel_dir)
    if not os.path.isdir(plugin_dir):
        continue

    # Collect all files in the plugin directory
    files_data = {}
    for root, dirs, fnames in os.walk(plugin_dir):
        for fn in sorted(fnames):
            if fn.endswith(".pyc"):
                continue
            if "__pycache__" in root:
                continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, os.path.dirname(plugin_dir))
            with open(fp, "rb") as f:
                content = f.read()
            files_data[rel] = base64.b64encode(content).decode("ascii")

    backup = {
        "plugin": name,
        "version": "1.0.0.0",
        "ecosystem": "HELLFORGE",
        "core_expansion": "REGAS",
        "signed_by": ["REGAS", "Tentari"],
        "files": files_data,
        "timestamp": time.time(),
    }

    json_path = os.path.join(backup_dir, f"{name}.json")
    with open(json_path, "w") as f:
        json.dump(backup, f, indent=2)
    
    json_size = os.path.getsize(json_path)
    print(f"  {name}: {len(files_data)} files, {json_size//1024}KB")

# ── Phase 7: Final verification ──

print(f"\n" + "=" * 60)
print("Phase 7: Final verification")
print("=" * 60)

verified_regas = 0
verified_tentari = 0
unverified = 0

for name, rel_dir in sorted(ALL_PLUGINS.items()):
    plugin_dir = os.path.join(PROJECT, rel_dir)
    init_path = os.path.join(plugin_dir, "__init__.py")
    if not os.path.exists(init_path):
        continue

    # Check REGAS signature
    v, level, author, detail = verify_file(init_path)
    if level == TRUST_REGAS:
        print(f"  [REGAS] {name}: {author} (UTMOST TRUST)")
        verified_regas += 1
    elif level == TRUST_TENTARI:
        print(f"  [TENTARI] {name}: {author} (TRUSTED)")
        verified_tentari += 1
    else:
        print(f"  [UNSIGNED] {name}: {detail}")
        unverified += 1

print(f"\n  REGAS (utmost trust): {verified_regas}")
print(f"  TENTARI (trusted): {verified_tentari}")
print(f"  Unsigned: {unverified}")
print(f"\nHELLFORGE v1.0.0.0 ALPHA — READY")
print(f"Backup: {zip_path}")
print(f"Embedded: {backup_dir}")
