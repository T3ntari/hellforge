"""v4 → v2 converter via mode_v2_semantic."""


def convert(events, bpm, source_text=""):
    """Downgrade v4 to v2."""
    from ep_compiler.mode_v2_semantic import events_to_v2
    result = "// Downgraded from v4 to v2 by Portbaby\n"
    result += "// ⚠ Major loss: polyrhythms, generative params, channel bindings stripped\n\n"
    result += events_to_v2(events, bpm, source_ver="v4")
    return result
