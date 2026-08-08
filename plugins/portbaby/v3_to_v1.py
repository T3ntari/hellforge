"""v3 → v1 Machine/Human converter. Expands shorthand and macros to flat events."""

from ep_compiler.import_midi import events_to_e_source


def convert(events, bpm, source_text=""):
    """Convert v3 events to v1 by re-emitting as machine tokens."""
    return events_to_e_source(events, bpm, human=True)
