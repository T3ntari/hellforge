"""Compile and play all Portbaby-converted versions natively through eshell."""
import sys
import os
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("E_CONVERSION_DIR") or os.path.join(SCRIPT_DIR, "conversion_test")
ESHELL = os.path.join(SCRIPT_DIR, "eshell.py")

files = [
    ("Original .eic", "GNG_Nocturne_v1_machine.e"),
    ("v1 Human", "GNG_Nocturne_v1_human.e"),
    ("v1 Machine", "GNG_Nocturne_v1_machine.e"),
    ("v2 Semantic", "GNG_Nocturne_v2.e"),
    ("v3 Shorthand", "GNG_Nocturne_v3.e"),
    ("v4 Machine+Sections", "GNG_Nocturne_v4.e"),
    ("v4 Human @time:", "GNG_Nocturne_v4_human.e"),
]

for label, filename in files:
    path = os.path.join(DIR, filename)
    if not os.path.exists(path):
        print(f"  Skipping {filename}")
        continue
    print(f"\n{'='*60}")
    print(f"  {label} — {filename}")
    print(f"{'='*60}")
    
    # Compile .e -> .mid, then play
    mid = os.path.join(DIR, f"play_{filename.replace('.e','.mid')}")
    r = subprocess.run([sys.executable, ESHELL, "-c", f"compile \"{path}\" -o \"{mid}\" && play \"{mid}\""],
                      capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
    if r.returncode != 0:
        print(f"  Error: {r.stderr[:200]}")
    else:
        for line in r.stdout.split("\n"):
            if line.strip():
                print(f"  {line.strip()}")
