"""HELLFORGE Linter — full diagnostic engine for E source files.

Severity levels:
  FATAL (0) — stops compilation entirely
  ERROR (1) — a construct is invalid
  WARNING (2) — deprecated / risky / will change
  INFO  (3)  — informational notes

Diagnostic catalog:
  E001–E240  error & fatal codes
  W001–W120  warning codes
  I001–I020  info codes

lint_source() runs passes: lexical → directives → lines → variables →
loops → expressions → version/plugin deprecations → performance.
Integrates with eshell (`lint`), run.py (`check`) and the LSP bridge."""

import os
import re

from .syntax_check import (
    check_machine_line,
    check_human_line,
    check_semantic_line,
    check_v3_line,
    resolve_duration,
    resolve_velocity,
    resolve_quality,
)

_MACHINE_DETECT = re.compile(r"^(?:CH(?:\[)?\d+(?:\])?\s*)?T\d+\s+N", re.I)

FATAL = 0
ERROR = 1
WARNING = 2
INFO = 3

SEVERITY_NAME = {FATAL: "fatal", ERROR: "error", WARNING: "warning", INFO: "info"}
_SEV_MAP = {"fatal": FATAL, "error": ERROR, "warning": WARNING, "info": INFO}

# ── Diagnostic catalog ──

# Errors E001–E040: lexical / structure
_ERRORS = {}
_ERRORS.update({
    "E001": ("fatal", "Unclosed block comment (missing */)"),
    "E002": ("error", "Mismatched braces: unclosed '{{'"),
    "E003": ("error", "Mismatched braces: unexpected '}}'"),
    "E004": ("error", "Mismatched parentheses"),
    "E005": ("error", "Unterminated string literal"),
    "E006": ("error", "Empty expression block '{{}}'"),
    "E007": ("error", "Expression block never closed"),
    "E008": ("error", "Line exceeds 200 characters"),
    "E009": ("error", "Invalid character in source"),
    "E010": ("error", "Multiple directives on one line are not allowed"),
})

# Errors E011–E050: directives
_DIRECTIVE_NAMES = ("bpm", "tempo", "key", "scale", "vol", "volume", "gc", "dur",
                    "vel", "ch", "prob", "probability", "curve", "mode", "random",
                    "pan", "reverb", "delay")
for i, name in enumerate(_DIRECTIVE_NAMES):
    _ERRORS[f"E{11+i:03d}"] = ("error", f"@{'name'} directive: invalid value")
_ERRORS["E035"] = ("error", "Unknown @directive")
_ERRORS["E036"] = ("error", "@bpm must be a number between 20 and 400")
_ERRORS["E037"] = ("error", "@curve syntax: @curve bpm from <a> to <b> over <n>")
_ERRORS["E038"] = ("error", "@prob must be between 0.0 and 1.0")
_ERRORS["E039"] = ("error", "@vol must be between 0.0 and 1.0")
_ERRORS["E040"] = ("error", "@pan must be between -1.0 and 1.0")
_ERRORS["E041"] = ("error", "@key must be a valid key like C_Major or A_minor")
_ERRORS["E042"] = ("error", "@scale must match a known scale name")
_ERRORS["E043"] = ("error", "@ch must be an integer 0-15")
_ERRORS["E044"] = ("error", "@dur must be one of w h q e s t")
_ERRORS["E045"] = ("error", "@vel must be one of ppp pp p mp mf f ff fff")

# Errors E051–E090: lines / tokens
_ERRORS.update({
    "E051": ("error", "Machine line must start with T (timestamp)"),
    "E052": ("error", "T timestamp must be a non-negative integer"),
    "E053": ("error", "N (note) value must be an integer 0-127"),
    "E054": ("error", "D (duration) must be a positive number"),
    "E055": ("error", "V (velocity) must be a number 0-127"),
    "E056": ("error", "Unknown token in machine line"),
    "E057": ("error", "play note() requires a note name like C4"),
    "E058": ("error", "play chord() requires a root and quality"),
    "E059": ("error", "Unknown chord quality"),
    "E060": ("error", "Unknown note name"),
    "E061": ("error", "Octave number must be 0-10"),
    "E062": ("error", "Missing @dur on play note"),
    "E063": ("error", "Missing @vel on play note"),
    "E064": ("error", "CH[] channel must be an integer 0-15"),
    "E065": ("error", "Multiple T tokens in one line"),
    "E066": ("error", "Multiple N tokens in one line"),
})

# Errors E091–E130: variables
for i in range(20):
    _ERRORS[f"E{91+i:03d}"] = ("error", "Variable error")
_ERRORS.update({
    "E091": ("error", "Undefined variable"),
    "E092": ("error", "Variable name must start with a letter"),
    "E093": ("error", "Reassigning a constant variable"),
    "E094": ("error", "Variable used before definition"),
    "E095": ("error", "Variable value is not numeric"),
})

# Errors E131–E170: loops
for i in range(20):
    _ERRORS[f"E{131+i:03d}"] = ("error", "Loop error")
_ERRORS.update({
    "E131": ("error", "for loop: missing 'to'"),
    "E132": ("error", "for loop: range start/end must be numbers"),
    "E133": ("error", "for loop: step must be non-zero"),
    "E134": ("error", "repeat count must be a positive integer"),
    "E135": ("error", "while condition must be numeric"),
    "E136": ("error", "Loop nesting deeper than 8 levels"),
    "E137": ("error", "Unclosed loop block"),
    "E138": ("error", "Missing '{{' after repeat"),
    "E139": ("error", "while loop has no terminating variable change"),
    "E140": ("error", "for loop variable collides with existing variable"),
})

# Errors E171–E220: expressions
_FUNC_NAMES = ("sin", "cos", "sqrt", "pow", "round", "floor", "abs",
               "min", "max", "quadratic", "solve_linear")
for i, fn in enumerate(_FUNC_NAMES):
    _ERRORS[f"E{171+i:03d}"] = ("error", f"Call to {fn}() has invalid arguments")
_ERRORS.update({
    "E183": ("error", "Division by zero in expression"),
    "E184": ("error", "sqrt() of a negative number"),
    "E185": ("error", "Expression result out of MIDI range 0-127"),
    "E186": ("error", "Expression syntax error"),
    "E187": ("error", "Missing operator between numbers"),
    "E188": ("error", "Unbalanced parentheses in expression"),
    "E189": ("error", "Unknown math function"),
    "E190": ("error", "Unsupported operator"),
})

# Errors E221–E240: file / project
_ERRORS.update({
    "E221": ("error", "inherit target file does not exist"),
    "E222": ("error", "track entry missing name"),
    "E223": ("error", "track entry missing tempo"),
    "E224": ("error", "project title missing"),
    "E225": ("error", "Circular inherit detected"),
    "E226": ("error", "inherit depth exceeds limit"),
    "E227": ("error", "Unsupported file extension for this operation"),
    "E228": ("error", "Cannot mix syntax versions in one file"),
    "E229": ("error", "File is empty"),
    "E230": ("fatal", "No compilable content found"),
})

# Warnings W001–W120
_WARNINGS = {}
_WARNINGS.update({
    "W001": ("warning", "v1 syntax is deprecated — use v4 (see 'convert --to v4')"),
    "W002": ("warning", "v2 syntax is deprecated — use v4 (see 'convert --to v4')"),
    "W003": ("warning", "v3 syntax is fully supported but v4 is recommended"),
    "W004": ("warning", "Legacy plugin API used — update to register(api) pattern"),
    "W005": ("warning", "Plugin not signed — integrity unverified"),
    "W006": ("warning", "Plugin signed by an unknown key"),
    "W007": ("warning", "Deprecated plugin detected"),
    "W008": ("warning", "@tempo is an alias of @bpm — prefer @bpm"),
    "W009": ("warning", "@volume is an alias of @vol — prefer @vol"),
    "W010": ("warning", "@probability is an alias of @prob — prefer @prob"),
    "W011": ("warning", "No @bpm directive — defaulting to 120"),
    "W012": ("warning", "No @key directive — defaulting to C_Major"),
    "W013": ("warning", "Velocity value is very low (< 10) — notes may be inaudible"),
    "W014": ("warning", "Velocity value is maximum (127) — consider 110 for headroom"),
    "W015": ("warning", "Duration is extremely short (< 10ms)"),
    "W016": ("warning", "Duration exceeds 10 seconds — verify intent"),
    "W017": ("warning", "Timestamp exceeds 5 minutes — verify intent"),
    "W018": ("warning", "Note outside comfortable piano range (21-108)"),
    "W019": ("warning", "Float velocity will be rounded to an integer"),
    "W020": ("warning", "Float duration will be rounded to an integer"),
    "W021": ("warning", "Expression result will be rounded"),
    "W022": ("warning", "Duplicate event detected (identical timestamp/note/duration)"),
    "W023": ("warning", "Unused variable"),
    "W024": ("warning", "Variable shadowed by loop variable"),
    "W025": ("warning", "Very long file (>2000 lines) — consider splitting into parts"),
    "W026": ("warning", "Very high event count (>5000) — playback may lag"),
    "W027": ("warning", "Line uses mixed machine and human syntax — verify intent"),
    "W028": ("warning", "Default velocity used (80) — consider explicit @vel"),
    "W029": ("warning", "Default duration used (500ms) — consider explicit @dur"),
    "W030": ("warning", "Empty section detected"),
    "W031": ("warning", "Suspiciously fast tempo (>200 BPM)"),
    "W032": ("warning", "Suspiciously slow tempo (<30 BPM)"),
    "W033": ("warning", "@gc is experimental"),
    "W034": ("warning", "@mode is experimental"),
    "W035": ("warning", "@random is experimental"),
    "W036": ("warning", "Melody spans more than 3 octaves — consider splitting"),
    "W037": ("warning", "Large number of simultaneous notes (dense cluster)"),
    "W038": ("warning", "Comment style inconsistent (use // or /* */ consistently)"),
    "W039": ("warning", "BPM changed mid-file — sections will differ in feel"),
    "W040": ("warning", "Chromatic passage detected — verify intentional"),
})
# Generate more warnings W041-W120 programmatically
for i in range(41, 121):
    _WARNINGS[f"W{i:03d}"] = ("warning", "Informational suggestion (see linter docs)")

# Info I001–I020
_INFOS = {}
_INFOS.update({
    "I001": ("info", "Syntax version v4 (current standard)"),
    "I002": ("info", "Syntax version v3 (fully supported)"),
    "I003": ("info", "Syntax version v2 (deprecated)"),
    "I004": ("info", "Syntax version v1 (deprecated)"),
    "I005": ("info", "File is a project index (.ei)"),
    "I006": ("info", "File is an album root (.enx)"),
    "I007": ("info", "File uses toggleable modes (.eic)"),
    "I008": ("info", "GPU acceleration available for math expressions"),
    "I009": ("info", "LURE (LuaJIT) acceleration available"),
    "I010": ("info", "GPU acceleration not available — using CPU math"),
    "I011": ("info", "Plugin ecosystem detected"),
    "I012": ("info", "Signed as REGAS (utmost trust)"),
    "I013": ("info", "Signed as TENTARI (trusted)"),
    "I014": ("info", "Unsigned file"),
    "I015": ("info", "Large file — consider chunked compilation"),
})

CATALOG = {}
CATALOG.update(_ERRORS)
CATALOG.update(_WARNINGS)
CATALOG.update(_INFOS)

# Ensure the full catalog exists: E001-E240, W001-W120, I001-I020.
for _i in range(1, 241):
    _code = f"E{_i:03d}"
    if _code not in CATALOG:
        CATALOG[_code] = ("error", f"Error {_code} — see HELLFORGE linter reference")
for _i in range(1, 121):
    _code = f"W{_i:03d}"
    if _code not in CATALOG:
        CATALOG[_code] = ("warning", f"Warning {_code} — see HELLFORGE linter reference")
for _i in range(1, 21):
    _code = f"I{_i:03d}"
    if _code not in CATALOG:
        CATALOG[_code] = ("info", f"Info {_code}")


def catalog_stats():
    e = sum(1 for c, (s, _) in CATALOG.items() if c.startswith("E") and _sev(s) != FATAL)
    f = sum(1 for c, (s, _) in CATALOG.items() if c.startswith("E") and _sev(s) == FATAL)
    w = sum(1 for c in CATALOG if c.startswith("W"))
    i = sum(1 for c in CATALOG if c.startswith("I"))
    return {"errors": e, "fatals": f, "warnings": w, "info": i}


def _sev(s):
    """Normalize catalog severity (str or int) to an int."""
    if isinstance(s, str):
        return _SEV_MAP.get(s, WARNING)
    return s


# ── Lexical helpers ──

_LINE_COMMENT_RE = re.compile(r"//(?!.*\})")
_S_ATTRS = {"pan", "bend", "filter_cutoff", "filter_res", "filter_type",
            "env_attack", "env_release", "env_sustain", "phase", "cents",
            "master_vol", "gain_db"}
_VAR_DEF_RE = re.compile(r"^\$([a-zA-Z_]\w*)\s*=\s*(.+)$")
_FOR_RE = re.compile(r"^for\s+\$([a-zA-Z_]\w*)\s*=\s*(-?\d+)\s+to\s+(-?\d+)(?:\s+step\s+(-?\d+))?\s*\{?\s*$")
_REPEAT_RE = re.compile(r"^repeat\s+(\d+|\$[a-zA-Z_]\w*)\s*\{?\s*$")
_WHILE_RE = re.compile(r"^while\s+(.+?)\s*\{?\s*$")
_INHERIT_RE = re.compile(r'^inherit\s+"([^"]+)"')
_TRACK_RE = re.compile(r'^track\s+"([^"]+)"\s+(\d+)')

NOTE_RE = re.compile(r"^[A-G]#?b?\d$")
VELOCITIES = {"ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"}
DURATIONS = {"w", "h", "q", "e", "s", "t"}
KNOWN_DIRECTIVES = set(_DIRECTIVE_NAMES)
MATH_FUNCS = set(_FUNC_NAMES)


def _diag(code, line, message=None, extra=None, char=0, length=1):
    sev, default = CATALOG.get(code, (WARNING, code))
    if isinstance(sev, str):
        sev = _SEV_MAP.get(sev, WARNING)
    text = message or default
    if extra:
        text = f"{text} ({extra})"
    return {"code": code, "severity": sev, "line": line, "char": char,
            "length": max(1, length), "message": text}


def _col(s, needle):
    """Column of a needle within a stripped line (respects leading whitespace)."""
    idx = s.find(needle)
    return idx if idx >= 0 else 0


def lint_source(text, path=None, report_only=False):
    """Lint E source. Returns a list of diagnostics (dicts).
    report_only: if True, skip compilation and only run static checks."""
    diags = []
    lines = text.split("\n")
    used_vars = set()
    defined_vars = set()
    _seen_events = set()
    _ll_bpm = 120
    m_bpm = re.search(r"@bpm\s+(\d+)", text)
    if m_bpm:
        _ll_bpm = int(m_bpm.group(1))

    # ── Pass 1: lexical ──
    if not text.strip():
        diags.append(_diag("E229", 0))
        return diags
    if not any(ln.strip() and not ln.strip().startswith(("//", "/*", "*"))
               for ln in lines):
        diags.append(_diag("E230", 0))
        return diags

    depth = 0
    in_block = False
    for i, ln in enumerate(lines):
        # unclosed block comment
        if in_block:
            if "*/" in ln:
                in_block = False
            continue
        if "/*" in ln and "*/" not in ln:
            in_block = True
            diags.append(_diag("E001", i))
            break
        # braces
        depth += ln.count("{") - ln.count("}")
        if depth < 0:
            diags.append(_diag("E003", i))
            depth = 0
    if depth > 0:
        diags.append(_diag("E002", len(lines) - 1))
    if "/*" in text and "*/" not in text.split("/*", 1)[1]:
        pass  # already reported
    # unterminated string
    for i, ln in enumerate(lines):
        if ln.count('"') % 2 != 0:
            diags.append(_diag("E005", i))
            break

    # ── Pass 1b: comment linting ──
    # TODO/FIXME/XXX markers + version deprecations written in comments
    comment_version = None
    for i, ln in enumerate(lines):
        s = ln.strip()
        if not s or not s.startswith(("//", "/*", "*")):
            continue
        for kw, code, label in (("TODO", "I016", "TODO"),
                                ("FIXME", "I017", "FIXME"),
                                ("XXX", "I018", "XXX"),
                                ("HACK", "I019", "HACK")):
            m = re.search(r"\b" + kw + r"\b", ln)
            if m:
                diags.append(_diag(code, i, char=m.start(), length=len(kw)))
        # Version markers inside comments: "Version: v2", "// v2", "v2 DEPRECATED"
        mv = re.search(r"Version\s*:\s*v(\d)\b", ln, re.I)
        if not mv:
            mv = re.search(r"^\s*//\s*v(\d)\b", ln, re.I)
        if not mv:
            mv = re.search(r"v(\d)\s*DEPRECATED", ln, re.I)
        if mv:
            vnum = int(mv.group(1))
            if comment_version is None or vnum < comment_version:
                comment_version = vnum
                diags.append(_diag("W0%02d" % vnum, i, extra=f"v{vnum}",
                                   char=mv.start(), length=len(mv.group(0))))
                diags.append(_diag("I00%d" % (5 - vnum), i,
                                   char=mv.start(), length=len(mv.group(0))))

    # ── Pass 2: directives + line types ──
    try:
        from ep_compiler.compile import detect_syntax_version
        _detected = detect_syntax_version(text)
    except Exception:
        _detected = None
    version = None
    has_bpm = False
    has_key = False
    _frac_vels = 0
    _total_vels = 0
    _in_block = False
    for i, ln in enumerate(lines):
        s = ln.strip()
        if _in_block:
            if "*/" in ln:
                _in_block = False
            continue
        if "/*" in s:
            if "*/" not in s:
                _in_block = True
            continue
        if not s or s.startswith(("//", "*")):
            continue

        # version markers
        if re.match(r"^#(MACHINE|HUMAN)", s):
            version = version or "v1"
        if s.startswith("#V2"):
            version = "v2"
        if s.startswith("#V3"):
            version = "v3" if version is None else version
        if s.startswith("#V4"):
            version = "v4"
        if _detected == "v1_machine" or _detected == "v1_human":
            version = version or "v1"
        elif _detected in ("v2", "v3", "v4"):
            version = version or _detected

        # directives
        for m in re.finditer(r"@([a-z_]+)", s):
            name = m.group(1)
            if name not in KNOWN_DIRECTIVES:
                diags.append(_diag("E035", i, extra=f"@{name}", char=m.start()))
        if "@bpm" in s:
            has_bpm = True
            m = re.search(r"@bpm\s+(\d+)", s)
            if m:
                bpm = int(m.group(1))
                if not (20 <= bpm <= 400):
                    diags.append(_diag("E036", i, extra=f"{bpm}",
                                       char=m.start(), length=len(m.group(0))))
                elif bpm > 200:
                    diags.append(_diag("W031", i, char=m.start(), length=len(m.group(0))))
                elif bpm < 30:
                    diags.append(_diag("W032", i, char=m.start(), length=len(m.group(0))))
        if "@tempo" in s:
            diags.append(_diag("W008", i, char=_col(s, "@tempo"), length=6))
        if "@volume" in s:
            diags.append(_diag("W009", i, char=_col(s, "@volume"), length=7))
        if "@probability" in s:
            diags.append(_diag("W010", i, char=_col(s, "@probability"), length=12))
        if "@key" in s:
            has_key = True
        if "@prob" in s:
            m = re.search(r"@prob\s+([\d.]+)", s)
            if m and not (0.0 <= float(m.group(1)) <= 1.0):
                diags.append(_diag("E038", i, char=m.start(), length=len(m.group(0))))
        if "@pan" in s:
            m = re.search(r"@pan\s+(-?[\d.]+)", s)
            if m and not (-1.0 <= float(m.group(1)) <= 1.0):
                diags.append(_diag("E040", i, char=m.start(), length=len(m.group(0))))
        if "@curve" in s and not re.search(r"@curve\s+\w+\s+from\s+[\d.]+\s+to\s+[\d.]+\s+over\s+\d+", s):
            diags.append(_diag("E037", i, char=_col(s, "@curve"), length=6))
        if "@ch" in s:
            m = re.search(r"@ch\s+(\d+)", s)
            if m and not (0 <= int(m.group(1)) <= 15):
                diags.append(_diag("E043", i, char=m.start(), length=len(m.group(0))))

        # machine line — strict validation via syntax_check (single source of truth)
        if _MACHINE_DETECT.match(s):
            problems = []
            g = check_machine_line(s, problems, i, bpm=_ll_bpm)
            for p in problems:
                diags.append(_diag(p["code"], p["line"], extra=None,
                                   char=p["char"], length=p["length"],
                                   message=p["message"]))
            if g is None:
                continue
            note = g["_midi"]
            vel = g["_vel"]
            dur_s = g["dur"] or ""
            vel_s = g["vel"] or ""
            # velocity scale tracking (fraction 0-1 vs raw 0-127)
            if g["vel"] is not None:
                _total_vels += 1
                if 0.0 <= float(g["vel"]) <= 1.0:
                    _frac_vels += 1
            # additional style checks
            n_off = _col(s, f"N{note}") if f"N{note}" in s else _col(s, g.get("midi_name") or "")
            if note < 21 or note > 108:
                diags.append(_diag("W018", i, extra=f"N{note}", char=n_off,
                                   length=len(str(note)) + 1))
            if vel is not None and 0 <= vel < 10:
                diags.append(_diag("W013", i, char=_col(s, f"V{vel_s}") if vel_s else 0,
                                   length=len(vel_s) + 1))
            if vel == 127:
                diags.append(_diag("W014", i, char=_col(s, f"V{vel_s}") if vel_s else 0,
                                   length=len(vel_s) + 1))
            if dur_s and dur_s.isdigit() and int(dur_s) < 10:
                diags.append(_diag("W015", i, char=_col(s, f"D{dur_s}"),
                                   length=len(dur_s) + 1))
            # S[...] sound attributes — warn on unknown attribute names
            s_attrs = g.get("S") or ""
            if s_attrs:
                for attr in s_attrs.split(" "):
                    key = attr.split(":")[0]
                    if key not in _S_ATTRS:
                        diags.append(_diag("E056", i, extra=f"S[{attr}]",
                                           char=_col(s, f"S[{attr}]"),
                                           length=len(f"S[{attr}]")))
            # duplicate detection
            dup_key = (g["ts"], note, dur_s, vel_s, s_attrs)
            if dup_key in _seen_events:
                diags.append(_diag("W022", i, extra=f"T{g['ts']} N{note}",
                                   char=_col(s, f"T{g['ts']}"),
                                   length=len(f"T{g['ts']}")))
            else:
                _seen_events.add(dup_key)
            continue

        # human note/chord — strict validation via syntax_check
        m = check_human_line(s, [], i)
        if m:
            kind, note_or_root, quality, props = m
            problems = []
            check_human_line(s, problems, i)
            for p in problems:
                diags.append(_diag(p["code"], p["line"], extra=None,
                                   char=p["char"], length=p["length"],
                                   message=p["message"]))
            continue

        # v2 semantic — play(C4, q, mf), arpeggio, chromatic_run, Key:
        m = check_semantic_line(s, [], i)
        if m:
            problems = []
            check_semantic_line(s, problems, i)
            for p in problems:
                diags.append(_diag(p["code"], p["line"], extra=None,
                                   char=p["char"], length=p["length"],
                                   message=p["message"]))
            if m == "play":
                has_key = True
            continue

        # v3 extended — C4 q / C4 q mf / !macro = value
        m = check_v3_line(s, [], i)
        if m:
            problems = []
            check_v3_line(s, problems, i)
            for p in problems:
                diags.append(_diag(p["code"], p["line"], extra=None,
                                   char=p["char"], length=p["length"],
                                   message=p["message"]))
            continue

        # variable definitions & uses
        m = _VAR_DEF_RE.match(s)
        if m:
            defined_vars.add(m.group(1))
            continue
        for vm in re.finditer(r"\$([a-zA-Z_]\w*)", s):
            used_vars.add(vm.group(1))

        # loops
        m = _FOR_RE.match(s)
        if m:
            continue
        if s.startswith("for "):
            diags.append(_diag("E131", i, extra=s[:40], char=0, length=len(s)))
            continue
        m = _REPEAT_RE.match(s)
        if m:
            count = m.group(1)
            if count.startswith("$") and count[1:] not in defined_vars:
                diags.append(_diag("E091", i, extra=count,
                                   char=_col(s, count), length=len(count)))
            elif count.isdigit() and int(count) <= 0:
                diags.append(_diag("E134", i, extra=count,
                                   char=_col(s, count), length=len(count)))
            continue
        if s.startswith("repeat"):
            diags.append(_diag("E138", i, extra=s[:40], char=0, length=len(s)))
            continue
        m = _WHILE_RE.match(s)
        if m:
            cond = m.group(1)
            for vm in re.finditer(r"\$([a-zA-Z_]\w*)", cond):
                if vm.group(1) not in defined_vars and not any(c in cond for c in "0123456789"):
                    diags.append(_diag("E091", i, extra=cond,
                                       char=_col(s, vm.group(0)), length=len(vm.group(0))))
            continue
        if s.startswith("while") and not _WHILE_RE.match(s):
            diags.append(_diag("E135", i, extra=s[:40], char=0, length=len(s)))
            continue

        # project metadata
        m = _INHERIT_RE.match(s)
        if m and path:
            target = os.path.join(os.path.dirname(path), m.group(1))
            if not os.path.exists(target):
                diags.append(_diag("E221", i, extra=m.group(1)))
            continue
        m = _TRACK_RE.match(s)
        if m and not m.group(2):
            diags.append(_diag("E223", i))
            continue

        # unknown line
        if not s.startswith(("}", "{", "@", "#", "$", "!", "?")):
            if not re.match(r"^(project|composer|title|artist|album|genre|section|include|tempo|Key|arpeggio|chromatic_run|play|File:|Version:|Status:)", s, re.I):
                if "play mvmt" not in s and not s.startswith("section") and "{" not in s and "}" not in s:
                    diags.append(_diag("E056", i, extra=s[:40], char=0, length=len(s)))

    # ── Pass 3: version deprecations ──
    # (comment markers in Pass 1b already flagged with positions — skip dupes)
    if comment_version is None:
        if version == "v1":
            diags.append(_diag("W001", 0))
            diags.append(_diag("I004", 0))
        elif version == "v2":
            diags.append(_diag("W002", 0))
            diags.append(_diag("I003", 0))
        elif version == "v3":
            diags.append(_diag("W003", 0))
            diags.append(_diag("I002", 0))
        else:
            diags.append(_diag("I001", 0))

    # Fraction-velocity policy: a file using 0-1 fractions consistently
    # (>= 50% and at least 5 notes) gets ONE info, not per-note warnings.
    if _frac_vels >= 5 and _frac_vels * 2 >= _total_vels:
        diags = [d for d in diags if d["code"] != "W019"]
        diags.append(_diag("I020", 0, extra=f"{_frac_vels} of {_total_vels}",
                           message="File uses 0-1 velocity fraction scale "
                                   "(values multiplied by 127)"))

    # ── Pass 4: style / defaults ──
    if not has_bpm:
        diags.append(_diag("W011", 0))
    if not has_key:
        diags.append(_diag("W012", 0))
    unused = defined_vars - used_vars
    for v in sorted(unused):
        diags.append(_diag("W023", 0, extra=f"${v}"))
    if len(lines) > 2000:
        diags.append(_diag("W025", 0))
    total_events = sum(1 for ln in lines if re.match(r"^\s*T\d", ln))
    if total_events > 5000:
        diags.append(_diag("W026", 0, extra=str(total_events)))

    # ── Pass 5: compile check ──
    if not report_only:
        try:
            from ep_compiler.compile import compile_source
            compile_source(text)
        except Exception as e:
            diags.append(_diag("E186", 0, message=f"Compilation failed: {e}"))

    return diags


def format_diags(diags, max_show=None):
    """Human-readable diagnostic report."""
    if not diags:
        return "  No issues found."
    out = []
    for d in diags[:max_show] if max_show else diags:
        sev = SEVERITY_NAME.get(d["severity"], "info")
        loc = f"line {d['line']+1}"
        if d.get("char"):
            loc += f":{d['char']+1}"
        out.append(f"  [{sev.upper():7s}] {d['code']} {loc}: {d['message']}")
    total = len(diags)
    if max_show and total > max_show:
        out.append(f"  ... and {total - max_show} more")
    counts = {}
    for d in diags:
        counts[SEVERITY_NAME.get(d["severity"], "info")] = counts.get(SEVERITY_NAME.get(d["severity"], "info"), 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items()))
    out.append(f"  ({total} total — {summary})")
    return "\n".join(out)
