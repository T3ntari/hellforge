**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [overview](overview.md) | [regas-trust](regas-trust.md) | [tentari-signing](tentari-signing.md) | [key-management](key-management.md) | [verification](verification.md)

## REGAS Trust

**REGAS** is an author trust tag in HELLFORGE plugin metadata (e.g.
`Made by Tentari. Signed: REGAS.`) — a legacy marker from the CORE-EXPANSION
era of the project.

### Current status

- REGAS is **not** a server-confirmed trust level anymore. The private
  registry submission flow (`/verify`, `/confirm`, `--submit-regas`) was
  removed from the open-source release; registry auth is not part of the
  project.
- Plugins may still carry the REGAS tag as an authorship/quality
  indication; it implies **no** automatic trust privileges.
- Verification is purely local: plugin hashes against `pkglist.json`
  codes (see [pkglist](../packaging/pkglist.md)) and file signatures
  against `.e_identity/trusted/` keys (see [Verification](verification.md)).

### History

Originally REGAS meant "registry-confirmed identity — highest trust",
granting eligibility for `sys strict 2` without warnings. That mechanism
no longer exists; all official HELLFORGE packages now ship with SHA-256
verification codes in `pkglist.json`, verified locally by
`tools/verify_integrity.py`.