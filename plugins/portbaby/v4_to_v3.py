"""v4 → v3 converter. Polyrhythms approximated as tuplets."""

from ep_compiler.import_midi import events_to_e_source


def convert(events, bpm, source_text=""):
    """Downgrade v4 to v3. Polyrhythm info is lost, notes preserved."""
    result = "// Downgraded from v4 to v3 by Portbaby\n"
    result += "// Polyrhythm structure approximated. Review manually.\n\n"
    result += events_to_e_source(events, bpm, human=True)
    return result
