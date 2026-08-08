"""Compile pipeline orchestrator. Detects syntax version, routes to correct parser, validates output.
Handles .e, .ei, .eci, .enx formats. Strips comments; detects circular deps; fires plugin hooks."""

import re
import os
from .events import (
    create_event,
    validate_events,
    sort_events,
)
from .directives import (
    parse_directives,
    parse_config_strip,
    DEFAULT_LL_STATE,
)
from .mode_v1_machine import (
    parse_machine_line,
    detect_machine,
)
from .mode_v1_human import parse_human_line
from .comments import strip_comments
from .graph import (
    CompilationGraph,
    CircularReferenceError,
)
from .math_engine import (
    build_ast,
    ast_to_dict,
    find_expressions,
    is_var_definition,
    parse_var_definition,
)
from .variables import (
    Scope,
    evaluate_expression,
)
from .loops import (
    detect_and_unroll_loops,
    LoopError,
)


class CompileError(Exception):
    """Raised by strict compilation — carries the diagnostic list."""

_graph = CompilationGraph()


def preprocess_math(lines, scope=None):
    """Process #MATH lines: variable definitions, expression substitution, loop unrolling.
    Works with whatever evaluators are registered (LURE, Python, or none).
    If no evaluator, {$expr} is left as-is — no crash."""
    if scope is None:
        scope = Scope()

    result = []
    for line in lines:
        stripped = line.strip()

        # Variable definition: $bpm = 120
        if is_var_definition(stripped):
            name, expr_str = parse_var_definition(stripped)
            if name:
                # Try to evaluate the expression immediately
                val, err = evaluate_expression(expr_str, scope)
                if val is not None:
                    scope.set(name, val)
                else:
                    # Can't evaluate yet — store as string for later
                    scope.set(name, expr_str)
            continue

        # Variable reference resolution + expression substitution
        processed = line
        matches = find_expressions(processed)
        for full_match, inner_expr, start, end in sorted(matches, key=lambda m: -m[3]):
            val, err = evaluate_expression(inner_expr, scope)
            if val is not None:
                if isinstance(val, float):
                    # Round to nearest int for timestamps/durations, keep 3 decimals for others
                    val = round(val) if val > 1 else round(val, 3)
                    if val == int(val):
                        val = int(val)
                processed = processed[:start] + str(val) + processed[end:]

        # Simple $var resolution — only for $var NOT inside {} blocks
        # These are rare: bare $bpm outside of {$bpm * 2}
        def _replace_var(m):
            pos = m.start()
            # Check if inside braces by scanning backwards for { without matching }
            before = processed[:pos]
            if before.count("{") > before.count("}"):
                return m.group(0)  # inside braces — skip
            v = scope.get(m.group(1))
            return str(v) if v is not None else m.group(0)
        processed = re.sub(r'\$([a-zA-Z_]\w*)', _replace_var, processed)

        result.append(processed)

    return result


_DEPRECATION_WARNED = set()


_V5_STATEMENT_RE = re.compile(
    r'^\s*(?:print|assert|include)\b|^\s*prog\s*\(|^\s*perc\s*\(|^!fn\s+'
    r'|\bpick\s*\(|\brand\s*\(|\bscale\s*\(|\brun\s*\('
    r'|for\s+\$[a-zA-Z_]\w*\s+in\s+\[|\.\.\s|^\s*(?:break|continue)\s*$',
    re.I | re.MULTILINE)


def _has_v5_statement(text):
    """True when the source uses v5-only statements that earlier pipelines
    (and the LURE fast path) cannot handle."""
    return bool(_V5_STATEMENT_RE.search(text or ""))


def _warn_deprecated(version):
    """Print the deprecation banner once per version per process.
    v5 is the canonical syntax; v1-v4 compile for back-compat only."""
    if version in _DEPRECATION_WARNED:
        return
    _DEPRECATION_WARNED.add(version)
    print(f"WARNING: {version} syntax is deprecated — use v5 (convert with 'run.py compile --to v5')")


def detect_syntax_version(text):
    text = strip_comments(text)
    if re.search(r'#compiler\s+\w+\s*:', text, re.I):
        pass
    # v5 markers (checked first — v5 is a superset of everything)
    v5_patterns = [
        r'Version:\s*v5',               # v5 header
        r'//\s*v5\b',                   # v5 comment marker
        r'\bpedal\s+(?:on|off)\b',      # sustain pedal statements
        r'^\s*(?:rest|R)\s+[whqest0-9]',  # rests
        r'\bt3\s*\(|\btrip\s*\(|\btup\s*\(',  # tuplets
        r'@oct\s*:',                    # octave shift directive
        r'@art\s*:',                    # articulations
        r'@tie\b',                      # ties (prop)
        r'[A-Ga-g]#?b?\d\s*~',          # ties (tilde shorthand)
        r'^\s*(?:print|assert|include)\b',  # io statements
        r'^\s*prog\s*\(',               # chord progressions
        r'^\s*perc\s*\(',               # percussion
        r'^!fn\s+',                     # parameterized macros
        r'\bpick\s*\(|\brand\s*\(',     # deterministic randomness
        r'\bscale\s*\(|\brun\s*\(',     # scale/chromatic iteration
        r'for\s+\$[a-zA-Z_]\w*\s+in\s+\[|\.\.\s*\d',  # list/range loops
        r'^\s*(?:break|continue)\s*$',  # loop control
    ]
    for p in v5_patterns:
        if re.search(p, text, re.I | re.MULTILINE):
            return 'v5'
    # v4 markers (next superset level)
    v4_patterns = [
        # NOTE: Euclidean E(5,4) and polyrhythm [C4 E4](3:2) are valid v5
        # superset constructs — markerless files with them default to v5.
        r'ritard(?:ando)?\(',           # ritardando
        r'@curve\s+(?:bpm|vel)',        # tempo / velocity curves
        r'Version:\s*v4',               # v4 header
        r'//\s*v4\b',                   # v4 comment marker
        r';\s*T\d',                     # semicolon statement separators
        r';\s*play\s+note',             # semicolon human statements
        r'\bT\s*:\s*\d+',               # labeled machine fields
        r'<[A-Ga-g]#?b?\d[^>{}]*>',     # angle-bracket note groups
        r'[A-Ga-g]#?b?\d\s*\|',         # pipe-parallel notes
        r'\\\s*$',                      # backslash line continuation
    ]
    for p in v4_patterns:
        if re.search(p, text, re.I | re.MULTILINE):
            _warn_deprecated('v4')
            return 'v4'
    v3_patterns = [r'@(adagio|allegro|presto)', r'^!\w+\s*=', r'\?\d+\.\d+\s+T',
                   r'V~', r'D~',
                   # NOTE: `C4 q` v3 shorthand is a valid v5 superset
                   # construct — markerless files default to v5.
                   r'x\d+\s*$', r'&', r'/\*', r'ppp\s*<']
    for p in v3_patterns:
        if re.search(p, text, re.I | re.MULTILINE):
            _warn_deprecated('v3')
            return 'v3'
    v2_patterns = [r'\[Section:', r'Key:\s*\w+_\w+', r'play\(', r'arpeggio\(', r'chromatic_run\(']
    for p in v2_patterns:
        if re.search(p, text, re.I):
            _warn_deprecated('v2')
            return 'v2'
    v1_patterns = [r'Version:\s*v1', r'//\s*v1\b', r'#MACHINE', r'#HUMAN']
    for p in v1_patterns:
        if re.search(p, text, re.I):
            _warn_deprecated('v1')
            return 'v1_machine' if re.search(r'^T\d+\s+N\d+', text, re.MULTILINE) else 'v1_human'
    # Everything else — including plain machine lines (T0 N60 D500 V80) and
    # plain human lines (play note(...)) with no version markers — compiles
    # as v5: the canonical default. No deprecation notice.
    return 'v5'


def apply_scale_quantization(events, ll_state):
    scale = ll_state.get("scale")
    if scale:
        # Try LURE quantizer first
        try:
            from plugins.lure import quantize as lure_quantize
            if lure_quantize:
                result = lure_quantize(events, scale)
                if result is not None:
                    return result
        except ImportError:
            pass
        try:
            from .scale_quantizer import quantize_events
            events = quantize_events(events, scale)
        except ImportError:
            pass
    return events


def apply_ll_controllers(events, ll_state):
    """Apply low-level controller directives to compiled events.
    - @gain:dB scales velocities (linear amplitude gain)
    - @gc:<strategy> runs real garbage collection on the event list
    - @mem:<budget> enforces an event-count budget (warn + truncate)
    Returns the (possibly modified) events list."""
    if not events:
        return events

    gain_db = ll_state.get("gain_db")
    if gain_db:
        factor = 10 ** (float(gain_db) / 20.0)
        for e in events:
            e["velocity"] = max(0, min(127, int(round(e.get("velocity", 80) * factor))))

    strategy = ll_state.get("gc_strategy", "default")
    if strategy and strategy != "off":
        try:
            import ep_core
            events = ep_core.run_gc(events, strategy)
        except Exception:
            pass

    budget = ll_state.get("mem")
    if budget:
        if len(events) > budget:
            print(f"  > @mem: {len(events)} events exceeds budget {budget} — truncating")
            events = events[:budget]
    return events


def apply_performance_post_passes(events, text, bpm, ll_state):
    """Run v5 piano-performance post-passes: velocity curves, ties,
    global sustain state, octave shift, legato adjustment."""
    try:
        from .mode_v5_performance import apply_performance_post_passes as _v5
        return _v5(events, text, bpm, ll_state)
    except Exception:
        return events


def compile_source(text, bpm=None, strict=False, base_dir=None):
    """Compile source text to (events, bpm).
    strict=True raises CompileError listing all diagnostics (fail-fast).
    The '@strict on' directive in source forces strict; '@strict off' relaxes."""
    if re.search(r"@strict\s+on\b", text, re.I):
        strict = True
    elif re.search(r"@strict\s+off\b", text, re.I):
        strict = False
    try:
        from .mode_v1_machine import last_problems as _mlp
        from .mode_v1_human import last_problems as _hlp
        _mlp.clear()
        _hlp.clear()
    except Exception:
        pass
    """Compile E language text to events. Auto-detects syntax version.
    Uses LURE (LuaJIT) if available for 5-15x speedup.
    Fires plugin pre_compile/post_compile hooks and syntax handlers."""
    from .debug import (
        trace,
        info,
    )
    trace("COMPILE", "Starting compilation")

    text = strip_comments(text)

    # v5 includes: inline `include "file.e"` (before version detection so
    # included content participates fully). base_dir comes from compile_file.
    if _has_v5_statement(text):
        try:
            from .mode_v5_statements import resolve_includes
            text = resolve_includes(text, base_dir=base_dir)
        except (ValueError, FileNotFoundError) as e:
            raise CompileError(str(e))
        except Exception:
            pass

    # v5 !fn macros (text-level definition collection).
    _v5_fns = {}
    if _has_v5_statement(text):
        try:
            from .mode_v5_statements import process_v5_pre
            text, _v5_fns = process_v5_pre(text)
        except Exception:
            pass

    # LURE fast path: if lupa + LuaJIT available, try Lua compilation first.
    # Skipped when v5-only statements are present — LURE cannot parse them.
    if not _has_v5_statement(text):
        try:
            from plugins.lure import get_engine
            engine = get_engine()
            if engine and engine.available:
                result = engine.compile_text(text, bpm or 120)
                if result:
                    events, bp = result
                    trace("COMPILE", f"LURE compiled: {len(events)} events, {bp} BPM")
                    try:
                        import ep_core
                        ep_core._last_compiled_events[:] = events
                        ep_core._compilation_count += 1
                    except ImportError:
                        pass
                    return events, bp
        except Exception:
            pass

    try:
        from ep_core import (
            trigger_event,
            _syntax_handlers,
            _last_compiled_events,
            _compilation_count,
        )
        results = trigger_event("pre_compile", text)
        if results:
            text = results[-1] or text
    except ImportError:
        _syntax_handlers = []

    config = parse_config_strip(text)
    ll_state = dict(DEFAULT_LL_STATE)
    ll_state = parse_directives(text, ll_state)
    if ll_state.get("seed") is not None:
        try:
            from plugins.lure.math_python import set_seed
            set_seed(ll_state["seed"])
        except Exception:
            pass
    auto_bpm = ll_state.get('bpm', 120)
    if bpm is None:
        bpm = auto_bpm

    version = detect_syntax_version(text)

    # First pass: only set up scope from pure-constant var defs.
    # Do NOT resolve {$expr} yet — that mutates line content and breaks loops.
    # compile_v1() handles expression resolution after loop unrolling.
    _math_scope = Scope()
    for _line in text.split("\n"):
        if is_var_definition(_line.strip()):
            _name, _expr = parse_var_definition(_line.strip())
            if '$' not in _expr:  # pure constant, no variable references
                _val, _err = evaluate_expression(_expr, None)
                if _val is not None:
                    _math_scope.set(_name, _val)

    if version in ('v3', 'v4', 'v5'):
        try:
            from .punctuation import expand_punctuation
            text = expand_punctuation(text)
        except ImportError:
            pass
        try:
            from .mode_v3_extended import preprocess_v3
            text = preprocess_v3(text)
        except ImportError:
            pass
        if version in ('v4', 'v5'):
            try:
                from .mode_v4_polyrhythm import process_polyrhythms
                text = process_polyrhythms(text, bpm)
            except Exception:
                pass
            try:
                from .mode_v5_performance import process_performance_pre
                text = process_performance_pre(text, bpm)
            except Exception:
                pass
        events, bp = compile_v1(text, bpm, ll_state, scope=_math_scope, strict=strict, v5_fns=_v5_fns)
        events = apply_scale_quantization(events, ll_state)
        events = apply_ll_controllers(events, ll_state)
        events = apply_performance_post_passes(events, text, bpm, ll_state)
        if strict:
            _raise_strict_if_problems()
        try:
            events = _run_post_compile_hooks(events, bp)
        except ImportError:
            pass
        return events, bp

    if version == 'v2':
        try:
            from .mode_v2_semantic import compile_v2
            events, bp = compile_v2(text)
            events = sort_events(events)
            events = apply_scale_quantization(events, ll_state)
            events = apply_ll_controllers(events, ll_state)
            events = apply_performance_post_passes(events, text, bpm, ll_state)
            return events, bp
        except ImportError:
            pass

    events, bp = compile_v1(text, bpm, ll_state, scope=_math_scope, strict=strict, v5_fns=_v5_fns)
    events = apply_scale_quantization(events, ll_state)
    events = apply_ll_controllers(events, ll_state)
    events = apply_performance_post_passes(events, text, bpm, ll_state)
    try:
        events = _run_post_compile_hooks(events, bp)
    except ImportError:
        pass

    if strict:
        _raise_strict_if_problems()

    try:
        import ep_core
        ep_core._last_compiled_events[:] = events
        ep_core._compilation_count += 1
    except ImportError:
        pass

    info("COMPILE", f"Compiled: {len(events)} events, {bp} BPM")
    return events, bp


def _run_post_compile_hooks(events, bp):
    """Run post_compile hooks in a feed-forward pipeline: each hook sees
    the previous hook's output, so plugins layer correctly (e.g. Humanize
    then Talisman culling). A hook returning None leaves events unchanged."""
    from ep_core import _event_hooks
    for cb in _event_hooks.get("post_compile", []):
        try:
            r = cb(events, bp)
        except Exception:
            continue
        if r is not None:
            events = r
    return events


def _raise_strict_if_problems():
    """Raise a CompileError listing every recorded diagnostic (fail-fast)."""
    from .mode_v1_machine import last_problems as _mlp
    from .mode_v1_human import last_problems as _hlp
    probs = list(_mlp) + list(_hlp)
    if probs:
        lines = "\n".join(
            f"  line {p['line']+1}, col {p['char']+1}: {p['code']} {p['message']}"
            for p in probs
        )
        raise CompileError(f"Strict compile failed with {len(probs)} problem(s):\n{lines}")


def compile_v1(text, bpm, ll_state, scope=None, strict=False, v5_fns=None):
    """Compile v1 (#MACHINE or #HUMAN) text to events.
    scope: optional Scope with variables from compile_source's preprocess_math."""
    from .mode_v1_human import parse_human_line as parse_human
    from .mode_v1_machine import parse_machine_line as parse_machine
    from .comments import strip_line
    from .debug import (
        trace,
        debug,
    )
    try:
        from ep_core import _syntax_handlers
    except ImportError:
        _syntax_handlers = []

    # Try LURE batch accelerator if available
    lure_engine = None
    try:
        from plugins.lure import get_engine
        lure_engine = get_engine()
    except ImportError:
        pass

    events = []
    cursor = 0
    all_lines = text.split('\n')

    # Strip comments and filter
    clean_lines = []
    line_indices = []
    for i, line in enumerate(all_lines):
        l = strip_line(line).strip()
        if not l or (l.startswith('#') and not l.startswith('#compiler')):
            continue
        clean_lines.append(l)
        line_indices.append(i)
        trace("COMPILE", f"Line {i}: {l[:80]}")

    # Loop unrolling + math preprocessing on clean lines
    # Inherit variables from compile_source's preprocess_math (if passed)
    loop_scope = scope if scope else Scope()
    _v5_stats_marker = False
    try:
        new_lines = detect_and_unroll_loops(clean_lines, lambda v: loop_scope.get(v))
        new_lines = preprocess_math(new_lines, loop_scope)
        # v5 statement pass: print / assert / prog / perc / !fn uses
        # (post-unroll so loop variables and $vars are resolved; print fires
        # per iteration). Math is re-run so !fn body expressions resolve.
        try:
            from .mode_v5_statements import process_v5_lines
            new_lines, printed = process_v5_lines(new_lines, bpm, ll_state, v5_fns)
            _v5_stats_marker = any(isinstance(m, tuple) and m[0] == "__stats__" for m in printed)
            for _msg in printed:
                if isinstance(_msg, tuple) and _msg[0] == "__stats__":
                    continue  # emitted after parsing, with real event stats
                print(f"  [v5] {_msg}")
            new_lines = preprocess_math(new_lines, loop_scope)
        except ImportError:
            pass
        except (AssertionError, ValueError, FileNotFoundError) as _e:
            # Explicit user errors (assert failed, unknown perc, missing
            # include) are hard failures — never silently swallowed.
            raise
        except Exception as _e:
            if strict:
                raise
            print(f"  [v5 ERROR] {_e}", flush=True)
        clean_lines = new_lines
    except (AssertionError, ValueError, FileNotFoundError):
        # Explicit user errors (assert failed, unknown perc, missing include,
        # bad loop form) are hard failures — never silently swallowed.
        raise
    except Exception as _e:
        # Surface loop/parse errors as diagnostics (lenient compile continues)
        try:
            from .mode_v1_machine import last_problems as _mlp
            from .syntax_check import _mk as _diag_mk
            _mlp.append(_diag_mk("E136", 0, 0, 1, f"Loop expansion error: {_e}"))
        except Exception:
            pass
        if strict:
            raise
        print(f"  [COMPILE ERROR] {_e}", flush=True)

    # LURE batch fast path: send all clean lines to LuaJIT for parsing
    lure_results = None
    if lure_engine and lure_engine.available and len(clean_lines) > 10:
        try:
            lure_results = lure_engine.parse_lines_batch(clean_lines)
        except Exception:
            pass

    # Process results (LURE or Python fallback)
    for idx, line in enumerate(clean_lines):
        ev = None
        ev_list = None

        # Try LURE result first
        if lure_results and idx < len(lure_results):
            lure_result = lure_results[idx]
            if lure_result:
                # Chord expansion
                if "_chord_intervals" in lure_result:
                    root = lure_result["_chord_root"]
                    intervals = lure_result["_chord_intervals"]
                    for interval in intervals:
                        chord_ev = dict(lure_result)
                        chord_ev["timestamp"] += cursor
                        chord_ev["midi"] = root + interval
                        chord_ev.pop("_chord_root", None)
                        chord_ev.pop("_chord_intervals", None)
                        events.append(chord_ev)
                    end_ts = max(e["timestamp"] + e["duration"] for e in events[-len(intervals):])
                    if end_ts > cursor: cursor = end_ts
                    continue
                # Single event
                ev = lure_result
                # Machine-mode lines have absolute timestamps (T<N> pattern)
                # Human-mode lines need cursor offset
                if not line.lstrip().startswith("T"):
                    ev["timestamp"] += cursor

        # Python fallback
        if not ev:
            # v5 performance statements first (pedal/rest/tuplets) so the
            # machine parser never mis-reports them (E051) into diagnostics.
            try:
                from .mode_v5_performance import parse_performance_line
                ev_list, new_cursor = parse_performance_line(line, cursor, bpm, ll_state)
                if ev_list is not None or new_cursor > cursor:
                    if ev_list:
                        events.extend(ev_list)
                    cursor = new_cursor
                    debug("COMPILE", f"Performance parsed: {line[:40]}")
                    continue
            except Exception:
                pass
        if not ev:
            ev = parse_machine(line, ll_state)
        if ev:
            events.append(ev)
            end = ev["timestamp"] + ev["duration"]
            if end > cursor:
                cursor = end
            debug("COMPILE", f"Machine parsed: T{ev['timestamp']} N{ev['midi']} D{ev['duration']} V{ev['velocity']}")
            continue

        if not ev_list:
            ev_list, new_cursor = parse_human(line, cursor, bpm, ll_state)
        if ev_list:
            events.extend(ev_list)
            cursor = new_cursor
            debug("COMPILE", f"Human parsed: {len(ev_list)} events, cursor={cursor}")
            continue

        for handler in _syntax_handlers:
            try:
                ev = handler(line, ll_state)
                if ev:
                    events.append(ev)
                    end = ev["timestamp"] + ev["duration"]
                    if end > cursor:
                        cursor = end
                    debug("COMPILE", f"Plugin syntax: {line[:40]}")
                    break
            except Exception:
                continue

        if not ev and not ev_list:
            debug("COMPILE", f"Unparseable line: {line[:60]}", "WARN")

    events = sort_events(events)
    events, _ = validate_events(events)
    if _v5_stats_marker:
        notes = [e for e in events if not e.get("pedal")]
        if notes:
            lo = min(n["midi"] for n in notes)
            hi = max(n["midi"] for n in notes)
            from .events import midi_to_name
            total = max((e["timestamp"] + e["duration"] for e in events), default=0)
            print(f"  [v5] {len(notes)} notes, {midi_to_name(lo)}-{midi_to_name(hi)}, "
                  f"{total/1000:.1f}s")
    trace("COMPILE", f"Compilation complete: {len(events)} events")
    return events, bpm


def compile_eci(text, bpm=None):
    from .mode_eci import compile_eci as _eci
    return _eci(text, bpm or 120)


def compile_ei_file(path, bpm_override=None):
    from .e_runtime import compile_ei_file as _ei
    try:
        _graph.enter(path)
        return _ei(path, bpm_override)
    except CircularReferenceError:
        raise
    finally:
        _graph.exit()


def compile_enx(path, bpm_override=None, graph=None):
    from .mode_enx import compile_enx as _enx
    g = graph or _graph
    try:
        g.enter(path)
        return _enx(path, bpm_override, graph=g)
    except CircularReferenceError:
        raise
    finally:
        g.exit()


def compile_file(path, bpm_override=None, strict=False):
    _graph.reset()
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == ".enx":
            return compile_enx(path, bpm_override)
        elif ext == ".ei":
            return compile_ei_file(path, bpm_override)
        elif ext == ".eci":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return compile_eci(text, bpm_override)
        elif ext in (".e", ".eic"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
            return compile_source(text, bpm_override, strict=strict, base_dir=os.path.dirname(path))
        else:
            return [], 120
    except CircularReferenceError as e:
        print(f"  {chr(27)}[91m\xd7 {e}{chr(27)}[0m")
        return [], 120
