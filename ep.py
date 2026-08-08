#!/usr/bin/env python3
"""
E Language Compiler v4.0 — Compatibility Shim.
All existing commands and syntax continue to work.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ep_compiler.cli import main
from ep_compiler.compile import (
    compile_source,
    compile_file as compile_auto,
    detect_syntax_version,
)
from ep_compiler.events import (
    create_event,
    validate_events,
    sort_events,
    midi_to_name,
    name_to_midi,
)
from ep_compiler.formats import (
    export_midi,
    export_ec,
    export_eic,
)
from ep_compiler.import_midi import (
    import_midi,
    events_to_e_source,
    import_ec,
    midi_to_e_project,
)
from ep_compiler.mode_eci import compile_eci
from ep_compiler.mode_enx import (
    compile_enx,
    parse_enx,
)
from ep_compiler.e_runtime import (
    load_ei,
    compile_ei_file,
    compile_ei_project,
    EIProject,
)
from ep_compiler.directives import (
    parse_directives,
    TEMPO_ALIASES,
)

# Backward-compatible aliases
parse_e_file = lambda path: _read_and_compile(path)
get_input_events = parse_e_file

def _read_and_compile(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    return compile_source(text)

if __name__ == "__main__":
    try:
        main()
    except IsADirectoryError as e:
        print(f"  Error: {e}", file=sys.stderr)
        print("  That's a directory — compile takes a single file.", file=sys.stderr)
        print("  Use 'run.py compile <dir>' to compile every file in a directory.", file=sys.stderr)
        sys.exit(1)
