"""Model context scaling — the copilot scales with the model.

Small models get distilled context, big models get everything:
"the more context/params, the more it can consume".

- profile(model, provider)          → small|medium|large (regex heuristics,
                                      incl. Ollama param counts in the name)
- BUDGETS / budget_for(model, prov) → prompt_budget, context_windows,
                                      search_top, max_files, thinking
- system_prompt_scaled(dir, model)  → system prompt assembled by profile from
                                      docs/agent/*.md when present (AGENTS.md /
                                      RULES.md / TODO.md fallback otherwise)
- set_override(profile) / get_override() — module-level profile forcing, used
                                      by `ai context small|medium|large|auto`
"""

import re
from pathlib import Path

from . import agent as llm_agent

# ── profile heuristics ──

SMALL_PATTERNS = re.compile(r"\btiny\b|\bmini\b|\bsmall\b|\bfree\b",
                            re.IGNORECASE)
# Sub-7B param counts (0.5b|1.5b|2b|3b|4b). The (?<![\d.]) guard keeps
# "14b"/"32b"/"130b" from matching 4b/2b/0b inside larger counts.
SMALL_PARAMS = re.compile(r"(?<![\d.])(?:0\.5|1\.5|[2-4])b", re.IGNORECASE)
LARGE_PATTERNS = re.compile(r"70b|405b|gpt-4|claude-opus|deepseek-v4|pro|max",
                            re.IGNORECASE)
# Flagship names that carry no size marker of their own ("deepseek-chat" is
# large-class).
LARGE_NAMES = frozenset({"deepseek-chat", "deepseek-reasoner"})
OLLAMA_PARAMS = re.compile(r"(\d+)b", re.IGNORECASE)

# ── budget table ────────────────────────

BUDGETS = {
    "small": {
        "prompt_budget": 6000,
        "context_windows": 6,
        "search_top": 3,
        "max_files": 1,
        "thinking": "collapsed",
    },
    "medium": {
        "prompt_budget": 18000,
        "context_windows": 10,
        "search_top": 5,
        "max_files": 2,
        "thinking": "collapsed",
    },
    "large": {
        "prompt_budget": 60000,
        "context_windows": 16,
        "search_top": 10,
        "max_files": 4,
        "thinking": "full allowed",
    },
}

# docs/agent/*.md loaded per profile, in prompt order (first = closest to base).
PROFILE_DOCS = {
    "small": ("quickstart.md",),
    "medium": ("quickstart.md", "testing.md", "copilot.md"),
    "large": ("quickstart.md", "testing.md", "copilot.md", "language.md",
              "compiler.md", "plugins.md", "architecture.md"),
}

RULES_CAP = 2500  # RULES.md always goes in, tightly capped
TODO_CAP = 4000   # fallback path: live checklist
FALLBACK_CAPS = (("AGENTS.md", 12000), ("RULES.md", 12000))  # as the legacy builder

_VALID_PROFILES = frozenset({"small", "medium", "large"})
_OVERRIDE = None  # module-level forced profile ("ai context <profile>")


# ── override API ────────────────────────

def set_override(profile=None):
    """Force a profile ("small"|"medium"|"large"); "auto"/None clears."""
    global _OVERRIDE
    if profile is None or str(profile).strip().lower() == "auto":
        _OVERRIDE = None
        return
    p = str(profile).strip().lower()
    if p not in _VALID_PROFILES:
        raise ValueError(f"profile must be small|medium|large|auto, got {profile!r}")
    _OVERRIDE = p


def get_override():
    """Current forced profile, or None when automatic."""
    return _OVERRIDE


# ── classification ──────────────────────

def profile(model, provider=None):
    """Classify a (model, provider) pair → small|medium|large. Unknown → medium."""
    if _OVERRIDE in _VALID_PROFILES:
        return _OVERRIDE
    m = (model or "").strip().lower()
    if not m:
        return "medium"
    if SMALL_PATTERNS.search(m) or SMALL_PARAMS.search(m):
        return "small"
    prov = str(provider or "").strip().lower()
    if prov == "ollama":
        params = [int(n) for n in OLLAMA_PARAMS.findall(m)]
        if params and min(params) < 7:  # any sub-7B count in the name → small
            return "small"
    if m in LARGE_NAMES or LARGE_PATTERNS.search(m):
        return "large"
    return "medium"


def budget_for(model, provider=None):
    """Budget dict for the model's profile (from the table above)."""
    return dict(BUDGETS[profile(model, provider)])


# ── system prompt assembly ──────────────

def _read(path, cap=None):
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None
    if cap is not None:
        text = text[:cap]
    return text


def system_prompt_scaled(project_dir, model, provider=None):
    """Assemble the system prompt for (model, provider) by profile.

    docs/agent/ present → base + RULES.md (capped 2500) + the profile's doc
    set (small = quickstart only; medium adds testing + copilot; large also
    language + compiler + plugins + architecture, each capped by the profile's
    prompt_budget). docs/agent/ missing → legacy fallback: AGENTS.md +
    RULES.md + TODO.md (capped) on top of the base prompt."""
    prof = profile(model, provider)
    root = Path(project_dir)
    parts = []
    docs_dir = root / "docs" / "agent"
    if docs_dir.is_dir() and (docs_dir / "quickstart.md").is_file():
        rules = _read(root / "RULES.md", RULES_CAP)
        if rules:
            parts.append(f"# RULES.md (project instructions)\n{rules}")
        for name in PROFILE_DOCS[prof]:
            text = _read(docs_dir / name)
            if text is None:
                continue
            if name != "quickstart.md" or prof != "small":
                text = text[:BUDGETS[prof]["prompt_budget"]]
            short = name[:-3]
            if len(text) >= BUDGETS[prof]["prompt_budget"]:
                parts.append(f"# {short}.md (agent docs, capped "
                             f"{BUDGETS[prof]['prompt_budget']} chars)\n{text}")
            else:
                parts.append(f"# {short}.md (agent docs)\n{text}")
    else:
        # Legacy fallback: AGENTS.md + RULES.md + TODO.md, existing behavior.
        for name, cap in FALLBACK_CAPS:
            text = _read(root / name, cap)
            if text:
                parts.append(f"# {name} (project instructions)\n{text}")
        todo_text = _read(root / "TODO.md", TODO_CAP)
        if todo_text:
            parts.append(f"# TODO.md (live checklist — update via the 'todo' plan key)\n"
                         f"{todo_text}")
    prompt = llm_agent.SYSTEM_PROMPT
    if parts:
        prompt = prompt + "\n\n" + "\n\n".join(parts)
    return prompt