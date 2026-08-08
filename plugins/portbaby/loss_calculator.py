"""Loss percentage computation for syntax version conversions."""

# Loss estimates for each conversion path
# Keys: (source_ver, target_ver) -> (base_loss_pct, issues)
LOSS_MATRIX = {
    ("v1_machine", "v1_human"): (0, []),
    ("v1_human", "v1_machine"): (0, []),
    ("v1_machine", "v2"): (10, ["Section structure not detected", "Chord blocks approximated"]),
    ("v1_human", "v2"): (5, ["Some chord voicings simplified"]),
    ("v1_machine", "v3"): (2, ["Macro detection is best-effort"]),
    ("v1_human", "v3"): (0, []),
    ("v1_machine", "v4"): (15, ["No polyrhythm info to preserve", "Channel bindings may be guessed"]),
    ("v1_human", "v4"): (10, ["Polyrhythm structure approximated"]),
    ("v2", "v1_machine"): (25, ["Section structure lost", "Chord blocks flattened"]),
    ("v2", "v1_human"): (20, ["Section structure lost"]),
    ("v2", "v3"): (10, ["Arpeggios expanded, not preserved as patterns"]),
    ("v2", "v4"): (15, ["Polyrhythm detection from v2 is approximate"]),
    ("v3", "v1_machine"): (5, ["Macros expanded, not preserved"]),
    ("v3", "v1_human"): (3, ["Shorthand expanded to play() syntax"]),
    ("v3", "v2"): (20, ["Chord detection from notes is approximate", "Section boundaries not in v3"]),
    ("v3", "v4"): (2, ["Most v3 features carry forward"]),
    ("v4", "v3"): (15, ["Polyrhythms approximated as tuplets"]),
    ("v4", "v2"): (30, ["Major structural downgrade", "Generative params lost"]),
    ("v4", "v1_machine"): (40, ["Maximum information loss", "All v4 metadata stripped"]),
    ("v4", "v1_human"): (35, ["Polyrhythm, generative, channel info lost"]),
}

# Quality adjustments based on actual content
QUALITY_MODIFIERS = {
    "has_polyrhythm": 15,   # extra loss if source has polyrhythms going to v1
    "has_macros": 5,        # macros can't be perfectly reverse-engineered
    "has_channels": 8,      # channel info lost going to v1
    "has_sections": 10,     # section structure lost going to v1/v3
    "has_random": 5,        # randomization can't be reverse-engineered
}


def calculate_loss(source_ver, target_ver, events):
    """Calculate estimated loss percentage for a conversion.
    Returns dict with loss_pct, issues list."""
    base = LOSS_MATRIX.get((source_ver, target_ver))
    if base is None:
        # Try reverse tuple
        base = LOSS_MATRIX.get((target_ver, source_ver))
        if base:
            return {"loss_pct": base[0], "issues": base[1], "events_in": len(events), "events_out": len(events)}
        return {"loss_pct": 50, "issues": ["Unknown conversion path"], "events_in": len(events), "events_out": len(events)}

    loss_pct, issues = base

    # Adjust based on actual content
    # Check for channels
    chs = set(e.get("channel") for e in events if e.get("channel") is not None)
    if chs and target_ver in ("v1_machine", "v1_human"):
        loss_pct += QUALITY_MODIFIERS["has_channels"]
        issues.append(f"{len(chs)} channel(s) will be merged")

    # Check for velocity extremes (indicates dynamic complexity)
    vels = [e.get("velocity", 80) for e in events]
    if vels and (max(vels) - min(vels)) > 80:
        loss_pct += 3
        issues.append("Wide dynamic range may be compressed")

    # Check event density (indicates complexity)
    if len(events) > 10000:
        loss_pct += 5
        issues.append("Large composition: structure may not be perfectly preserved")

    loss_pct = min(loss_pct, 100)  # cap at 100%

    return {"loss_pct": loss_pct, "issues": issues[:5], "events_in": len(events), "events_out": len(events)}
