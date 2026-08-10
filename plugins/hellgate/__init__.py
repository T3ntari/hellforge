"""HELLFORGE HellGate — a wrapper that boots and launches OpenCode directly,
focused inside the HELLFORGE root.

run.py hellgate

Flow per launch:
  wrapper warning (every time)
  -> first-run onboarding on a new machine (specs-based, even with history)
  -> provider/model resolution (ollama asks for a model via a select list)
  -> HellCode welcome page + loading screen (real init, x/1024)
  -> OpenCode TUI, directly

After OpenCode exits: Enter relaunches, $provider / $model / $agent / $dir
manage the session, q quits. HellGate is just a wrapper - not an official
product of OpenCode.
"""

import os
import sys

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

HELLGATE_VERSION = "0.1.14.55"

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))


def _cmd(args, api):
    """run.py hellgate entry."""
    if args and args[0] in ("--help", "-h"):
        print(__doc__)
        return 0
    from . import session as sess
    return sess.run(api)


def _agent_names():
    try:
        from . import knowledge as k
        return k.agent_names()
    except Exception:
        return ["Music-Composer", "Music-Refiner"]
