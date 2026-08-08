"""
E Compiler v4.0 — Modular compiler suite for the E Language.
Supports v1 (#MACHINE/#HUMAN), v2 (semantic), v3 (extended), and v4 (polyrhythm/generative) syntax.
"""

from .cli import main
from .compile import (
    compile_source,
    detect_syntax_version,
)
from .events import (
    create_event,
    validate_events,
)
from .formats import (
    export_midi,
    export_wav,
    export_ec,
)
from .directives import (
    parse_directives,
    TEMPO_ALIASES,
)

def compile_text(text):
    """Compile raw E language text to events. Auto-detects syntax version."""
    return compile_source(text)

def compile_file(path):
    """Compile an .e/.ei/.eic file to events. Auto-detects format."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return compile_source(text)
