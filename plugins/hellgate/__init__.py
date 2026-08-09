"""HELLFORGE Hellgate — launch OpenCode / Aider / OpenHands / Goose as the
proper agent TUIs for this project, focused inside the HELLFORGE root.

run.py hellgate          → interactive picker (choose a tool, then $ commands)
run.py hellgate opencode → launch a tool directly by name

The session REPL supports:
  $change            switch to another tool
  $new               start a fresh chat in the current tool
  $dir [path]        add/change the project directory (default: project root)
  $agent [name]      Music-Composer | Music-Refiner | default
  $help              list commands
  quit / exit        leave the session
"""

import os
import sys
import shlex

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

HELLGATE_DIR = os.path.dirname(os.path.abspath(__file__))


def _cmd(args, api):
    """run.py hellgate entry."""
    if args and args[0] in ("--help", "-h"):
        print(__doc__)
        return 0
    from . import session as sess
    tool = args[0] if args else None
    return sess.run(api, tool)


def _agent_names():
    try:
        from . import knowledge as k
        return k.agent_names()
    except Exception:
        return ["Music-Composer", "Music-Refiner"]
