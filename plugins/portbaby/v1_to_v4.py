"""v1 → v4 converter. Machine and human variants with full timing preservation.
Emits math-driven v4: arithmetic progressions collapse into `for $i` loops with
{$i * step} expressions and $beat/$root variables — compact, readable, low-memory."""

from .detectors import detect_channels

_note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
_dur_codes = {2000: "w", 1000: "h", 500: "q", 250: "e", 125: "s", 62: "t"}
_dyn_codes = [(112, "fff"), (96, "ff"), (80, "f"), (64, "mf"), (48, "mp"), (32, "p"), (16, "pp")]

_MIN_RUN = 3  # collapse runs of >= 3 arithmetic events into loops


def _dur_code(ms, bpm):
    scaled = ms * (120.0 / bpm) if bpm > 0 else ms
    for val, code in sorted(_dur_codes.items(), reverse=True):
        if scaled >= val * 0.7:
            code_ms = val * (bpm / 120.0) if bpm > 0 else val
            if abs(code_ms - ms) > 50:
                return None
            return code
    return "t"


def _dyn_name(vel):
    for v, name in _dyn_codes:
        if vel >= v:
            return name
    return "ppp"


def _find_runs(sorted_ev):
    """Greedily find maximal arithmetic-progression runs.
    Each run: (start_idx, length, dts, dmidi, dvel) with constant deltas
    (dts>0, dmidi const, dvel const, duration constant, channel constant).
    Returns list of runs (overlapping-safe, non-overlapping greedy)."""
    runs = []
    i = 0
    n = len(sorted_ev)
    while i < n:
        best = None
        # Try every possible start, grow while arithmetic
        for s in range(i, n):
            dts = None
            dmidi = None
            dvel = None
            dch = sorted_ev[s].get("channel")
            ddur = sorted_ev[s]["duration"]
            length = 1
            j = s + 1
            while j < n:
                a = sorted_ev[j - 1]
                b = sorted_ev[j]
                if b.get("channel") != dch:
                    break
                if b["duration"] != ddur:
                    break
                cur_dts = b["timestamp"] - a["timestamp"]
                cur_dmidi = b["midi"] - a["midi"]
                cur_dvel = b["velocity"] - a["velocity"]
                if cur_dts <= 0:
                    break
                if dts is None:
                    dts, dmidi, dvel = cur_dts, cur_dmidi, cur_dvel
                elif (cur_dts != dts or cur_dmidi != dmidi or cur_dvel != dvel):
                    break
                length += 1
                j += 1
            if length >= _MIN_RUN and (best is None or length > best[1]):
                best = (s, length, dts, dmidi, dvel)
        if best and best[1] >= _MIN_RUN:
            s, length, dts, dmidi, dvel = best
            runs.append(best)
            i = s + length
        else:
            i += 1
    return runs


def convert(events, bpm, source_text=""):
    """v4 machine format — collapses arithmetic progressions into for-loops."""
    return _convert_v4(events, bpm, human=False)


def convert_human(events, bpm, source_text=""):
    """v4 human-readable format — uses @time: for absolute timestamps."""
    return _convert_v4(events, bpm, human=True)


def _emit_loop(run, sorted_ev, bpm, human):
    """Emit a for-loop block for an arithmetic run. Returns list of lines.
    Human mode keeps plain lines (readability); machine mode uses loops."""
    s, length, dts, dmidi, dvel = run
    base = sorted_ev[s]
    count = length
    beat_ms = 60000 / bpm if bpm > 0 else 500
    base_ts = base["timestamp"]

    # Time: base offset + $i * step; use $beat math when dts divides the beat
    if dts and beat_ms and beat_ms % dts == 0:
        divisor = int(beat_ms // dts)
        if divisor == 1:
            t_expr = f"{base_ts} + $i * $beat"
        else:
            t_expr = f"{base_ts} + $i * $beat / {divisor}"
    else:
        t_expr = f"{base_ts} + $i * {dts}"

    n_expr = f"{base['midi']} + $i * {dmidi}" if dmidi else str(base['midi'])
    v_expr = f"{base['velocity']} + $i * {dvel}" if dvel else str(base['velocity'])
    d_val = base['duration']
    ch = base.get("channel")
    ch_part = f"CH[{ch}] " if ch is not None else ""

    lines = [f"// Loop: {count} notes (T+{dts}ms, N+{dmidi}, V+{dvel})"]
    lines.append("$bpm = {}".format(int(bpm)))
    lines.append("$beat = 60000 / $bpm")
    lines.append(f"for $i = 0 to {count-1} {{")
    lines.append(f"    {ch_part}T{{{t_expr}}} N{{{n_expr}}} D{d_val} V{{{v_expr}}}".rstrip())
    lines.append("}")
    return lines


def _convert_v4(events, bpm, human=False):
    sorted_ev = sorted(events, key=lambda e: (e["timestamp"], e["midi"]))
    if not sorted_ev:
        return "@bpm {}".format(int(bpm))
    beat_ms = 60000 / bpm if bpm > 0 else 500
    chs = set(e.get("channel") for e in events if e.get("channel") is not None)
    total_dur = max(e["timestamp"] + e["duration"] for e in sorted_ev)

    lines = []
    lines.append("// Ported to v4 by Portbaby")
    if human:
        lines.append("@mode human")
        lines.append("// Uses @time:N for absolute timing precision")
    lines.append("@bpm {}".format(int(bpm)))
    if chs:
        lines.append("// CH: {}".format(', '.join(str(c) for c in sorted(chs))))

    runs = _find_runs(sorted_ev)

    # Split into loop regions and plain regions
    covered = set()
    for (s, length, *_rest) in runs:
        for k in range(s, s + length):
            covered.add(k)

    # Emit in order: plain events outside runs (packed 4-per-line with ';'),
    # loops for runs
    i = 0
    pending = []
    while i < len(sorted_ev):
        if i in covered:
            # flush pending plain lines
            if pending:
                lines.extend(_pack_lines(pending, human))
                pending = []
            run = next(r for r in runs if r[0] <= i < r[0] + r[1])
            lines.extend(_emit_loop(run, sorted_ev, bpm, human))
            i = run[0] + run[1]
            continue
        pending.append(sorted_ev[i])
        if len(pending) >= 4:
            lines.extend(_pack_lines(pending, human))
            pending = []
        i += 1
    if pending:
        lines.extend(_pack_lines(pending, human))

    return "\n".join(lines)


def _pack_lines(events, human):
    """Pack plain events into lines — up to 4 statements per line joined with ';'."""
    if not events:
        return []
    out = []
    parts = []
    for e in events:
        nn = _note_names[e["midi"] % 12]
        octave = e["midi"] // 12 - 1
        dyn = _dyn_name(e["velocity"])
        ch = e.get("channel")
        if human:
            ch_part = " @ch:{}".format(ch) if ch is not None else ""
            time_part = " @time:{}".format(e["timestamp"])
            dur_part = "{}ms".format(max(10, min(e["duration"], 5000)))
            parts.append("play note({}{}) @dur:{} @vel:{}{}{}".format(
                nn, octave, dur_part, dyn, time_part, ch_part))
        else:
            ch_part = "CH[{}] ".format(ch) if ch is not None else ""
            parts.append("{}{}T{} N{} D{} V{:.2f}".format(
                ch_part, "" if ch_part else "", e["timestamp"], e["midi"],
                e["duration"], e["velocity"] / 127.0))
    out.append("; ".join(parts))
    return out
