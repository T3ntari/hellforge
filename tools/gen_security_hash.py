#!/usr/bin/env python3
"""Regenerate SECURITY_HASH.txt after intentional core changes.

    python3 tools/gen_security_hash.py

Writes:
  - SECURITY_HASH.txt      per-file SHA-512 manifest + aggregate triple-digest
  - ep_compiler/_version_key.py   Technique Y: this version's permanent key
  - ep_compiler/_x_hide.py        Technique X: rotating hidden fragments

Commit SECURITY_HASH.txt + _version_key.py together with your changes.
"""

import sys
import os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from ep_compiler.security_hash import (
    MANIFEST_PATH,
    DIGEST_NAMES,
    VERSION_KEY_FILE,
    X_FILE,
    aggregate,
    compute_manifest,
    digest_bundle,
    x_embed,
    y_key,
)


def main():
    import subprocess as _sp

    # The version tag must be written BEFORE the manifest is computed:
    # _version_key.py is a covered file, so its content is part of the digest.
    try:
        tag = _sp.run(["git", "describe", "--tags", "--abbrev=0"],
                      capture_output=True, text=True, timeout=5,
                      cwd=str(PROJECT)).stdout.strip() or "dev"
    except Exception:
        tag = "dev"

    # _version_key.py is NOT part of the hashed coverage (self-reference);
    # its tampering is caught by technique Y against GitHub when online.
    manifest = compute_manifest()
    bundle = digest_bundle(manifest)
    agg = aggregate(manifest)
    key = y_key(bundle, tag)

    VERSION_KEY_FILE.write_text(
        "# Technique Y — the permanent per-version key hash (from the committed\n"
        "# manifest, verified against GitHub). Generated. Do not edit.\n"
        f"VERSION_TAG = \"{tag}\"\n"
        f"VERSION_KEY = \"{key}\"\n")

    lines = [f"{rel}:{h}" for rel, h in sorted(manifest.items())]
    out = [
        "# HELLFORGE core integrity manifest — regenerate with",
        "#   python3 tools/gen_security_hash.py",
        "# Every CLI start compares the local computation against this file;",
        "# the live copy lives at",
        "#   https://raw.githubusercontent.com/T3ntari/hellforge/main/SECURITY_HASH.txt",
        "",
    ]
    out.extend(lines)
    out.append("")
    for n in DIGEST_NAMES:
        out.append(f"{n.upper()}={agg[n]}")
    out.append(f"AGGREGATE={bundle}")
    MANIFEST_PATH.write_text("\n".join(out) + "\n")

    # Technique X — hide the digest in random fragments in the core.
    x_embed(bundle)

    print(f"  wrote {MANIFEST_PATH}")
    print(f"  version key : {tag} = {y_key(bundle, tag)[:24]}...")
    print(f"  covered files: {len(manifest)}")
    print(f"  aggregate     : {bundle[:40]}...")
    print(f"  hidden X      : {X_FILE}")


if __name__ == "__main__":
    main()
