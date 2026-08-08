"""v2 → v1 Machine/Human converter (downgrade)."""

from ep_compiler.import_midi import events_to_e_source
from ep_compiler.mode_v2_semantic import compile_v2


def convert(events, bpm, source_text=""):
    """Downgrade v2 events to v1 syntax."""
    # If we have raw events, just re-emit as v1
    if events:
        return events_to_e_source(events, bpm, human=True)
    # If we have source text, compile v2 then emit
    if source_text:
        ev, bp = compile_v2(source_text)
        if ev:
            return events_to_e_source(ev, bp, human=True)
    return events_to_e_source(events, bpm, human=True)
