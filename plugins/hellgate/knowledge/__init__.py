"""hellgate.knowledge — the HELLFORGE knowledge pack.

v5-accurate documentation digests for external agent TUIs (OpenCode,
Aider, OpenHands, Goose) plus the music-agent personas. All text is read
fresh from the .md files in this directory on every call, so edits to the
markdown take effect immediately; missing files degrade to empty values.

Public API:
    agent_names()                    -> list[str]      ("## Name" headings in agents.md)
    agent_text(name: str)            -> str | None     (one persona body)
    full_text()                      -> str            (full.md — comprehensive map)
    core_text()                      -> str            (core.md — distilled digest)
    samples_text()                   -> str            (samples-index.md — samples table)
    pick_for(model_context_tokens)   -> tuple[str, str] (("core"|"full", text))
"""

import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    """Read a knowledge file. Returns its text or "" when missing/unreadable."""
    path = os.path.join(_HERE, name)
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return fh.read()
    except OSError:
        return ""


def full_text():
    """Comprehensive knowledge map (full.md)."""
    return _read("full.md")


def core_text():
    """Distilled key-points digest (core.md)."""
    return _read("core.md")


def samples_text():
    """Samples/examples index table (samples-index.md)."""
    return _read("samples-index.md")


def agent_names():
    """Parse the '## <Name>' headings in agents.md (level-2 headings only).

    Returns the heading names in document order, e.g.
    ["Music-Composer", "Music-Refiner"]. Empty list when the file is
    missing or has no level-2 headings.
    """
    names = []
    for line in _read("agents.md").splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("##\t"):
            names.append(stripped[2:].strip())
    return names


def agent_text(name):
    """Return one persona's section body from agents.md, or None.

    A section runs from its '## <Name>' heading to the next '## ' heading.
    The heading line itself is included, so the returned text is a
    self-contained system prompt. Case-insensitive name matching.
    """
    text = _read("agents.md")
    lines = text.splitlines()
    target = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") or stripped.startswith("##\t"):
            candidate = stripped[2:].strip()
            if target is None and candidate.lower() == str(name).lower():
                target = i
            elif target is not None:
                return "\n".join(lines[target:i]).strip() or None
    if target is not None:
        return "\n".join(lines[target:]).strip() or None
    return None


def pick_for(model_context_tokens):
    """Pick the digest for a model context budget.

    Returns (kind, text): kind is "core" when model_context_tokens is
    below 120000 (small context gets the distilled digest), otherwise
    "full". A missing file yields its text as "" with the matching kind.
    """
    if model_context_tokens < 120000:
        return ("core", core_text())
    return ("full", full_text())
