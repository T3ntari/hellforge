#!/usr/bin/env python3
"""Regenerate SECURITY_HASH.txt after intentional core changes.

    python3 tools/gen_security_hash.py

Writes the per-file SHA-512 manifest + the aggregate triple-digest
(SHA-256 + SHA-512 + BLAKE2b-512 = 160 bytes) to SECURITY_HASH.txt.
Commit that file together with your changes.
"""

import sys
import os

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT)

from ep_compiler.security_hash import (
    MANIFEST_PATH,
    DIGEST_NAMES,
    aggregate,
    compute_manifest,
    digest_bundle,
)


def main():
    manifest = compute_manifest()
    agg = aggregate(manifest)
    lines = [f"{rel}:{h}" for rel, h in sorted(manifest.items())]
    out = []
    out.append("# HELLFORGE core integrity manifest — regenerate with")
    out.append("#   python3 tools/gen_security_hash.py")
    out.append("# Every CLI start compares the local computation against this file;")
    out.append("# the live copy lives at")
    out.append("#   https://raw.githubusercontent.com/T3ntari/hellforge/main/SECURITY_HASH.txt")
    out.append("")
    out.extend(lines)
    out.append("")
    for n in DIGEST_NAMES:
        out.append(f"{n.upper()}={agg[n]}")
    out.append(f"AGGREGATE={digest_bundle(manifest)}")
    MANIFEST_PATH.write_text("\n".join(out) + "\n")
    print(f"  wrote {MANIFEST_PATH}")
    print(f"  covered files: {len(manifest)}")
    print(f"  aggregate     : {digest_bundle(manifest)[:40]}...")


if __name__ == "__main__":
    main()
