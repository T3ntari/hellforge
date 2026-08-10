# Integrity Commands — X/Y Digests, SAFE MODE, Safe Updates

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [krip-commands](krip-commands.md) | [integrity-commands](integrity-commands.md) | [security](../security/trust-model.md)

Every CLI start / initialization recomputes the core digest and compares it
against the committed manifest — and optionally the live GitHub copy.

## run.py integrity

```bash
run.py integrity              # local check
run.py integrity --github     # also compare against the live GitHub copy
```

Output: `[security] core integrity OK` (or `CORE INTEGRITY FLAGGED` with the
reason), the 160-byte aggregate digest, the committed expectation, and —
with `--github` — `github : MATCH|MISMATCH` against
`SECURITY_HASH.txt` at the repo's `main` branch.

### What it verifies

- **`SECURITY_HASH.txt`** (committed): one `rel:sha512` line per covered
  file (~56 core files: `ep_core.py`, `eshell.py`, `ep_pkg.py`,
  `pkglist.json`, all `ep_compiler/*.py`, all `plugins/*/__init__.py`),
  plus a 160-byte **triple aggregate** — SHA-256 + SHA-512 + BLAKE2b-512
  over the sorted manifest (`AGGREGATE=sha256.sha512.blake2b512`).
- **Technique X** — the offline proof. The 160-byte aggregate (and the
  version key) is split into tiny 1–2 line fragments, hidden inside random
  files in a deep gitignored store (`.e_identity/.integrity/.store/`), in
  random order/chunk sizes/filename styles. The order file lives in
  `.e_identity/.integrity/.order/`, is **deleted immediately after use**,
  and a fresh random layout is embedded on every init. Any tampering of a
  covered file — or of the X store itself — fails the reconstruction.
- **Technique Y** — the per-version key. `blake2b512(aggregate + ":" +
  version tag)` committed in `ep_compiler/_version_key.py` at release
  time. Online, it is verified against the live `SECURITY_HASH.txt` at
  the **version tag** on GitHub (resolved to its peeled commit SHA).

### Boot order

1. **X first** (local, offline) — fail → SAFE MODE.
2. Network probe — offline → X alone is the proof; the layout rotates.
3. Online → **Y + version check** against GitHub; a newer version is
   offered with a safe update.

### Regeneration (for core developers)

```bash
python3 tools/gen_security_hash.py
```

Writes `SECURITY_HASH.txt` + `ep_compiler/_version_key.py` + the X store.
Commit them together with your changes (see
[Contributing](../contributing.md)). `_version_key.py` is itself excluded
from hashed coverage (self-reference) — tampering is caught by Technique Y
online. Custom plugin dirs are covered by `SECURITY_HASH.local`, generated
by the updater.

## SAFE MODE

Entered when an integrity check fails (manual kernel selection, X failure,
or Y failure). Plugins are isolated; only a restricted shell runs:

- `status` — what failed: core digest vs committed, Technique X state,
  version key presence
- `reinstall` — re-install the current version from GitHub with a progress
  bar; configs, plugins, mods and identity are preserved
  (".installation successful, exiting safe mode")
- `/safemode exit force` — leave anyway, after an explicit risk warning
- `quit` — stay in safe mode (default, safe)

## Safe updates

Version of record = the GitHub version tag. `u` in the K-rip boot menu (or
the post-boot prompt, or booting a **previous kernel** from the registry)
runs the safe update:

1. **Backup**: `.plugin_config.json`, `.env`, `.e_identity/`, `mods/`,
   `SECURITY_HASH.local`, and any custom plugin dirs → `.backup_update/`
2. **Kernel registry snapshot** — the current kernel becomes a bootable
   previous entry (rollback target)
3. `git fetch origin tag <tag>` → stash uncommitted work → checkout
4. **Restore** user data; **register custom plugins** in
   `SECURITY_HASH.local`
5. Stash popped, fresh X/Y layout embedded, integrity re-checked

Nothing is lost; the previous kernel stays bootable from the menu.

---

See also: [Security trust model](../security/trust-model.md) · [Plugin integrity verification](../packaging/pkglist.md)
