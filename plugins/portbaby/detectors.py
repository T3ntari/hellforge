"""Version and structure detection utilities."""

import re


def detect_structure(text):
    """Analyze source text for structural elements.
    Returns dict with counts of various features."""
    result = {
        "events": len([l for l in text.split("\n") if re.match(r"^T\d+\s+N\d+", l)]),
        "sections": len(re.findall(r'\[Section:|section\s+"', text, re.I)),
        "macros": len(re.findall(r"^!\w+\s*=", text, re.MULTILINE)),
        "chords": len(re.findall(r"play\s+chord\(", text, re.I)),
        "human_notes": len(re.findall(r"play\s+note\(", text, re.I)),
        "shorthand": len(re.findall(r"^[A-G]#?b?\d+\s+[whqest]", text, re.MULTILINE)),
        "probability": len(re.findall(r"\?\d+\.\d+\s+T", text)),
        "repeats": len(re.findall(r"x\d+\s*$", text, re.MULTILINE)),
        "random_v": len(re.findall(r"V~", text)),
        "random_d": len(re.findall(r"D~", text)),
        "parallel": text.count("&"),
        "polyrhythms": len(re.findall(r"\[\w+\]/\d+", text)) + len(re.findall(r"E\(\d+,\d+\)", text)),
        "channels": len(set(re.findall(r"CH\[(\d+)\]", text))),
        "tracks": len(re.findall(r"TRK\[", text)),
    }
    return result


def estimate_complexity(text):
    """Estimate musical complexity on a scale of 1-10."""
    struct = detect_structure(text)
    score = 1
    if struct["events"] > 100:
        score += 1
    if struct["events"] > 1000:
        score += 1
    if struct["sections"] > 0:
        score += 1
    if struct["macros"] > 0:
        score += 1
    if struct["chords"] > 0:
        score += 1
    if struct["probability"] > 0 or struct["random_v"] > 0:
        score += 1
    if struct["polyrhythms"] > 0:
        score += 2
    if struct["repeats"] > 0:
        score += 1
    return min(score, 10)


def detect_channels(events):
    """Detect which MIDI channels are used in events."""
    chs = set()
    for e in events:
        ch = e.get("channel")
        if ch is not None:
            chs.add(ch)
    return sorted(chs) if chs else [0]
