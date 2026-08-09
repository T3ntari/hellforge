"""HellGate tools - OpenCode only.

    TOOL = {"id": "opencode", "name": "OpenCode", "license": "MIT",
            "install_cmd": ..., "confined": True, "notes": ...}

    def detect() -> bool
    def launch(project_dir, agent, knowledge_dir, extra_args, stream_out) -> int

The module reads hellgate-state/provider.json (via plugins.hellgate.providers)
for the active provider/model and confines all config into the project root.
"""

import importlib

TOOL_IDS = ("opencode",)


def discover():
    tools = []
    for tid in TOOL_IDS:
        try:
            mod = importlib.import_module(f"plugins.hellgate.tools.{tid}")
        except Exception as e:
            tools.append({"id": tid, "name": tid, "license": "?",
                          "install_cmd": None, "confined": False,
                          "notes": f"module error: {e}",
                          "installed": False, "launch": None})
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
