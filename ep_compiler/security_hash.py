"""HELLFORGE core integrity — committed code-structure digest.

Every CLI start / initialization recomputes this digest and compares it
against the committed SECURITY_HASH.txt (and optionally the live copy on
GitHub). Any change to the core structure — an altered file, a new plugin
directory (fentclient-style), a removed file — flags the system.

Digest: one line per covered file with its SHA-512, then an aggregate
triple-digest (SHA-256 + SHA-512 + BLAKE2b-512, 320 hex chars = 160 bytes)
over the sorted manifest. The manifest is committed to the repo, so anyone
can verify the code directly from GitHub: compare
https://raw.githubusercontent.com/T3ntari/hellforge/main/SECURITY_HASH.txt
with the local computation.

Regenerate after intentional core changes:
    python3 tools/gen_security_hash.py
"""

import hashlib
import json
import os
from pathlib import Path

PROJECT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MANIFEST_PATH = PROJECT_DIR / "SECURITY_HASH.txt"

DIGEST_NAMES = ("sha256", "sha512", "blake2b_512")


def covered_files():
    """Relative paths of the files the digest covers (self excluded)."""
    files = []
    for name in ("ep_core.py", "eshell.py", "ep_pkg.py", "pkglist.json"):
        p = PROJECT_DIR / name
        if p.is_file():
            files.append(name)
    comp = PROJECT_DIR / "ep_compiler"
    if comp.is_dir():
        for p in sorted(comp.glob("*.py")):
            if p.name != "security_hash.py":
                files.append(f"ep_compiler/{p.name}")
    plugs = PROJECT_DIR / "plugins"
    if plugs.is_dir():
        for p in sorted(plugs.glob("*/__init__.py")):
            files.append(f"plugins/{p.parent.name}/__init__.py")
    return sorted(files)


def sha512_of(path):
    h = hashlib.sha512()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def compute_manifest():
    """{relative_path: sha512} for every covered file."""
    out = {}
    for rel in covered_files():
        p = PROJECT_DIR / rel
        if p.is_file():
            out[rel] = sha512_of(p)
    return out


def aggregate(manifest):
    """Triple-digest over the sorted manifest lines."""
    lines = [f"{rel}:{h}" for rel, h in sorted(manifest.items())]
    payload = "\n".join(lines).encode()
    return {
        "sha256": hashlib.sha256(payload).hexdigest(),
        "sha512": hashlib.sha512(payload).hexdigest(),
        "blake2b_512": hashlib.blake2b(payload, digest_size=64).hexdigest(),
    }


def digest_bundle(manifest):
    agg = aggregate(manifest)
    return ".".join(agg[n] for n in DIGEST_NAMES)


def load_committed():
    """(manifest, bundle) from SECURITY_HASH.txt, or (None, None)."""
    try:
        text = MANIFEST_PATH.read_text().strip().splitlines()
    except OSError:
        return None, None
    manifest = {}
    bundle = None
    for line in text:
        if ":" in line and len(line.split(":")) == 2:
            rel, h = line.split(":", 1)
            if rel and len(h) == 128 and all(c in "0123456789abcdef" for c in h):
                manifest[rel] = h
        elif line.startswith("AGGREGATE="):
            bundle = line.split("=", 1)[1]
    return (manifest or None), bundle


def verify():
    """Full integrity check. Returns a dict:
    ok, bundle, committed, changed, missing, extra_dirs, detail"""
    manifest = compute_manifest()
    bundle = digest_bundle(manifest)
    committed, committed_bundle = load_committed()
    changed, missing = [], []
    if committed:
        for rel, h in sorted(manifest.items()):
            if rel not in committed:
                changed.append(rel)
            elif committed[rel] != h:
                changed.append(rel)
        for rel in sorted(committed):
            if rel not in manifest:
                missing.append(rel)
    # plugin dirs present but NOT covered (e.g. an unlisted plugin sneaked in)
    extra_dirs = []
    plugs = PROJECT_DIR / "plugins"
    if plugs.is_dir():
        for d in sorted(plugs.iterdir()):
            if not d.is_dir() or d.name == "__pycache__":
                continue
            rel = f"plugins/{d.name}/__init__.py"
            if rel not in manifest:
                extra_dirs.append(d.name)
    ok = (bundle == committed_bundle) and not changed and not missing and not extra_dirs
    detail = []
    if changed:
        detail.append(f"changed/added: {', '.join(changed)}")
    if missing:
        detail.append(f"missing: {', '.join(missing)}")
    if extra_dirs:
        detail.append(f"unlisted plugin dirs: {', '.join(extra_dirs)}")
    if committed_bundle and bundle != committed_bundle:
        detail.append("aggregate digest mismatch")
    if not committed_bundle:
        detail.append("no committed SECURITY_HASH.txt")
    return {
        "ok": ok, "bundle": bundle, "committed": committed_bundle,
        "changed": changed, "missing": missing,
        "extra_dirs": extra_dirs,
        "detail": "; ".join(detail) if detail else "core structure intact",
    }


def check_github(timeout=10):
    """Compare the local computation against the live GitHub copy (public
    repo — no secrets involved). Returns (ok, remote_bundle, note)."""
    import urllib.request
    url = ("https://raw.githubusercontent.com/T3ntari/hellforge/main/"
           "SECURITY_HASH.txt")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "E-Lang/Verify/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode()
    except Exception as e:
        return None, "", f"github unreachable: {e}"
    remote_bundle = None
    for line in text.splitlines():
        if line.startswith("AGGREGATE="):
            remote_bundle = line.split("=", 1)[1]
    local = digest_bundle(compute_manifest())
    if not remote_bundle:
        return None, "", "github copy has no aggregate"
    return (local == remote_bundle), remote_bundle, ""


def status_line(result):
    if result["ok"]:
        return "\033[32m[security]\033[0m core integrity OK"
    return ("\033[31m[security]\033[0m CORE INTEGRITY FLAGGED — "
            + (result["detail"] or "digest mismatch"))


def boot_check(stream_out=print):
    """Run at CLI start / every initialization."""
    r = verify()
    stream_out(status_line(r))
    if not r["ok"]:
        stream_out(f"\033[90m  expected: {r['committed'] or '(none)'}\033[0m")
        stream_out(f"\033[90m  actual  : {r['bundle']}\033[0m")
    return r["ok"]

# tamper
