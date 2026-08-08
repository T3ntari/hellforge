"""v3 → v4 converter. Most v3 features carry forward directly."""


def convert(events, bpm, source_text=""):
    """Convert v3 to v4. Events themselves need no transformation,
    but we add the v4 header for polyrhythm/generative support."""
    from .v1_to_v4 import convert as v1_to_v4
    result = v1_to_v4(events, bpm, source_text)
    result = "// Upgraded from v3 to v4 by Portbaby\n// v3 features (macros, shorthand, repeats) preserved\n\n" + result
    return result
