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


def _x_store_root():
    """Deep, obscure, gitignored store root for the hidden fragments."""
    root = PROJECT_DIR / ".e_identity" / ".integrity" / ".store"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _order_root():
    root = PROJECT_DIR / ".e_identity" / ".integrity" / ".order"
    root.mkdir(parents=True, exist_ok=True)
    return root


_ORDER_MARKER = "# hellforge-order-v2"
_FRAG_STYLES = (
    "# {hex}",
    "data: {hex}",
    "{hex}  # cache",
    "token={hex}",
    "[{hex}]",
    "#~ {hex}",
)


def _tiny_chunks(text, per_line):
    """Split into VERY small chunks, each fitting on one line."""
    out = []
    i = 0
    while i < len(text):
        size = random.randint(per_line // 2, per_line)
        out.append(text[i:i + size])
        i += size
    return out


def _random_fname():
    return random.choice((
        "blob_%s.cache" % os.urandom(2).hex(),
        "tmp_%s.dat" % os.urandom(2).hex(),
        "key.snap", "state_%s.json" % os.urandom(2).hex(),
        ".trace_%s" % os.urandom(2).hex(),
        "part_%s.bin" % os.urandom(2).hex(),
    ))


IDENTITY_FILES = (".e_identity/secret.key", ".e_identity/identity.json",
                  ".e_identity/.device_id")


def identity_digest():
    """SHA-256 over the local identity files (secret.key, identity.json,
    .device_id). 'none' when no identity exists yet. Tampering with any of
    them is detected at the next init (carried inside the X store)."""
    parts = []
    for rel in IDENTITY_FILES:
        p = PROJECT_DIR / rel
        if p.is_file():
            try:
                parts.append(rel + ":" + p.read_bytes().hex())
            except Exception:
                pass
    if not parts:
        return "none"
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def reembed():
    """Re-hide X with the CURRENT bundle + identity digest — call after
    legitimate identity changes (create identity, rotate device id)."""
    _tag, key = load_version_key()
    x_embed(digest_bundle(compute_manifest()), key or "")


def x_embed(bundle, y=None):
    """Hide X (the digest) and Y (the version key) as very small 1-2 line
    fragments, each in its own random-named file, inside a freshly created
    random deep directory. The ORDER (file -> position) is saved in another
    random directory. All previous layouts are purged first, so exactly one
    order file ever exists. Returns the order file path."""
    import uuid
    import shutil as _sh
    for root in (_x_store_root(), _order_root()):
        if root.is_dir():
            for old in list(root.iterdir()):
                _sh.rmtree(old, ignore_errors=True)
    store = _x_store_root() / uuid.uuid4().hex[:8]
    inner = store / uuid.uuid4().hex[:6]
    inner.mkdir(parents=True, exist_ok=True)

    x_chunks = _tiny_chunks(bundle, 14)
    y_chunks = _tiny_chunks(y or "", 12)
    entries = {}  # filename -> (kind, pos, hex)
    for pos, chunk in enumerate(x_chunks):
        fn = _random_fname()
        while fn in entries:
            fn = _random_fname()
        (inner / fn).write_text(random.choice(_FRAG_STYLES).format(hex=chunk) + "\n")
        entries[fn] = ("x", pos, chunk)
    for pos, chunk in enumerate(y_chunks):
        fn = _random_fname()
        while fn in entries:
            fn = _random_fname()
        (inner / fn).write_text(random.choice(_FRAG_STYLES).format(hex=chunk) + "\n")
        entries[fn] = ("y", pos, chunk)

    # identity digest — an extra store entry kind 'i'
    ident_fn = _random_fname()
    while ident_fn in entries:
        ident_fn = _random_fname()
    ident = identity_digest()
    (inner / ident_fn).write_text("id: " + ident + "\n")
    entries[ident_fn] = ("i", 0, ident)

    order_dir = _order_root() / uuid.uuid4().hex[:8]
    order_dir.mkdir(parents=True, exist_ok=True)
    order_path = order_dir / "order.ord"
    lines = [_ORDER_MARKER]
    lines.append("store=" + str(inner.relative_to(PROJECT_DIR)))
    for fn, (kind, pos, _c) in sorted(entries.items(), key=lambda kv: (kv[1][0], kv[1][1])):
        lines.append(f"{kind}:{pos}={fn}")
    order_path.write_text("\n".join(lines) + "\n")
    return order_path


def _find_order_file():
    """Detect the order file by scanning the random order directories."""
    root = _order_root()
    if not root.is_dir():
        return None
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        for f in sorted(d.iterdir()):
            try:
                head = f.read_text().splitlines()[:1]
            except Exception:
                continue
            if head and head[0].strip() == _ORDER_MARKER:
                return f
    return None


def _x_extract():
    """Reconstruct (bundle, y) from the hidden fragments using the order
    file. Returns (bundle, y, order_file) or (None, None, None)."""
    order_file = _find_order_file()
    if order_file is None:
        return None, None, None
    try:
        lines = order_file.read_text().splitlines()
        store_rel = None
        entries = []
        for ln in lines[1:]:
            if ln.startswith("store="):
                store_rel = ln.split("=", 1)[1]
            elif "=" in ln and ":" in ln:
                kind_pos, fn = ln.rsplit("=", 1)
                kind, pos = kind_pos.split(":", 1)
                entries.append((kind, int(pos), fn))
        if store_rel is None or not entries:
            return None, None, None
        store = (PROJECT_DIR / store_rel)
        by_kind = {"x": {}, "y": {}, "i": {}}
        for kind, pos, fn in entries:
            p = store / fn
            if not p.is_file():
                return None, None, None
            txt = p.read_text(errors="replace")
            import re as _re
            for line in txt.splitlines():
                line = line.strip()
                if kind == "i":
                    m = _re.fullmatch(r"id: ([0-9a-f]+)", line)
                    if m:
                        by_kind[kind][pos] = m.group(1)
                    continue
                for style in _FRAG_STYLES:
                    tpl = style.format(hex="{HEX}")
                    pat = _re.escape(tpl).replace(_re.escape("{HEX}"),
                                                  "([0-9a-f.]+)")
                    m = _re.fullmatch(pat, line)
                    if m:
                        by_kind[kind][pos] = m.group(1)
                        break
        if not by_kind["x"]:
            return None, None, None
        bundle = "".join(by_kind["x"][i] for i in sorted(by_kind["x"]))
        y = "".join(by_kind["y"][i] for i in sorted(by_kind["y"])) if by_kind["y"] else ""
        ident = "".join(by_kind["i"][i] for i in sorted(by_kind["i"])) if by_kind["i"] else None
        return bundle, y, ident, order_file
    except Exception:
        return None, None, None


def x_verify():
    """Technique X + Y check: reconstruct the hidden fragments, compare X
    with the current core digest and Y with the committed version key.
    The order file is DELETED immediately after use, and a fresh random
    layout is embedded for the next init. On failure the store is kept as
    evidence. Returns (ok, detail)."""
    bundle, y, ident, order_file = _x_extract()
    if bundle is None:
        # nothing hidden yet -> first-run embed from the current state
        cur = digest_bundle(compute_manifest())
        _tag, key = load_version_key()
        x_embed(cur, key or "")
        return True, "X embedded (first run)"
    current = digest_bundle(compute_manifest())
    if bundle != current:
        return False, ("X fragment digest does not match the current core "
                       "structure — a covered file was altered")
    cur_ident = identity_digest()
    if ident is not None and ident != cur_ident:
        return False, ("identity files altered — secret.key / identity.json / "
                       ".device_id changed since the last verification")
    tag, committed_y = load_version_key()
    if committed_y:
        if y != committed_y:
            return False, "Y fragment does not match the committed version key"
    # use done -> delete the order file (and its dir) immediately
    used_store = None
    try:
        order_file.unlink()
        d = order_file.parent
        if d.is_dir() and not list(d.iterdir()):
            d.rmdir()
    except Exception:
        pass
    # fresh random layout for the next init
    new_order = x_embed(current, committed_y or y or "")
    # prune old embed dirs (the used store + any stale ones)
    try:
        store = _x_store_root()
        used = set()
        if new_order is not None:
            ol = new_order.read_text().splitlines()
            for ln in ol:
                if ln.startswith("store="):
                    used.add((PROJECT_DIR / ln.split("=", 1)[1]).parent)
        for d2 in list(store.iterdir()):
            if d2.is_dir() and d2 not in used:
                import shutil as _sh
                _sh.rmtree(d2, ignore_errors=True)
        order_root = _order_root()
        keep = {new_order.parent} if new_order is not None else set()
        for d2 in list(order_root.iterdir()):
            if d2.is_dir() and d2 not in keep:
                import shutil as _sh
                _sh.rmtree(d2, ignore_errors=True)
    except Exception:
        pass
    return True, "X + Y verified (hidden fragments match core and version key)"


def x_rotate():
    """Re-hide with a fresh random layout (called every init)."""
    return x_verify()[0]


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
    import subprocess as _sp
    import urllib.request
    tag, y_local = load_version_key()
    if not y_local:
        return False, "no committed version key"
    # resolve the tag to its peeled commit SHA (annotated tags need ^{})
    commit_sha = ""
    try:
        r = _sp.run(["git", "ls-remote", "origin",
                     f"refs/tags/{tag}^{{}}"],
                    capture_output=True, text=True, timeout=timeout)
        if r.returncode == 0 and r.stdout.strip():
            commit_sha = r.stdout.split("\t")[0]
    except Exception:
        pass
    if not commit_sha:
        return False, f"cannot resolve tag {tag} on GitHub"
    url = (f"https://raw.githubusercontent.com/T3ntari/hellforge/"
           f"{commit_sha}/SECURITY_HASH.txt")
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
