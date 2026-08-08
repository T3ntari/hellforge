"""v4 → v1 converter. Maximum information loss."""

from ep_compiler.import_midi import events_to_e_source


def convert(events, bpm, source_text=""):
    """Downgrade v4 to v1. Strips all v4 metadata, keeps only note events."""
    result = "// Downgraded from v4 to v1 by Portbaby\n"
    result += "// ⚠ Maximum loss: polyrhythms, channels, generative params stripped\n\n"
    result += events_to_e_source(events, bpm, human=True)
    return result
