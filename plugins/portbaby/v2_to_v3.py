"""v2 → v3 Shorthand converter."""

from .v1_to_v3 import convert as v1_to_v3


def convert(events, bpm, source_text=""):
    """Convert v2 events to v3 shorthand. Reuses v1→v3 logic."""
    return v1_to_v3(events, bpm, source_text)
