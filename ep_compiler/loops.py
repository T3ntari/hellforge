"""E Loop Unroller — repeat N, for, while.
Pure core: parses loop constructs and unrolls them into flat line sequences.
Supports nested loops via recursive unrolling.
Supports mutable variable conditions in while loops."""

import re

class LoopError(Exception):
    pass

# Hard cap on unrolled output lines — prevents OOM on runaway loops.
# Configurable: set_unroll_cap(N). 0 = no cap.
_MAX_UNROLL_LINES = 100000


def set_unroll_cap(n):
    """Set the maximum number of unrolled lines before LoopError (0 = no cap)."""
    global _MAX_UNROLL_LINES
    _MAX_UNROLL_LINES = max(0, int(n))


def get_unroll_cap():
    return _MAX_UNROLL_LINES

VAR_DEF_RE = re.compile(r"^\$([a-zA-Z_]\w*)\s*=\s*(.+)$")


def _check_cap(result, loop_desc, cap):
    """Raise a clear LoopError when unrolled output exceeds the cap.
    Fails gracefully instead of OOM-ing."""
    if cap and len(result) > cap:
        raise LoopError(
            f"Loop '{loop_desc}' expanded beyond {cap} lines "
            f"({len(result)}). Reduce the range or raise the cap "
            f"via 'sys mem' / set_unroll_cap()."
        )


def _find_block_end(lines, start_idx):
    """Find matching close-brace for open-brace at start_idx line.
    Returns index of the close-brace line, or None if not found."""
    depth = 0
    for i in range(start_idx, len(lines)):
        stripped = lines[i].strip()
        depth += stripped.count("{") - stripped.count("}")
        if depth == 0:
            return i
    return None


def _parse_block_header(line):
    """Parse the header of a loop block. Returns (kind, args, body_lines).
    Supports single-line bodies: 'for $i = 0 to 3 { T{$i*100} N60 D100 }'."""
    s = line.strip()
    m = re.match(r"^repeat\s+(\d+|\$[a-zA-Z_]\w*)\s*(?:\{.*)?$", s)
    if m:
        return ("repeat", [m.group(1)], None)
    m = re.match(r"^for\s+\$([a-zA-Z_]\w*)\s*=\s*(-?\$?[\w.]+)\s+to\s+(-?\$?[\w.]+)(?:\s+step\s+(-?\$?[\w.]+))?\s*(?:\{.*)?$", s)
    if m:
        return ("for", [m.group(1), m.group(2), m.group(3), m.group(4)], None)
    m = re.match(r"^while\s+(.+?)\s*(?:\{.*)?$", s)
    if m:
        return ("while", [m.group(1)], None)
    return None, None, None


def _eval_expr(expr, scope):
    """Evaluate a simple arithmetic expression string with $vars replaced from scope.
    Supports + - * / // % ( ) and numbers."""
    try:
        for k, v in sorted(scope.items(), key=lambda x: -len(x[0])):
            expr = expr.replace(f"${k}", str(v))
        expr = expr.replace("$", "")
        return int(eval(expr, {"__builtins__": {}}, {"abs": abs, "round": round, "min": min, "max": max, "int": int}))
    except Exception:
        return None


def _extract_block_body(lines, idx):
    """Extract body lines from a loop block starting at idx.
    Returns (body_lines, end_idx) or (None, None) if unclosed."""
    stripped = lines[idx].strip()
    if "{" in stripped and "}" in stripped:
        body_start = stripped.index("{") + 1
        body_str = stripped[body_start:].strip()
        if body_str.endswith("}"):
            body_str = body_str[:-1].strip()
        return ([body_str] if body_str else [], idx)
    block_end = _find_block_end(lines, idx)
    if block_end is None:
        return None, None
    body_lines = []
    for j in range(idx + 1, block_end):
        b = lines[j].strip()
        if b:
            body_lines.append(b)
    return body_lines, block_end


def _unroll_once(lines, var_resolver, scope):
    """Single pass unroll: process lines, expand loops, return new lines.
    Returns (new_lines, any_unrolled) where any_unrolled indicates whether any loop was expanded."""
    result = []
    any_unrolled = False
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        kind, args, _ = _parse_block_header(stripped)

        if kind:
            body_lines, end_idx = _extract_block_body(lines, i)
            if body_lines is None:
                result.append(line)
                i += 1
                continue
            i = end_idx
            any_unrolled = True

            if kind == "repeat":
                count_str = args[0]
                if count_str.startswith("$"):
                    count = var_resolver(count_str[1:])
                    if count is None:
                        raise LoopError(f"Variable not found: {count_str}")
                    count = int(count)
                else:
                    count = int(count_str)
                for n in range(count):
                    for bl in body_lines:
                        resolved = bl.replace("$i", str(n)).replace("$counter", str(n))
                        result.append(resolved)
                    _check_cap(result, f"repeat {count_str}", _MAX_UNROLL_LINES)

            elif kind == "for":
                var_name, start_s, end_s, step_s = args
                def _r(v):
                    if v and str(v).startswith("$"):
                        r = var_resolver(v[1:])
                        return int(r) if r is not None else int(v)
                    return int(v) if v else 1
                start = _r(start_s)
                end = _r(end_s)
                step = _r(step_s) if step_s else 1
                n = start
                while (step > 0 and n <= end) or (step < 0 and n >= end):
                    for bl in body_lines:
                        resolved = bl.replace(f"${var_name}", str(n))
                        result.append(resolved)
                    _check_cap(result, f"for ${var_name} = {start_s} to {end_s}", _MAX_UNROLL_LINES)
                    n += step

            elif kind == "while":
                cond_str = args[0]
                local_scope = {}
                # Seed from var_resolver for vars mentioned in body
                for bl in body_lines:
                    m = VAR_DEF_RE.match(bl)
                    if m:
                        vname = m.group(1)
                        resolved = var_resolver(vname)
                        if resolved is not None:
                            local_scope[vname] = resolved
                iterations = 0
                while iterations < 100000:
                    cv = _eval_expr(cond_str, local_scope)
                    if cv is None:
                        cv = 1
                    if not cv:
                        break
                    for bl in body_lines:
                        result.append(bl)
                    _check_cap(result, f"while {cond_str}", _MAX_UNROLL_LINES)
                    # Process var defs in body to update local scope
                    for bl in body_lines:
                        m = VAR_DEF_RE.match(bl)
                        if m:
                            vname = m.group(1)
                            rhs = m.group(2)
                            val = _eval_expr(rhs, local_scope)
                            if val is not None:
                                local_scope[vname] = val
                    iterations += 1
        else:
            result.append(line)

        i += 1

    return result, any_unrolled


def detect_and_unroll_loops(lines, var_resolver, scope=None):
    """Scan lines for loop constructs and unroll them.
    Handles nested loops via recursive fixed-point unrolling.
    Handles multi-line blocks: repeat N { ... }, for ..., while ...
    scope: optional Scope/dict for while loop mutable variables
    Returns a flat list of lines with loops expanded."""
    current = list(lines)
    while True:
        current, any_unrolled = _unroll_once(current, var_resolver, scope)
        if not any_unrolled:
            break
    return current
