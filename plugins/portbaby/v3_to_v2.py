"""v3 → v2 converter via mode_v2_semantic."""


def convert(events, bpm, source_text=""):
    """Convert v3 to v2 using the shared events_to_v2 function."""
    from ep_compiler.mode_v2_semantic import events_to_v2
    result = "// Ported from v3 (shorthand) by Portbaby\n"
    result += "// Chord detection is approximate — review before use\n\n"
    result += events_to_v2(events, bpm, source_ver="v3")
    return result
