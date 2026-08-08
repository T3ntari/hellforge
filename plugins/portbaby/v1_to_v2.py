"""v1 → v2 Semantic syntax converter using mode_v2_semantic."""


def convert(events, bpm, source_text=""):
    """Convert v1 events to v2 section-based syntax."""
    from ep_compiler.mode_v2_semantic import events_to_v2
    return events_to_v2(events, bpm, source_ver="v1")
