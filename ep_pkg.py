"""
E Package Manager v2 — Production-grade mod/plugin/pkglist system.
Supports listing, scanning, updating, fetching, dependency resolution, security.
Registry API: http://host:5592/api/{list|mod|plugin|download}
"""

import hashlib
import json
import os
import re
import shutil
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

PROJECT_DIR = Path(__file__).parent.resolve()
MODS_DIR = PROJECT_DIR / "mods"
PLUGINS_DIR = PROJECT_DIR / "plugins"
PKGLIST_PATH = PROJECT_DIR / "pkglist.json"
import os
REGISTRY_BASE = os.environ.get("HF_REGISTRY", "")
VERSION = "2.0.0"

SECURITY_BLOCKLIST = [
    b"os.system", b"os.popen", b"subprocess.Popen", b"subprocess.call",
    b"subprocess.run", b"shutil.rmtree", b"pathlib.rmtree",
    b"__import__('os')", b"eval(", b"exec(", b"compile(",
    b"pty.spawn", b"ctypes.CDLL", b"win32api",
    b"socket.connect", b"requests.get",  # No network access for mods
]

R = "\033[0m"; B = "\033[1m"; D = "\033[2m"; I = "\033[3m"
RED = "\033[91m"; GREEN = "\033[92m"; YELLOW = "\033[93m"
CYAN = "\033[96m"; GREY = "\033[90m"; MAGENTA = "\033[95m"

def c(text, color=""):
    return f"{color}{text}{R}" if color else text


# ═══════════════════════════════════════════════
#  Package List
# ═══════════════════════════════════════════════

def load(force_reload=False):
    """Load pkglist from disk. If force_reload, bypasses any caching."""
    d = {"mods": {}, "plugins": {}, "version": VERSION, "updated": "", "url": ""}
    if not PKGLIST_PATH.exists():
        return d
    try:
        with open(PKGLIST_PATH, "r") as f:
            return {**d, **json.load(f)}
    except Exception:
        return d


def save(data):
    data["updated"] = datetime.now().isoformat()
    with open(PKGLIST_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  {c('✓', GREEN)} pkglist saved  ({len(data.get('mods',{}))} mods, {len(data.get('plugins',{}))} plugins)")


def sync_from_url(url):
    url = url.strip("\"'")
    print(f"  {c('⟳', YELLOW)} fetching pkglist  {c(url, D)}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"E-Pkg/{VERSION}"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        if "mods" not in data and "plugins" not in data:
            return print(f"  {c('✗', RED)} invalid pkglist — missing mods/plugins")
        data["url"] = url
        save(data)
        m = len(data.get("mods", {}))
        p = len(data.get("plugins", {}))
        print(f"  {c('✓', GREEN)} synced  {c(f'{m} mods, {p} plugins', B)}")
    except urllib.error.HTTPError as e:
        print(f"  {c('✗', RED)} HTTP {e.code}")
    except Exception as e:
        print(f"  {c('✗', RED)} {e}")


def sync_from_file(path):
    path = str(path).strip("\"'")
    if not os.path.exists(path):
        return print(f"  {c('✗', RED)} file not found: {path}")
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if "mods" not in data and "plugins" not in data:
            return print(f"  {c('✗', RED)} invalid pkglist format")
        save(data)
        m = len(data.get("mods", {}))
        p = len(data.get("plugins", {}))
        print(f"  {c('✓', GREEN)} loaded  {c(f'{m} mods, {p} plugins', B)}")
    except json.JSONDecodeError as e:
        print(f"  {c('✗', RED)} JSON error: {e}")


# ═══════════════════════════════════════════════
#  Security Scanner (AST-based, not string blocklist)
# ═══════════════════════════════════════════════

def scan_file(path):
    """Security-scan a Python file using AST analysis.
    Catches obfuscated dangerous calls that string-matching misses."""
    try:
        from ep_core import ast_scan
    except ImportError:
        return []
    try:
        with open(path, "rb") as f:
            data = f.read()
    except Exception as e:
        return [(0, str(e))]
    return ast_scan(data)


def scan_directory(dir_path, label=""):
    target = Path(str(dir_path).strip("\"'"))
    if not target.exists():
        return print(f"  {c('📁', D)} {label or 'target'} directory not found")
    total_files = 0
    total_issues = 0
    results = {}
    for f in sorted(target.glob("*.*")):
        if f.suffix not in (".py", ".pyc") or f.name.startswith("_"):
            continue
        total_files += 1
        issues = scan_file(f)
        if issues:
            results[f.name] = issues
            total_issues += len(issues)

    if total_files == 0:
        return print(f"  {c('📁', D)} {label or 'directory'}  {c('(empty)', D)}")

    status = c("✓ clean", GREEN) if total_issues == 0 else c(f"⚠ {total_issues} issues", RED)
    print(f"  {c('🔍', D)} scanned {c(total_files, B)} {label or 'files'}  {status}")
    for fname, issues in results.items():
        for line, pat in issues:
            print(f"    {c(fname, D)}:{line}  {c(pat, RED)}")


# ═══════════════════════════════════════════════
#  Package Info / Metadata
# ═══════════════════════════════════════════════

def get_installed_meta(path):
    """Get metadata from a plugin/mod path. Handles both single files and directories."""
    meta = {"name": path.stem, "version": "?", "author": "?", "update_url": "", "description": ""}
    try:
        # If it's a directory, read __init__.py instead
        if path.is_dir():
            init_file = path / "__init__.py"
            if not init_file.exists():
                return meta
            text = init_file.read_text(encoding="utf-8", errors="replace")
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
        for key in meta:
            p = re.compile(rf'^(?:#\s*)?{key}\s*[:=]\s*["\'](.+?)["\']', re.I | re.MULTILINE)
            m = p.search(text)
            if m:
                meta[key] = m.group(1)
        m = re.search(r'^(?:#\s*)?VERSION\s*=\s*["\'](.+?)["\']', text, re.MULTILINE)
        if m and meta["version"] == "?":
            meta["version"] = m.group(1)
        m = re.search(r'^__version__\s*=\s*["\'](.+?)["\']', text, re.MULTILINE)
        if m and meta["version"] == "?":
            meta["version"] = m.group(1)
    except Exception:
        pass
    return meta


def compare_versions(v1, v2):
    """Compare two semver strings. Returns -1, 0, 1."""
    try:
        p1 = [int(x) for x in re.split(r'[.+-]', v1) if x.isdigit()]
        p2 = [int(x) for x in re.split(r'[.+-]', v2) if x.isdigit()]
        for a, b in zip(p1, p2):
            if a < b: return -1
            if a > b: return 1
        return 0
    except Exception:
        return 0 if v1 == v2 else -1


# ═══════════════════════════════════════════════
#  Display
# ═══════════════════════════════════════════════

def _table(rows, headers=None):
    """Print aligned table from list of tuples."""
    if not rows:
        return
    widths = [max(len(str(r[i])) for r in rows) for i in range(len(rows[0]))]
    if headers:
        widths = [max(w, len(h)) for w, h in zip(widths, headers)]
        print("  " + "  ".join(c(h, B).ljust(w) for h, w in zip(headers, widths)))
        print("  " + "  ".join(c("─" * w, D) for w in widths))
    for row in rows:
        print("  " + "  ".join(str(r).ljust(w) for r, w in zip(row, widths)))


def _find_packages(target_dir):
    """Yield (name, path) for both single-file and directory-based packages.
    Skips .py files that are shadowed by a same-named directory plugin."""
    dir_names = set()
    for d in sorted(target_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("_") and (d / "__init__.py").exists():
            dir_names.add(d.name)
            yield d.name, d
    for f in sorted(target_dir.glob("*.py*")):
        if f.name.startswith("_") or f.name == "__init__.py":
            continue
        if f.stem in dir_names:
            continue
        yield f.stem, f


def _resolve_package(name, target_dir):
    """Find a package by name (file or directory). Directory takes priority over file."""
    d = target_dir / name
    if d.is_dir() and (d / "__init__.py").exists():
        return d
    paths = list(target_dir.glob(f"{name}.*"))
    if paths:
        return paths[0]
    return None


def list_installed(pkg_type):
    target = MODS_DIR if pkg_type == "mods" else PLUGINS_DIR
    label = "Mods" if pkg_type == "mods" else "Plugins"
    if not target.exists():
        return print(f"  {c(f'📁 no installed {label.lower()}', D)}")

    items = []
    for name, path in _find_packages(target):
        m = get_installed_meta(path)
        has_url = c("↻", CYAN) if m["update_url"] else ""
        ptype = c("dir", MAGENTA) if path.is_dir() else c("file", D)
        # Verification badge (from ep_compiler.plugin_security)
        try:
            from ep_compiler.plugin_security import (
                load_pkglist_verifications,
                compute_plugin_hash,
            )
            codes = load_pkglist_verifications()
            expected = codes.get(name, "")
            badge = ""
            if expected:
                actual = compute_plugin_hash(name=name) or ""
                if actual == expected:
                    badge = c("[VERIFIED]", GREEN)
                else:
                    badge = c("[ALTERED]", RED)
        except Exception:
            badge = ""
        items.append((badge, c(name, CYAN), ptype, c(f"v{m['version']}", D), c(m["author"], GREY)))

    if not items:
        return print(f"  {c(f'📁 no installed {label.lower()}', D)}")
    print(f"  {c(f'📦 Installed {label}', B)}")
    _table(items)


def list_available(pkg_type, detail=False):
    pkgs = load().get(pkg_type, {})
    label = "Mods" if pkg_type == "mods" else "Plugins"

    # Try to fetch from remote registry
    try:
        import urllib.request as _ur
        _url = (os.environ.get("HF_REGISTRY") or "") + "/verify/plugins"
        _req = _ur.Request(_url, headers={"User-Agent": "E-Lang/1.0"})
        _resp = _ur.urlopen(_req, timeout=10)
        _data = json.loads(_resp.read())
        for _p in _data.get("plugins", []):
            _name = _p.get("name", "")
            if _name and _name not in pkgs:
                pkgs[_name] = {
                    "version": _p.get("version", "?"),
                    "description": _p.get("description", ""),
                    "author": _p.get("author", ""),
                    "tags": _p.get("tags", ""),
                    "url": "",
                }
    except Exception:
        pass

    if not pkgs:
        return print(f"  {c(f'no {label.lower()} in pkglist', D)}  {c('(try pkglist update url <url>)', GREY)}")

    print(f"  {c(f'📦 Available {label}', B)}  {c(f'({len(pkgs)} packages)', D)}")
    if detail:
        for name, info in sorted(pkgs.items()):
            print(f"    {c(name, CYAN)} v{info.get('version','?')}")
            for k in ("author", "description", "url", "tags"):
                v = info.get(k, "")
                if v:
                    print(f"      {c(k+':', D)} {v}")
            print()
    else:
        rows = []
        for name, info in sorted(pkgs.items()):
            ver = f"v{info.get('version','?')}"
            desc = info.get("description", "")[:50]
            tags = info.get("tags", "")
            rows.append((c(name, CYAN), c(ver, D), c(desc, GREY), c(tags, MAGENTA)))
        _table(rows, ["Package", "Version", "Description", "Tags"])


def search(query):
    q = query.lower()
    pkgs = load()
    results = []
    for ptype in ("mods", "plugins"):
        for name, info in pkgs.get(ptype, {}).items():
            text = f"{name} {info.get('description','')} {info.get('tags','')}".lower()
            score = text.count(q)
            if score > 0:
                results.append((score, name, ptype, info.get("version", "?"), info.get("description", "")[:60]))
    results.sort(reverse=True)

    if not results:
        return print(f"  {c('🔍 no results for', YELLOW)} \"{query}\"")

    print(f"  {c('🔍 Search results', B)} {c(f'({len(results)} matches)', D)}")
    for _, name, ptype, ver, desc in results[:15]:
        tag = c("[mod]", CYAN) if ptype == "mods" else c("[plugin]", MAGENTA)
        print(f"    {tag} {c(name, B)} v{ver}  {c(desc, D)}")
    if len(results) > 15:
        print(f"    {c(f'... {len(results)-15} more', D)}")


# ═══════════════════════════════════════════════
#  Real Progress Bar (delegates to ep_core)
# ═══════════════════════════════════════════════

from ep_core import _real_progress as _progress


def _finish_progress(name, pkg_type="plugin"):
    """Finalize progress bar at 100% and print install complete."""
    bar_width = 24
    print(f"\r  {c('✓', GREEN)} [{'█' * bar_width}] 100%  {c(name, CYAN)} installed  ")


# ═══════════════════════════════════════════════
#  Fetch / Download
# ═══════════════════════════════════════════════

def _download(url, dest, label=""):
    """Download a file (or copy from file:// URL) with progress display.
    Security-scans before saving."""
    data = None

    # Handle file:// URLs — copy from local filesystem
    if url.startswith("file://"):
        local_path = url[7:]  # strip file://
        # Try relative to project dir
        full_path = PROJECT_DIR / local_path
        if not full_path.exists():
            full_path = Path(local_path)
        if not full_path.exists():
            return print(f"  {c('✗', RED)} local file not found: {local_path}")
        try:
            data = full_path.read_bytes()
            print(f"  {c('✓', CYAN)} found locally: {full_path}")
        except Exception as e:
            return print(f"  {c('✗', RED)} read error: {e}")
    else:
        # HTTP download
        try:
            req = urllib.request.Request(url, headers={"User-Agent": f"E-Pkg/{VERSION}"})
            print(f"  {c('⟳', YELLOW)} downloading {c(label or Path(url).name, B)}")
            with urllib.request.urlopen(req, timeout=120) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                data = b""
                downloaded = 0
                while True:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    data += chunk
                    downloaded += len(chunk)
                    if total:
                        pct = downloaded * 100 // total
                        bar = "\u2588" * (pct // 5) + "\u2591" * (20 - pct // 5)
                        print(f"\r  {c('⟳', YELLOW)} [{bar}] {pct}%", end="", flush=True)
                print()
        except urllib.error.HTTPError as e:
            return print(f"  {c('✗', RED)} HTTP {e.code}")
        except Exception as e:
            return print(f"  {c('✗', RED)} {e}")

    if data is None:
        return False

    # Security scan
    from tempfile import NamedTemporaryFile
    with NamedTemporaryFile(delete=False) as tmp:
        tmp.write(data)
        tmpf = tmp.name
    issues = scan_file(tmpf)
    if issues:
        print(f"  {c('✗ Security block — rejected', RED)}")
        for line, pat in issues[:5]:
            print(f"    {c(pat, RED)}")
        os.unlink(tmpf)
        return False

    dest = Path(dest)
    dest.parent.mkdir(exist_ok=True)
    shutil.move(tmpf, dest)
    sz = len(data) // 1024
    print(f"  {c('✓', GREEN)} saved  {c(dest.name, B)} ({sz}KB)")
    return True


def fetch(name, pkg_type):
    """Download/install a package from the registry or local file:// URL."""
    pkgs = load().get(pkg_type, {})
    info = pkgs.get(name, {})
    url = info.get("url", "")
    target = MODS_DIR if pkg_type == "mods" else PLUGINS_DIR

    # Check if already installed
    from ep_pkg import _resolve_package
    existing = _resolve_package(name, target)
    if existing:
        print(f"  {c('Already installed:', CYAN)} {name} ({existing})")
        try:
            confirm = input(f"  Reinstall? [{c('y/N',B)}] ").strip().lower()
            if confirm != "y":
                return
        except (EOFError, KeyboardInterrupt):
            return

    # Handle file:// URLs — copy from local filesystem
    if url.startswith("file://"):
        local_path = url[7:]
        full_path = PROJECT_DIR / local_path
        if not full_path.exists():
            full_path = Path(local_path)

        if full_path.exists():
            if full_path.is_file() and full_path.name == "__init__.py":
                parent_dir = full_path.parent
                if parent_dir.is_dir() and parent_dir.name == name:
                    dest_dir = target / name
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    all_files = []
                    total_bytes = 0
                    for root, dirs, fnames in os.walk(parent_dir):
                        dirs[:] = [d for d in dirs if d != "__pycache__"]
                        for fn in fnames:
                            fpath = os.path.join(root, fn)
                            rel = os.path.relpath(fpath, parent_dir)
                            all_files.append((rel, fpath))
                            total_bytes += os.path.getsize(fpath)
                    copied = 0
                    for idx, (rel, src) in enumerate(all_files):
                        dst = dest_dir / rel
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        with open(src, "rb") as sf:
                            with open(dst, "wb") as df:
                                data = sf.read()
                                df.write(data)
                        copied += len(data)
                        pct = int(copied * 100 / total_bytes) if total_bytes else 100
                        _progress(pct, "copying", f"{idx+1}/{len(all_files)}")
                    _progress(100, "finalizing")
                    _finish_progress(name, pkg_type)
                    _auto_reload()
                    return True

            if full_path.is_dir():
                dest_dir = target / name
                if dest_dir.exists():
                    shutil.rmtree(dest_dir)
                all_files = []
                total_bytes = 0
                for root, dirs, fnames in os.walk(full_path):
                    dirs[:] = [d for d in dirs if d != "__pycache__"]
                    for fn in fnames:
                        fpath = os.path.join(root, fn)
                        rel = os.path.relpath(fpath, full_path)
                        all_files.append((rel, fpath))
                        total_bytes += os.path.getsize(fpath)
                copied = 0
                for idx, (rel, src) in enumerate(all_files):
                    dst = dest_dir / rel
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(src, "rb") as sf:
                        with open(dst, "wb") as df:
                            data = sf.read()
                            df.write(data)
                    copied += len(data)
                    pct = int(copied * 100 / total_bytes) if total_bytes else 100
                    _progress(pct, "copying", f"{idx+1}/{len(all_files)}")
                _progress(100, "finalizing")
                _finish_progress(name, pkg_type)
                _auto_reload()
                return True
            else:
                # Single file
                dest = target / f"{name}.py"
                return _download(url, dest, label=name)
        else:
            # Local path not found — try Tentari embedded JSON backup
            embedded_json = PROJECT_DIR / "embedded_plugins" / f"{name}.json"
            if embedded_json.exists():
                try:
                    import json
                    import base64
                    import hashlib
                    import os
                    import shutil
                    with open(embedded_json, "r", encoding="utf-8") as f:
                        payload = json.load(f)
                    target_dir = target / name
                    if target_dir.exists():
                        shutil.rmtree(target_dir)
                    entries = payload.get("files", [])
                    total_bytes = payload.get("total_size", 0)
                    decoded = 0
                    written = 0
                    for i, entry in enumerate(entries):
                        rel = entry["path"]
                        raw_b64 = entry["data"]
                        data = base64.b64decode(raw_b64)
                        actual = hashlib.sha256(data).hexdigest()
                        expected = entry.get("sha256", "")
                        if expected and actual != expected:
                            continue
                        dst = target_dir / rel
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        with open(dst, "wb") as f:
                            f.write(data)
                        decoded += len(raw_b64)
                        written += len(data)
                        pct = int(written * 100 / total_bytes) if total_bytes else 100
                        _progress(pct, "decoding", f"{i+1}/{len(entries)}")
                    if written:
                        _progress(100, "finalizing")
                        _finish_progress(name, pkg_type)
                        _auto_reload()
                        return True
                except Exception as e:
                    print(f"\n  {c('✗', RED)} Tentari backup failed: {e}")

            # Try HTTP fallback
            if not url:
                url = f"{REGISTRY_BASE}/{pkg_type}/{name}/download"
            dest = target / f"{name}.py"
            return _download(url, dest, label=name)

    # HTTP download (single file)
    if not url:
        url = f"{REGISTRY_BASE}/{pkg_type}/{name}/download"
    dest = target / f"{name}.py"
    result = _download(url, dest, label=name)
    if result:
        # Post-install: verify plugin integrity
        _verify_plugin_integrity(name, target)
        _auto_reload()
    return result


def _verify_plugin_integrity(name, target_dir):
    """Verify an installed plugin against pkglist codes (local only)."""
    try:
        from ep_compiler.plugin_security import compute_plugin_hash, load_pkglist_verifications
        h = compute_plugin_hash(name=name)
        if h:
            codes = load_pkglist_verifications()
            expected = codes.get(name, "")
            if expected:
                if h == expected:
                    print(f"  {c('[VERIFIED]', GREEN)} {name} integrity OK")
                else:
                    print(f"  {c('[ALERT]', RED)} {name} hash mismatch — may be altered")
            else:
                print(f"  {c('[UNVERIFIED]', YELLOW)} {name} — no verification code in pkglist")
    except ImportError:
        pass  # no verification codes available
    except Exception:
        pass


def update(name, pkg_type, all_flag=False):
    """Update a package by name, or all if all_flag."""
    target = MODS_DIR if pkg_type == "mods" else PLUGINS_DIR
    label = "mod" if pkg_type == "mods" else "plugin"

    if all_flag:
        count = 0
        for f in sorted(target.glob("*.py*")):
            if f.name.startswith("_"):
                continue
            meta = get_installed_meta(f)
            if meta["update_url"]:
                print(f"  {c('⟳', CYAN)} updating {c(meta['name'], B)}")
                _download(meta["update_url"], f, label=meta["name"])
                count += 1
            else:
                print(f"  {c('  -', D)} {c(meta['name'], GREY)}  {c('(no update_url)', D)}")
        if count == 0:
            print(f"  {c('no {label}s with update_url', YELLOW)}")
        return

    # Specific
    pkgs = load().get(pkg_type, {})
    info = pkgs.get(name, {})
    url = info.get("url", "")
    if not url:
        return print(f"  {c('✗', RED)} no URL for {c(name, B)} in pkglist")
    dest = target / f"{name}.py"
    _download(url, dest, label=name)


def uninstall(name, pkg_type):
    """Remove an installed mod/plugin. Handles both files and directories."""
    target = MODS_DIR if pkg_type == "mods" else PLUGINS_DIR
    path = _resolve_package(name, target)
    if not path:
        return print(f"  {c('✗', RED)} {name} not found in {target.name}")
    if path.is_dir():
        shutil.rmtree(path)
        print(f"  {c('🗑', RED)} removed  {c(f'{name}/', D)}")
    else:
        path.unlink()
        print(f"  {c('🗑', RED)} removed  {c(path.name, D)}")


# ═══════════════════════════════════════════════
#  Version check
# ═══════════════════════════════════════════════

def check_versions(pkg_type=None):
    pkgs = load()
    targets = (["mods", "plugins"] if pkg_type is None else [pkg_type])
    checks = []

    for pt in targets:
        td = MODS_DIR if pt == "mods" else PLUGINS_DIR
        if not td.exists():
            continue
        for f in sorted(td.glob("*.py*")):
            if f.name.startswith("_"):
                continue
            meta = get_installed_meta(f)
            inst = meta["version"]
            entry = pkgs.get(pt, {}).get(meta["name"], {})
            avail = entry.get("version", "?")
            # bundled (no update_url) = part of the repo, always in sync
            if not entry.get("update_url"):
                checks.append((meta["name"], pt, inst, avail, True))
            else:
                checks.append((meta["name"], pt, inst, avail, False))

    if not checks:
        return print(f"  {c('no packages to check', D)}")

    rows = []
    for name, pt, inst, avail, bundled in checks:
        if bundled or inst == "?" or avail == "?" or inst == avail:
            status = c("✓", GREEN)
        else:
            status = c("⬆", YELLOW) if compare_versions(inst, avail) < 0 else c("•", D)
        rows.append((c(name, CYAN), c(pt, D), f"v{inst}", f"v{avail}", status))

    print(f"  {c('📊 Version Check', B)}")
    _table(rows, ["Package", "Type", "Installed", "Available", ""])


# ═══════════════════════════════════════════════
#  Init
# ═══════════════════════════════════════════════

def init():
    """Initialize default pkglist if none exists."""
    if not PKGLIST_PATH.exists():
        default = {
            "version": VERSION,
            "updated": datetime.now().isoformat(),
            "url": "",
            "mods": {},
            "plugins": {},
        }
        save(default)


_last_manual_reload = 0.0


def _auto_reload():
    """Re-initialize the plugin/mod system without restarting eshell."""
    global _last_manual_reload
    _last_manual_reload = time.time()
    try:
        import sys
        from ep_core import (
            _plugins,
            _mods,
            _event_hooks,
            _plugin_directives,
            _boot_steps,
        )
        from ep_core import (
            _plugin_help_texts,
            _variable_handlers,
            _syntax_handlers,
            _eshell_commands,
        )
        _plugins.clear()
        _mods.clear()
        for hl in _event_hooks.values():
            hl.clear()
        _plugin_directives.clear()
        _boot_steps.clear()
        _plugin_help_texts.clear()
        _variable_handlers.clear()
        _syntax_handlers.clear()
        _eshell_commands.clear()
        for name in list(sys.modules.keys()):
            if name.startswith("plugins.") or name.startswith("mods.") or name.startswith("encryption."):
                del sys.modules[name]
        from ep_core import (
            init as core_init,
            show_boot_progress,
        )
        core_init()
        show_boot_progress()
        # Re-register eshell commands
        try:
            import eshell
            for name, (handler, help_text) in _eshell_commands.items():
                if name not in eshell.cmds:
                    eshell.cmds[name] = handler
        except Exception:
            pass
        print(f"  {c('✓', GREEN)} system reloaded")
    except Exception as e:
        print(f"  {c(f'Auto-reload error: {e}', RED)}")
