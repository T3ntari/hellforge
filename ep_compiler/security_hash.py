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
            if p.name not in ("security_hash.py", "_x_hide.py", "_version_key.py"):
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


# ──────────────────────────────────────────────────────────────────────
# Technique X — rotating hidden digest fragments (offline backup of the
# core digest) and Technique Y — the per-version key hash from GitHub.
#
# X: the 160-byte aggregate digest is split into tiny fragments and hidden
#    inside a generated core file (ep_compiler/_x_hide.py, gitignored) in
#    random order / chunk sizes / comment styles. Re-randomized on every
#    init. X verifies the CURRENT core state without any network: if a
#    covered file (or the X file itself) is tampered with, extraction
#    mismatches and the system enters SAFE MODE.
#
# Y: a permanent per-version key: blake2b512(aggregate + ":" + version tag).
#    Committed in ep_compiler/_version_key.py at release time. Verified
#    online against the live SECURITY_HASH.txt at the version tag on
#    GitHub — the version's canonical key hash.
#
# Boot order: X first (local) -> network? -> online: Y + version check.
# Offline: X alone is the proof.
# ──────────────────────────────────────────────────────────────────────

import random

X_FILE = PROJECT_DIR / "ep_compiler" / "_x_hide.py"
VERSION_KEY_FILE = PROJECT_DIR / "ep_compiler" / "_version_key.py"

_FRAG_STYLES = [
    ('# x.{i} = "{hex}"', '#' * (random.randint(4, 24))),
    ('_x{i} = "{hex}"  # core', '_XH'),
    ('#~ {hex} ~#', '/*' * 1),
]


def y_key(bundle, version_tag):
    """Technique Y: permanent per-version key hash (128 hex chars)."""
    return hashlib.blake2b((bundle + ":" + version_tag).encode(),
                           digest_size=64).hexdigest()


def local_version():
    """Current version tag from git (falls back to a constant)."""
    try:
        import subprocess
        r = subprocess.run(["git", "describe", "--tags", "--abbrev=0"],
                           capture_output=True, text=True, timeout=5,
                           cwd=str(PROJECT_DIR))
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    try:
        from ep_compiler._version_key import VERSION_TAG
        return VERSION_TAG
    except Exception:
        return "dev"


def load_version_key():
    """(version_tag, y) from ep_compiler/_version_key.py or (None, None)."""
    try:
        ns = {}
        exec(compile(VERSION_KEY_FILE.read_text(), str(VERSION_KEY_FILE), "exec"), ns)
        return ns.get("VERSION_TAG"), ns.get("VERSION_KEY")
    except Exception:
        return None, None


def _x_fragments(bundle):
    """Split the bundle into 6-16 tiny fragments with random sizes.
    Returns [(original_index, chunk)] — shuffled so the layout order is
    random, but every fragment keeps its index for reconstruction."""
    n = random.randint(6, 16)
    parts = []
    step = max(8, len(bundle) // n)
    i = 0
    while i < len(bundle):
        size = random.randint(4, max(8, step * 2))
        parts.append((i, bundle[i:i + size]))
        i += size
    random.shuffle(parts)
    return parts


def x_embed(bundle):
    """Hide the digest in random tiny fragments inside the X file. Returns
    the path."""
    frags = _x_fragments(bundle)
    lines = ['"""Technique X — rotating core-digest fragments. Generated on every',
             'init; random order / chunk sizes / positions. Do not edit."""',
             ""]
    for pos, (idx, fr) in enumerate(frags):
        style = random.choice(_FRAG_STYLES)
        if style[0].startswith("# x."):
            lines.append(f'# x.{idx} = "{fr}"')
        elif style[0].startswith("_x"):
            lines.append(f'_x{idx} = "{fr}"  # core')
        else:
            lines.append(f'#~ {idx}:{fr} ~#')
    # internal checksum of the X payload itself (detects X tampering)
    payload = "\n".join(fr for _, fr in sorted(frags)).encode()
    lines.append(f'_X_CHECK = "{hashlib.blake2b(payload, digest_size=32).hexdigest()}"')
    X_FILE.parent.mkdir(parents=True, exist_ok=True)
    X_FILE.write_text("\n".join(lines) + "\n")
    return X_FILE


def _x_extract():
    """Rebuild the bundle from the hidden fragments. None on failure."""
    try:
        text = X_FILE.read_text()
    except OSError:
        return None
    frags = {}
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("# x."):
            m = line.split('"')
            if len(m) >= 2:
                try:
                    frags[int(line[4:line.index("=")].strip())] = m[1]
                except Exception:
                    return None
        elif line.startswith("_x") and "=" in line and not line.startswith("_X_CHECK"):
            m = line.split('"')
            if len(m) >= 2:
                try:
                    frags[int(line[2:line.index("=")].strip())] = m[1]
                except Exception:
                    return None
        elif line.startswith("#~") and "~#" in line:
            inner = line[2:-2].strip()
            if ":" in inner:
                idx, fr = inner.split(":", 1)
                try:
                    frags[int(idx)] = fr
                except Exception:
                    return None
    if not frags:
        return None
    ordered = [frags[i] for i in sorted(frags)]
    # checksum must match the fragment payload (same join as x_embed)
    payload = "\n".join(ordered).encode()
    try:
        chk_line = [l for l in text.splitlines() if l.startswith("_X_CHECK")][0]
        expected = chk_line.split('"')[1]
        if hashlib.blake2b(payload, digest_size=32).hexdigest() != expected:
            return None
    except Exception:
        return None
    return "".join(ordered)


def x_verify():
    """Technique X check — the offline proof. Returns (ok, detail)."""
    hidden = _x_extract()
    if hidden is None:
        return False, "X fragments missing or tampered (no _x_hide.py)"
    current = digest_bundle(compute_manifest())
    if hidden != current:
        return False, ("X fragment digest does not match the current core "
                       "structure — a covered file was altered")
    return True, "X verified (hidden digest matches core structure)"


def x_rotate():
    """Re-hide the digest with a fresh random layout — called every init."""
    if x_verify()[0]:
        try:
            x_embed(digest_bundle(compute_manifest()))
            return True
        except Exception:
            return False
    return False


def remote_version(timeout=10):
    """Latest version tag on GitHub via git ls-remote (no API token)."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "ls-remote", "--tags",
             "https://github.com/T3ntari/hellforge.git"],
            capture_output=True, text=True, timeout=timeout)
        tags = []
        for line in r.stdout.splitlines():
            ref = line.split("	")[-1]
            if "refs/tags/v" in ref and "^{}" not in ref:
                tags.append(ref.replace("refs/tags/", ""))
        import re as _re
        def key(t):
            m = _re.match(r"v(\d+)\.(\d+)\.(\d+)(?:\.(\d+))?", t)
            if not m:
                return (0, 0, 0, 0)
            g = m.groups()
            return (int(g[0]), int(g[1]), int(g[2]), int(g[3]) if g[3] else 0)
        return max(tags, key=key) if tags else None
    except Exception:
        return None


def y_verify_online(timeout=15):
    """Technique Y check: compare the local version key against the live
    SECURITY_HASH.txt at the version tag on GitHub. Returns
    (ok, detail)."""
    import urllib.request
    tag, y_local = load_version_key()
    if not y_local:
        return False, "no committed version key"
    url = (f"https://raw.githubusercontent.com/T3ntari/hellforge/"
           f"{tag}/SECURITY_HASH.txt")
    try:
        req = urllib.request.Request(url,
                                     headers={"User-Agent": "E-Lang/Verify/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode()
    except Exception as e:
        return False, f"github unreachable: {e}"
    remote_bundle = None
    for line in text.splitlines():
        if line.startswith("AGGREGATE="):
            remote_bundle = line.split("=", 1)[1]
    if not remote_bundle:
        return False, "github copy has no aggregate"
    y_remote = y_key(remote_bundle, tag)
    if y_remote != y_local:
        return False, "Y mismatch: version key differs from GitHub"
    return True, f"Y verified (key matches GitHub @ {tag})"
