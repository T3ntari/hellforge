"""Hellgate tools layer — one module per tool lives here.

Contract (implemented by tools/opencode.py, tools/aider.py,
tools/openhands.py, tools/goose.py):

    TOOL = {
        "id": "opencode",               # unique id
        "name": "OpenCode",
        "license": "MIT",
        "install_cmd": str | None,      # one-line shell install hint
        "confined": bool,               # can run fully inside project root
        "notes": str | None,            # picker note (docker needed etc.)
    }

    def detect() -> bool:
        Return True when the tool is installed / launchable.

    def launch(project_dir: str, agent: str | None, knowledge_dir: str,
               extra_args: list[str], stream_out=print) -> int:
        Launch the tool focused inside project_dir; must not read/write
        outside project_dir. Return the tool exit code.

Every module imports nothing outside the stdlib and hellgate.util.
discover() returns the four TOOL dicts merged with live detect() status.
"""

import importlib

TOOL_IDS = ("opencode", "aider", "openhands", "goose")


def discover():
    tools = []
    for tid in TOOL_IDS:
        try:
            mod = importlib.import_module(f"plugins.hellgate.tools.{tid}")
        except Exception as e:  # a broken tool module must not kill the picker
            tools.append({
                "id": tid, "name": tid, "license": "?", "install_cmd": None,
                "confined": False, "notes": f"module error: {e}",
                "installed": False, "launch": None,
            })
            continue
        d = dict(mod.TOOL)
        d["installed"] = bool(mod.detect())
        d["launch"] = mod.launch
        d["_mod"] = mod
        tools.append(d)
    return tools


def by_id(tid):
    for t in discover():
        if t["id"] == tid:
            return t
    return None
