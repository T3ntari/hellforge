"""Play all converted versions of GNG_Nocturne sequentially for comparison."""
import sys
import os
import subprocess
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIR = os.environ.get("E_CONVERSION_DIR") or os.path.join(SCRIPT_DIR, "conversion_test")
PLAYER = os.path.join(SCRIPT_DIR, "player.py")

versions = [
    ("Original MIDI", "GNG_Nocturne.mid"),
    ("v1_human", "GNG_v1_human.mid"),
    ("v1_machine", "GNG_v1_machine.mid"),
    ("v2 (chord compressed)", "GNG_v2.mid"),
    ("v3 (shorthand)", "GNG_v3.mid"),
    ("v4 (machine + sections)", "GNG_v4.mid"),
    ("v4_human (@time:)", "GNG_v4_human.mid"),
]

for label, filename in versions:
    path = os.path.join(DIR, filename)
    if not os.path.exists(path):
        print(f"  Skipping {filename} (not found)")
        continue
    print(f"\n{'='*60}")
    print(f"  Now playing: {label} — {filename}")
    print(f"{'='*60}")
    sys.stdout.flush()
    r = subprocess.run([sys.executable, PLAYER, path], timeout=300)
    if r.returncode != 0:
        print(f"  Error playing {filename}")
    time.sleep(1)  # pause between tracks

print(f"\nAll versions played.")
