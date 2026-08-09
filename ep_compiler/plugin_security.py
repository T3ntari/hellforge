"""HELLFORGE plugin security — integrity hashes for installed plugins.

Moved out of the removed fentclient plugin so the open-source release keeps
offline plugin-integrity checking without the internal backend. No network
code: verification is local-only (pkglist.json hashes).
"""

import hashlib
import json
import os
from pathlib import Path

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PLUGINS_DIR = PROJECT_DIR / "plugins"

_VERIFICATION_CACHE = None


def compute_plugin_hash(plugin_dir=None, name=None):
    """SHA-256 over all files of a plugin dir (path + bytes)."""
    if plugin_dir is None:
        if name is None:
            return None
        plugin_dir = PLUGINS_DIR / name
    plugin_dir = Path(plugin_dir)
    if not plugin_dir.is_dir():
        return None
    h = hashlib.sha256()
    files = sorted(plugin_dir.rglob("*"),
                   key=lambda p: str(p.relative_to(plugin_dir)))
    for f in files:
        if f.is_file() and "__pycache__" not in f.parts:
            rel = str(f.relative_to(plugin_dir))
            try:
                data = f.read_bytes()
                h.update(rel.encode("utf-8"))
                h.update(data)
            except Exception:
                pass
    return h.hexdigest()


def load_pkglist_verifications():
    """Plugin name -> verification code from pkglist.json (local only)."""
    try:
        pkglist_path = PROJECT_DIR / "pkglist.json"
        if not pkglist_path.exists():
            return {}
        with open(pkglist_path, "r") as f:
            data = json.load(f)
        result = {}
        for ptype in ("plugins", "mods"):
            for name, info in data.get(ptype, {}).items():
                code = info.get("verification", "")
                if code:
                    result[name] = code
        return result
    except Exception:
        return {}


def refresh_verification_cache(force=False):
    """Local pkglist codes, cached per process."""
    global _VERIFICATION_CACHE
    if _VERIFICATION_CACHE and not force:
        return _VERIFICATION_CACHE
    local = load_pkglist_verifications()
    if local:
        _VERIFICATION_CACHE = local
    return local


def verify_plugin_integrity(name):
    """(valid, expected, actual, detail) for a plugin name."""
    codes = refresh_verification_cache()
    expected = codes.get(name, "")
    if not expected:
        return (False, "", "", "No verification code in registry")
    actual = compute_plugin_hash(name=str(name)) or ""
    if actual == expected:
        return (True, expected, actual, "Integrity verified")
    return (False, expected, actual, "Code mismatch — plugin may be altered")
