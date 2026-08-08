"""v1 → v3 Shorthand converter with exact ms duration preservation."""

_dyn_codes = [(112,"fff"),(96,"ff"),(80,"f"),(64,"mf"),(48,"mp"),(32,"p"),(16,"pp")]
def _dyn_name(vel):
    for v, name in _dyn_codes:
        if vel >= v:
            return name
    return "ppp"


def convert(events, bpm, source_text=""):
    """Convert v1 events to v3 shorthand with original durations (exact ms)."""
    sorted_ev = sorted(events, key=lambda e: e["timestamp"])
    lines = ["@bpm {}".format(int(bpm))]

    for e in sorted_ev:
        ts = e["timestamp"]
        # Always use machine format with exact original duration
        lines.append("T{} N{} D{} V{:.2f}".format(ts, e['midi'], e['duration'], e['velocity'] / 127.0))

    return "\n".join(lines)
