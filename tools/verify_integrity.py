#!/usr/bin/env python3
"""HELLFORGE integrity check — prove every installed plugin's integrity.

    python3 tools/verify_integrity.py [--remote]

Local mode (default): hashes every plugin and compares against the codes
published in pkglist.json — works for anyone, no secrets involved.

--remote: additionally pulls codes from the PRIVATE registry configured in
the environment (HF_VERIFY_URL + HF_VERIFY_TOKEN). Nothing is hardcoded;
unset variables mean local-only. Exit code 0 = all verified, 1 = any
mismatch or missing code.
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

from ep_compiler.plugin_security import (
    compute_plugin_hash,
    load_pkglist_verifications,
    refresh_verification_cache,
    verify_plugin_integrity,
)


def main():
    remote = "--remote" in sys.argv
    if remote:
        codes = refresh_verification_cache(force=True)
        src = "private registry (HF_VERIFY_URL)" if os.environ.get("HF_VERIFY_URL") \
            else "local pkglist (no HF_VERIFY_URL set)"
    else:
        codes = load_pkglist_verifications()
        src = "local pkglist.json"
    if not codes:
        print("  no verification codes available — nothing to check")
        return 1
    print(f"  integrity check — codes from {src}")
    print(f"  {'plugin':<14} {'status':<10} detail")
    bad = 0
    for name in sorted(codes):
        valid, exp, act, detail = verify_plugin_integrity(name)
        mark = "OK" if valid else "FAIL"
        if not valid:
            bad += 1
        print(f"  {name:<14} {mark:<10} {detail}")
    if remote and not os.environ.get("HF_VERIFY_URL"):
        print("  (--remote requested but HF_VERIFY_URL is not set — used local codes)")
    print(f"\n  {'ALL PLUGINS VERIFIED' if bad == 0 else str(bad) + ' FAILED'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
