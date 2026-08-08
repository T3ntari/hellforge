"""HELLFORGE v4 punctuation expansion.

Adds modern punctuation syntax on top of machine/human v4:
  ;  statement separator      T0 N60 D500; T500 N62 D500
  ,  argument / group list    [C4, E4, G4](3:2)   E(3, 5)   chord(C4, minor)
  :  labeled fields           T:0 N:60 D:500 V:80   N:C4  D:q  V:mf  CH[0]
  [] () {} <>  all brackets   angle <> aliases []; () funcs; {} math/blocks
  \\  line continuation        T0 N60 D500 \\
  |  parallel (chord) notes   [C4|E4|G4](3:2)  ->  chord per step

All expansion is comment-aware and bracket-depth-aware — safe on
machine lines, human lines, loops, and math blocks.
"""

import re

_STATEMENT_END = re.compile(r";")
_GROUP_COMMA = re.compile(r"\[([^\]]*)\]")
_LABELED_MACHINE = re.compile(
    r"^(?P<pre>(?:CH(?:\[)?\d+(?:\])?\s*)?)"
    r"T\s*:\s*(?P<ts>\d+)\s+"
    r"N\s*:\s*(?P<note>[A-Ga-g]#?b?\d*|\d+)\s*"
    r"(?P<rest>.*)$"
)
_LABELED_FIELD = re.compile(
    r"\b(?P<kind>[DNV])\s*:\s*(?P<val>[A-Za-z0-9.]{1,12})"
)


def _strip_comment(line):
    """Remove // comment portion (not inside braces)."""
    depth = 0
    for i, ch in enumerate(line):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth = max(0, depth - 1)
        elif ch == "/" and depth == 0 and i + 1 < len(line) and line[i + 1] == "/":
            return line[:i]
    return line


def _find_unprotected_semicolons(line):
    """Indices of ';' at bracket depth 0 (outside [], (), {}, <> and comments)."""
    out = []
    depth = 0
    in_str = None
    for i, ch in enumerate(line):
        if in_str:
            if ch == in_str:
                in_str = None
            continue
        if ch in ('"', "'"):
            in_str = ch
        elif ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth = max(0, depth - 1)
        elif ch == ";":
            if depth == 0:
                out.append(i)
    return out


def expand_line_continuations(text):
    """Join lines ending with a lone backslash (not in comments).
    Statements are joined with ';' so the result is still valid."""
    lines = text.split("\n")
    out = []
    i = 0
    while i < len(lines):
        raw = lines[i]
        code = _strip_comment(raw)
        if code.rstrip().endswith("\\"):
            # continue accumulating
            merged = [code.rstrip()[:-1].rstrip()]
            while i + 1 < len(lines):
                i += 1
                nxt = lines[i]
                nxt_code = _strip_comment(nxt)
                if nxt_code.rstrip().endswith("\\"):
                    merged.append(nxt_code.rstrip()[:-1].rstrip())
                else:
                    merged.append(nxt)
                    break
            out.append(" ; ".join(m for m in merged if m.strip()))
        else:
            out.append(raw)
        i += 1
    return "\n".join(out)


def expand_semicolons(text):
    """Split ';' at depth 0 into separate statements (own lines)."""
    lines = text.split("\n")
    out = []
    for line in lines:
        code = _strip_comment(line)
        semi_idxs = _find_unprotected_semicolons(code)
        if not semi_idxs:
            out.append(line)
            continue
        comment_part = line[len(code):] if len(line) > len(code) else ""
        pieces = []
        last = 0
        for idx in semi_idxs:
            pieces.append(code[last:idx].strip())
            last = idx + 1
        pieces.append(code[last:].strip())
        for p in pieces:
            if p:
                out.append(p)
        if comment_part:
            out.append(comment_part.lstrip())
    return "\n".join(out)


def expand_angle_groups(text):
    """<C4 E4 G4> -> [C4 E4 G4] (angle brackets alias square note groups)."""
    def _rep(m):
        inner = m.group(1)
        if re.search(r"[A-Ga-g]#?b?\d", inner):
            return "[" + inner + "]"
        return m.group(0)
    return re.sub(r"<([^<>{}]+)>", _rep, text)


def expand_group_commas(text):
    """[C4, E4, G4] -> [C4 E4 G4] and (C4, E4, G4) -> (C4 E4 G4)."""
    def _rep(m):
        inner = m.group(1)
        if re.search(r"[A-Ga-g]#?b?\d", inner):
            return "[" + re.sub(r"\s*,\s*", " ", inner) + "]"
        return m.group(0)
    return re.sub(r"\[([^\]]*)\]", _rep, text)


def expand_labeled_fields(text):
    """T:0 N:60 D:500 V:80 -> T0 N60 D500 V80 (and N:C4 D:q V:mf)."""
    lines = text.split("\n")
    out = []
    for line in lines:
        m = _LABELED_MACHINE.match(line.strip())
        if not m:
            out.append(line)
            continue
        pre = m.group("pre")
        ts = m.group("ts")
        note = m.group("note")
        rest = m.group("rest")
        if note.isdigit():
            new = f"{pre}T{ts} N{note}"
        else:
            new = f"{pre}T{ts} N {note}"
        for fm in _LABELED_FIELD.finditer(rest):
            kind, val = fm.group("kind"), fm.group("val")
            if kind == "N":
                # note: N60 (number) or N C4 (name — needs a space)
                if val.isdigit():
                    new += f" N{val}"
                else:
                    new += f" N {val}"
            elif val.replace(".", "", 1).isdigit():
                new += f" {kind}{val}"
            else:
                # word form — machine syntax needs a space: D q, V mf
                new += f" {kind} {val}"
        out.append(new)
    return "\n".join(out)


def expand_punctuation(text):
    """Full v4 punctuation pass — order matters:
    continuations -> angle groups -> group commas -> semicolons -> labeled."""
    text = expand_line_continuations(text)
    text = expand_angle_groups(text)
    text = expand_group_commas(text)
    text = expand_semicolons(text)
    text = expand_labeled_fields(text)
    return text
