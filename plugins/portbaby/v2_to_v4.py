"""v2 → v4 converter."""

from .v1_to_v4 import convert as v1_to_v4


def convert(events, bpm, source_text=""):
    """Convert v2 events to v4. Reuses v1→v4 logic with section wrapping."""
    result = v1_to_v4(events, bpm, source_text)
    wrapped_result = "// Ported from v2 by Portbaby\n"
    wrapped_result += "// Original sections may not be preserved\n\n"
    wrapped_result += result
    return wrapped_result
