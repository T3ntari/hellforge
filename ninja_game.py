#!/usr/bin/env python3
"""ninja_game.py — launch the Ninja game directly.

No boot manager, no console, no menu: just the game. Opens a window
(pygame/SDL — the same stack as the built-in player) on any machine with
a display; falls back to a terminal session when headless.

Run:
    .venv/bin/python ninja_game.py
or make it executable and run it straight from the repo root.

Keys: W/S forward/back, A/D strafe, Q/E turn, Shift run,
      M menu (FSR 3.1 / TAA / accumulation / weather), Q or close = quit.
"""

import os
import sys

os.environ["KRIP_INNER"] = "1"
os.environ["KRIP_BYPASS"] = "1"
os.environ.pop("KRIP_BOOT_CMD", None)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from plugins.ninja._game import NinjaGame


def main():
    try:
        game = NinjaGame()
    except Exception as e:
        print(f"  Ninja: failed to start ({e})")
        return 1
    print("  Ninja — corridor walker (FSR 3.1, rain on)")
    try:
        game.play()
    except KeyboardInterrupt:
        print("\n  bye")
    return 0


if __name__ == "__main__":
    sys.exit(main())
