"""HELLFORGE plugin security — integrity hashes for installed plugins.

Offline plugin-integrity checking for the open-source release — no
backend, no hardcoded endpoints. No network
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
    """Verification codes, cached per process.

    Source order:
      1. Remote registry — ONLY when HF_VERIFY_URL is set (opt-in, private
         installs). A Bearer token is sent when HF_VERIFY_TOKEN is set.
      2. Local pkglist.json codes.

    The public repo ships with no endpoint and no token: everything here is
    env-driven, so the open-source tree contains zero private info while
    private installs keep proving integrity against their own backend.
    """
    global _VERIFICATION_CACHE
    if _VERIFICATION_CACHE and not force:
        return _VERIFICATION_CACHE
    remote = _fetch_remote_verifications()
    if remote:
        _VERIFICATION_CACHE = remote
        return remote
    local = load_pkglist_verifications()
    if local:
        _VERIFICATION_CACHE = local
    return local


def _fetch_remote_verifications():
    """Fetch codes from the private registry configured via env. Returns
    None (never raises) when not configured or unreachable."""
    import urllib.request
    url = os.environ.get("HF_VERIFY_URL", "")
    if not url:
        return None
    try:
        req = urllib.request.Request(url,
                                     headers={"User-Agent": "E-Lang/Verify/1.0"})
        token = os.environ.get("HF_VERIFY_TOKEN", "")
        if token:
            req.add_header("Authorization", "Bearer " + token)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        codes = {}
        for ptype in ("plugins", "mods"):
            for name, info in data.get(ptype, {}).items():
                code = info.get("verification", "") if isinstance(info, dict) else ""
                if code:
                    codes[name] = code
        return codes or None
    except Exception:
        return None


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

def get_device_id():
    """Local persistent device ID (no network, no backend)."""
    from ep_core import IDENTITY_DIR
    dev_path = IDENTITY_DIR / ".device_id"
    if dev_path.exists():
        try:
            with open(dev_path) as f:
                return f.read().strip()
        except Exception:
            pass
    import hashlib as _h
    dev_id = _h.sha256(os.urandom(32)).hexdigest()[:32]
    try:
        os.makedirs(IDENTITY_DIR, exist_ok=True)
        with open(dev_path, "w") as f:
            f.write(dev_id)
    except Exception:
        pass
    return dev_id
