"""#MACHINE mode parser: T0 N60 D500 V0.8 syntax + word forms (N C4, D q, V mf).

Strict: anchored regex, unknown tokens / out-of-range values report typed
problems via ep_compiler.syntax_check instead of failing silently."""

import re

from .syntax_check import check_machine_line

# Module-level diagnostics store — compile/linter/LSP read these.
last_problems = []


def parse_machine_line(line, ll_state):
    """Parse a single #MACHINE line. Returns event dict or None.
    Problems (with code/line/char/length) are appended to last_problems."""
    problems = []
    g = check_machine_line(line, problems, bpm=ll_state.get("bpm", 120))
    if g is None:
        last_problems.extend(problems)
        return None

    midi = g["_midi"]
    vel = g["_vel"]
    dur = g["_dur"]
    if midi < 0 or midi > 127 or dur is None:
        last_problems.extend(problems)
        return None
    vel = max(0, min(127, vel))
    dur = max(1, dur)

    bend = int(g["bend"]) if g["bend"] else 0
    pan = float(g["pan"]) if g["pan"] else 0.0

    event = {
        "timestamp": g["_ts"],
        "midi": midi,
        "duration": dur,
        "velocity": vel,
        "pan": max(-1.0, min(1.0, pan)),
        "bend": max(-64, min(64, bend)),
        "channel": int(g["channel"]) if g["channel"] else None,
        "track": g["track"] if g["track"] else None,
        "filter_cutoff": g["filter_cutoff"],
        "filter_res": float(g["filter_res"]) if g["filter_res"] else ll_state.get("filter_res"),
        "filter_type": g["filter_type"] or ll_state.get("filter_type"),
        "env_attack": g["env_attack"] or ll_state.get("env_attack"),
        "env_release": g["env_release"] or ll_state.get("env_release"),
        "env_sustain": float(g["env_sustain"]) if g["env_sustain"] else ll_state.get("env_sustain"),
        "phase": float(g["phase"]) if g["phase"] else ll_state.get("phase"),
        "cents": int(g["cents"]) if g["cents"] else ll_state.get("cents"),
        "master_vol": ll_state.get("master_vol"),
        "gain_db": ll_state.get("gain_db"),
    }
    if g.get("art"):
        try:
            from .mode_v5_performance import apply_articulation
            event["art"] = g["art"]
            apply_articulation(event, g["art"])
        except Exception:
            pass
    return event


def detect_machine(text):
    """Detect if text contains #MACHINE syntax."""
    return bool(re.search(r'^T\d+\s+N\d+', text, re.MULTILINE))
