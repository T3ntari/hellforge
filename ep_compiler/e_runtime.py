""".ei project runtime interpreter — include, section, play, wait, inheritance.
Strips comments. Detects circular root references via DAG."""
import os
import re
import copy
from .comments import (
    strip_comments,
    strip_line,
)
from .graph import CircularReferenceError

EI_INCLUDE_RE = re.compile(r'include\s+"([^"]+)"\s+as\s+(\w+)', re.I)
EI_INCLUDE_DIR_RE = re.compile(r'include_dir\s+"([^"]+)"\s+as\s+(\w+)', re.I)
EI_SECTION_RE = re.compile(r'section\s+"([^"]+)"\s*\{', re.I)
EI_PLAY_RE = re.compile(r'play\s+(\w+)(?:\s+after\s+(\d+)ms?)?(?:\s+with\s+(\w+))?', re.I)
EI_WAIT_RE = re.compile(r'wait\s+(\d+)ms?', re.I)
EI_TEMPO_RE = re.compile(r'tempo\s+(\d+(?:\.\d+)?)', re.I)
EI_ROOT_RE = re.compile(r'root\s+"([^"]+)"', re.I)
EI_PROJECT_RE = re.compile(r'project\s+"([^"]+)"', re.I)
EI_COMPOSER_RE = re.compile(r'composer\s+"([^"]+)"', re.I)


class EIProject:
    """Represents a parsed .ei project with inherited state."""
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.name = ""
        self.composer = ""
        self.parts = {}       # name -> source text
        self.sections = []    # list of (name, commands)
        self.commands = []    # flattened commands if no sections
        self.bpm = 120
        self.parent = None    # parent EIProject (for inheritance)
        self.variables = {}   # $var scope

    def resolve_path(self, rel):
        return os.path.normpath(os.path.join(self.base_dir, rel))


def load_ei(path, visited=None):
    """Load and parse a .ei file. Returns EIProject with all parts resolved.
    Raises CircularReferenceError if a root inheritance cycle is detected."""
    from .graph import CircularReferenceError
    if visited is None:
        visited = set()
    abspath = os.path.normpath(os.path.abspath(path))
    if abspath in visited:
        chain = list(visited) + [abspath]
        raise CircularReferenceError(abspath, [str(p) for p in chain])
    visited.add(abspath)

    base_dir = os.path.dirname(abspath)
    proj = EIProject(base_dir)

    with open(abspath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    text = strip_comments(text)

    # Parse metadata
    m = EI_PROJECT_RE.search(text)
    if m:
        proj.name = m.group(1)
    m = EI_COMPOSER_RE.search(text)
    if m:
        proj.composer = m.group(1)
    m = EI_TEMPO_RE.search(text)
    if m:
        proj.bpm = float(m.group(1))

    # Parse root (inheritance)
    m = EI_ROOT_RE.search(text)
    if m:
        parent_path = proj.resolve_path(m.group(1))
        if os.path.exists(parent_path):
            parent_proj = load_ei(parent_path, visited)
            if parent_proj:
                proj.parent = parent_proj
                proj.parts.update(parent_proj.parts)
                proj.variables.update(parent_proj.variables)

    # Parse include directives
    for m in EI_INCLUDE_RE.finditer(text):
        rel = m.group(1)
        name = m.group(2)
        full = proj.resolve_path(rel)
        if os.path.exists(full):
            with open(full, "r", encoding="utf-8", errors="replace") as pf:
                proj.parts[name] = pf.read()

    for m in EI_INCLUDE_DIR_RE.finditer(text):
        rel = m.group(1)
        name = m.group(2)
        full = proj.resolve_path(rel)
        if os.path.isdir(full):
            for fname in sorted(os.listdir(full)):
                if fname.endswith(".e"):
                    with open(os.path.join(full, fname), "r", encoding="utf-8") as pf:
                        proj.parts[f"{name}/{fname}"] = pf.read()

    # Parse sections and commands
    lines = text.split("\n")
    in_section = None
    current_section_commands = []

    for line in lines:
        stripped = strip_line(line).strip()
        if not stripped:
            continue

        inline_m = re.match(r'section\s+"([^"]+)"\s*\{\s*(.+?)\s*\}', stripped, re.I)
        if inline_m:
            sname = inline_m.group(1)
            body = inline_m.group(2).strip()
            commands = [c.strip() for c in body.split(";") if c.strip()] if body else []
            proj.sections.append((sname, commands))
            continue

        m = EI_SECTION_RE.match(stripped)
        if m:
            if in_section and current_section_commands:
                proj.sections.append((in_section, list(current_section_commands)))
            in_section = m.group(1)
            current_section_commands = []
            continue
        if stripped == "}":
            if in_section and current_section_commands:
                proj.sections.append((in_section, list(current_section_commands)))
            in_section = None
            current_section_commands = []
            continue
        if in_section:
            current_section_commands.append(stripped)
        else:
            if EI_PLAY_RE.match(stripped) or EI_WAIT_RE.match(stripped) or EI_TEMPO_RE.match(stripped):
                proj.commands.append(stripped)

    if in_section and current_section_commands:
        proj.sections.append((in_section, list(current_section_commands)))

    return proj


def compile_ei_project(proj, global_bpm=120):
    """Compile an EIProject into flat events. Returns (events, bpm)."""
    from .compile import compile_source
    from .events import (
        sort_events,
        validate_events,
    )

    all_events = []
    cursor = 0
    bpm = proj.bpm or global_bpm

    def resolve_part(name, offset=0):
        nonlocal cursor
        if name in proj.parts:
            text = proj.parts[name]
            for vk, vv in proj.variables.items():
                text = text.replace(f"${vk}", str(vv))
            ev, _ = compile_source(text, bpm=bpm)
            for e in ev:
                e["timestamp"] += offset
            return ev
        return []

    def process_commands(commands, start_cursor=0):
        nonlocal cursor, bpm
        local_cursor = start_cursor
        for cmd in commands:
            m = EI_PLAY_RE.match(cmd)
            if m:
                name = m.group(1)
                after = int(m.group(2)) if m.group(2) else 0
                with_name = m.group(3)
                if with_name:
                    ev1 = resolve_part(name, local_cursor + after)
                    ev2 = resolve_part(with_name, local_cursor + after)
                    all_events.extend(ev1 + ev2)
                    dur1 = max((e["timestamp"] + e["duration"] for e in ev1), default=0)
                    dur2 = max((e["timestamp"] + e["duration"] for e in ev2), default=0)
                    local_cursor = max(local_cursor + after, max(dur1, dur2))
                else:
                    ev = resolve_part(name, local_cursor + after)
                    all_events.extend(ev)
                    if ev:
                        local_cursor = max(e["timestamp"] + e["duration"] for e in ev)
                continue
            m = EI_WAIT_RE.match(cmd)
            if m:
                local_cursor += int(m.group(1))
                continue
            m = EI_TEMPO_RE.match(cmd)
            if m:
                bpm = float(m.group(1))
                continue
        return local_cursor

    if proj.sections:
        for sname, scmds in proj.sections:
            cursor = process_commands(scmds, cursor)
    else:
        cursor = process_commands(proj.commands, cursor)

    if proj.parent:
        parent_events, parent_bpm = compile_ei_project(proj.parent, bpm)
        all_events = parent_events + all_events

    all_events = sort_events(all_events)
    all_events, _ = validate_events(all_events)
    return all_events, bpm


def compile_ei_file(path, bpm_override=None):
    """Load and compile a .ei file. Returns (events, bpm).
    Raises CircularReferenceError if a cycle is detected in root inheritance."""
    proj = load_ei(path)
    ev, bp = compile_ei_project(proj, bpm_override or 120)
    return ev, bp
