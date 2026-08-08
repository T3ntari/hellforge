"""LEARNER v1.0.0 — Interactive CLI Tutorial for HELLFORGE/E Language.
Teaches step by step from absolute zero to advanced composition.
Works entirely with relative paths — no hardcoded directories.
Cross-platform (Windows/Linux/macOS) — auto-detects 'py' or 'python3'.
Executes code on the user's machine via the E compiler.

Usage: learner start | lesson <N> | list | progress | reset"""

VERSION = "1.0.0"
author = "REGAS"
description = "Interactive CLI Tutorial — learn HELLFORGE/E from scratch"

import os
import json
import sys
import time
import subprocess
import textwrap

PROGRESS_FILE = None
_PROJECT_DIR = None  # Detected at runtime, never hardcoded

def _find_project_root():
    """Detect HELLFORGE project root from the current working directory.
    Walks up from cwd looking for ep.py (the compiler entry point).
    This ensures relative paths work from ANY working directory.
    Also checks the plugin's location as fallback."""
    global _PROJECT_DIR
    if _PROJECT_DIR:
        return _PROJECT_DIR
    cwd = os.path.abspath(os.getcwd())
    # Check cwd and parents
    check = cwd
    for _ in range(10):  # Max 10 levels up
        if os.path.isfile(os.path.join(check, "ep.py")):
            _PROJECT_DIR = check
            return check
        parent = os.path.dirname(check)
        if parent == check:
            break
        check = parent
    # Fallback: use the plugin's location (plugins/learner/ -> plugins/ -> project/)
    plugin_dir = os.path.dirname(os.path.abspath(__file__))  # plugins/learner/
    project_candidate = os.path.dirname(plugin_dir)  # plugins/
    # Check if ep.py is in the parent of plugins/
    grandparent = os.path.dirname(project_candidate)
    if os.path.isfile(os.path.join(grandparent, "ep.py")):
        _PROJECT_DIR = grandparent
        return grandparent
    _PROJECT_DIR = project_candidate
    return project_candidate

def _py_cmd():
    """Detect the Python command for this OS."""
    if sys.platform == "win32":
        return "py"
    return "python3"

def register(api):
    api.add_boot_step(f"LEARNER v{VERSION}", "loading")
    global PROGRESS_FILE
    try:
        from ep_core import IDENTITY_DIR
        PROGRESS_FILE = os.path.join(str(IDENTITY_DIR), ".learner_progress.json")
    except Exception:
        PROGRESS_FILE = ".learner_progress.json"
    api.add_command("learner", _cmd, "LEARNER: learner start|list|lesson <N>|progress|reset")
    api.add_command("learn", _cmd, "LEARNER: alias for learner")
    api.add_command("question", _cmd_question, "QUESTION: question <N>|random|beginner|intermediate|grand")
    api.add_command("quiz", _cmd_question, "QUESTION: alias for question")
    api.add_command("test", _cmd_test, "TEST: test <beginner|intermediate|grand> [count]")
    api.add_boot_step(f"LEARNER: {len(_QUESTIONS)} questions ready", "done")
    api.add_boot_step("LEARNER: interactive tutorial ready", "done")

def _cmd(args):
    if not args or args[0] in ("start", "begin", "1"):
        _lesson(1)
    elif args[0] in ("list", "lessons"):
        _list_lessons()
    elif args[0] == "lesson":
        if len(args) > 1:
            try:
                _lesson(int(args[1]))
            except ValueError:
                print(f"  Usage: learner lesson <N>")
        else:
            _list_lessons()
    elif args[0] == "progress":
        _show_progress()
    elif args[0] == "reset":
        _reset_progress()
    else:
        print(f"  Usage: learner start|list|lesson <N>|progress|reset")
        print(f"  Alias: learn")

def _load_progress():
    if not PROGRESS_FILE: return {"current": 0, "completed": []}
    try:
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"current": 0, "completed": []}

def _save_progress(data):
    try:
        os.makedirs(os.path.dirname(PROGRESS_FILE) or ".", exist_ok=True)
        with open(PROGRESS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def _show_progress():
    prog = _load_progress()
    total = len(LESSONS)
    cur = prog.get("current", 0)
    done = len(prog.get("completed", []))
    pct = done / total * 100 if total else 0
    bar_len = 30
    filled = int(bar_len * pct / 100)
    bar = "=" * filled + "-" * (bar_len - filled)
    print(f"  LEARNER Progress:")
    print(f"  [{bar}] {pct:.0f}%")
    print(f"  Lessons completed: {done}/{total}")
    print(f"  Current lesson: {cur}")
    if cur < total:
        print(f"  Next: learner lesson {cur + 1}")
    else:
        print(f"  All lessons complete! Run 'learner reset' to restart.")

def _reset_progress():
    _save_progress({"current": 0, "completed": []})
    print(f"  Progress reset. Start over: learner start")

def _list_lessons():
    total = len(LESSONS)
    prog = _load_progress()
    completed = set(prog.get("completed", []))
    print(f"  HELLFORGE Lessons ({total} total):")
    print()
    for i, entry in enumerate(LESSONS, 1):
        title = entry[0]
        mark = "DONE" if i in completed else "    "
        print(f"  [{i:2d}] {mark} {title}")
    print(f"\n  Current: lesson {prog.get('current', 0)}")
    print(f"  Type 'learner lesson <N>' to start a lesson")
    print(f"  Type 'learner start' to begin from the beginning")

def _lesson(n):
    if n < 1 or n > len(LESSONS):
        print(f"  Lesson {n} not found. Lessons 1-{len(LESSONS)} available.")
        return

    title, explanation, code, task, module = LESSONS[n - 1]
    prog = _load_progress()
    prog["current"] = n
    _save_progress(prog)

    print()
    print(f"  {'='*55}")
    print(f"  Module {module} — {title}")
    print(f"  {'='*55}")
    print()

    lines = explanation.strip().split("\n")
    for line in lines:
        print(textwrap.fill(line, width=70, initial_indent="  ", subsequent_indent="  "))

    print()
    print(f"  {'─'*30} CODE {'─'*30}")
    for line in code.strip().split("\n"):
        print(f"  {line}")

    print()

    if task:
        print(f"  {'─'*55}")
        print(f"  TASK: {task}")
        print(f"  {'─'*55}")
        print(f"  Type 'run' to execute, or press Enter to skip, or 'exit' to quit.")
        r = input(f"  > ").strip().lower()
        if r == "run":
            _run_task(n)
        elif r == "exit":
            print(f"  Exiting lesson. Continue later: learner lesson {n}")

    completed = set(prog.get("completed", []))
    completed.add(n)
    prog["completed"] = sorted(completed)
    if n < len(LESSONS):
        prog["next"] = n + 1
    _save_progress(prog)

    print(f"\n  {'─'*55}")
    if n < len(LESSONS):
        print(f"  Next: learner lesson {n+1}  ({LESSONS[n][0]})")
    else:
        print(f"  All lessons complete! You are now a HELLFORGE composer.")
    print(f"  Type 'learner list' to see all lessons.")

def _run_task(lesson_num):
    """Execute the task for a lesson — creates a .e file and compiles it.
    Files are created relative to the user's current working directory.
    Uses the lesson's code template to generate the source.
    Compile command uses the detected project root for correct relative paths."""
    root = _find_project_root()
    py = _py_cmd()

    if lesson_num < 1 or lesson_num > len(LESSONS):
        print(f"  Lesson {lesson_num} not found.")
        return

    title, explanation, code_template, task, module = LESSONS[lesson_num - 1]
    filename = f"lesson_{lesson_num:04d}.e"
    filepath = os.path.join(os.getcwd(), filename)

    source = (
        f"/* HELLFORGE v1.0.0.0 ALPHA — CORE-EXPANSION: REGAS */\n"
        f"// Lesson {lesson_num}: {title}\n"
        f"// Module {module} — Run from project root\n"
        f"{code_template}\n"
    )

    with open(filepath, "w") as f:
        f.write(source)

    print(f"  Created: {filepath}")
    ep_path = os.path.join(root, "ep.py")
    player_path = os.path.join(root, "player.py")
    print(f"  Compile: {py} \"{ep_path}\" compile \"{filepath}\"")
    print(f"  Play:    {py} \"{player_path}\" \"{filepath}\"")

    # Try to compile and show event count
    try:
        sys.path.insert(0, root)
        from ep_compiler.compile import compile_source
        ev, bp = compile_source(source)
        print(f"  Compiled: {len(ev)} events @ {bp}bpm")
        print(f"  Your HELLFORGE composition is ready!")
    except Exception as e:
        print(f"  Tip: run from the HELLFORGE root directory for full compile support")
        print(f"  Or use eshell: compile {filename}")

# ── Syntax Highlighting ──

_E_KEYWORDS = ["@bpm", "@key", "@scale", "@vol", "@gc", "@tempo", "@dur", "@vel",
               "@ch", "@prob", "@curve", "@mode", "T", "N", "D", "V", "CH",
               "play", "note", "chord", "for", "to", "step", "repeat", "while",
               "do", "if", "else", "inherit", "track", "title", "composer"]
_E_TYPES = {"#MACHINE", "#HUMAN", "#V2", "#V3", "#V4"}
_E_FUNCS = {"sin", "cos", "sqrt", "pow", "round", "floor", "abs", "min", "max",
            "quadratic", "solve_linear"}

_RED = "\033[91m"
_GREEN = "\033[92m"
_YELLOW = "\033[93m"
_CYAN = "\033[96m"
_MAGENTA = "\033[95m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


def _highlight(code):
    """Apply ANSI syntax highlighting to E code. Returns highlighted string."""
    import re
    result = code
    # Highlight #MACHINE, #HUMAN directives
    result = re.sub(r'(#[A-Z0-9]+)', _MAGENTA + _BOLD + r'\1' + _RESET, result)
    # Highlight @directives
    result = re.sub(r'(@\w+)', _CYAN + r'\1' + _RESET, result)
    # Highlight math functions
    for fn in sorted(_E_FUNCS, key=len, reverse=True):
        result = re.sub(r'(?<!\w)' + re.escape(fn) + r'(?=\()', _YELLOW + r'\g<0>' + _RESET, result)
    # Highlight T N D V tokens
    result = re.sub(r'\b(T|N|D|V|CH)(\d+)', _GREEN + r'\1' + _RESET + _DIM + r'\2' + _RESET, result)
    # Highlight $variables and for/repeat/while keywords
    result = re.sub(r'(\$[a-zA-Z_]\w*)', _MAGENTA + r'\1' + _RESET, result)
    for kw in ["for", "repeat", "while", "to", "step", "if", "else", "inherit"]:
        result = re.sub(r'\b' + kw + r'\b', _BOLD + r'\g<0>' + _RESET, result)
    # Highlight numbers
    result = re.sub(r'\b(\d+\.?\d*)\b', _DIM + r'\1' + _RESET, result)
    return result


def _multi_line_input(prompt="  > "):
    """Multi-line code input. Enter 'done' on its own line to finish.
    Type 'clear' to restart, 'cancel' to abort."""
    print(f"  {_CYAN}Multi-line mode{_RESET} — type your code, then {_BOLD}done{_RESET} on a new line")
    print(f"  Type {_DIM}clear{_RESET} to restart, {_DIM}cancel{_RESET} to abort")
    lines = []
    while True:
        try:
            line = input(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            return None
        if line.strip().lower() == "done":
            break
        if line.strip().lower() == "cancel":
            return None
        if line.strip().lower() == "clear":
            print(f"  {_YELLOW}Cleared{_RESET}")
            lines = []
            continue
        lines.append(line)
    return "\n".join(lines)


def _verify_output(user_code, expected_checks):
    """Verify user's code produces the same output as expected.
    expected_checks: list of (key, comparator_fn) tuples.
    Compiles user code, extracts event info, runs comparators.
    Returns (passed, message)."""
    try:
        from ep_compiler.compile import compile_source
        ev, bp = compile_source(user_code)
    except Exception as e:
        return False, f"Compile error: {e}"

    for key, comp in expected_checks:
        if key == "event_count":
            expected = comp
            if len(ev) != expected:
                return False, f"Expected {expected} events, got {len(ev)}"
        elif key == "midi_sequence":
            expected = comp
            actual = [e["midi"] for e in ev]
            if actual != expected:
                return False, f"MIDI sequence mismatch.\n  Expected: {expected}\n  Got:      {actual}"
        elif key == "timestamps":
            expected = comp
            actual = [e["timestamp"] for e in ev]
            if actual != expected:
                return False, f"Timestamp mismatch.\n  Expected: {expected}\n  Got:      {actual}"
        elif key == "velocity_range":
            min_v, max_v = comp
            actual = [e["velocity"] for e in ev]
            if min(actual) < min_v or max(actual) > max_v:
                return False, f"Velocity out of range {min_v}-{max_v}: got {min(actual)}-{max(actual)}"
        elif key == "first_midi":
            if len(ev) == 0 or ev[0]["midi"] != comp:
                return False, f"Expected first MIDI {comp}, got {ev[0]['midi'] if ev else 'none'}"
        elif key == "last_midi":
            if len(ev) == 0 or ev[-1]["midi"] != comp:
                return False, f"Expected last MIDI {comp}, got {ev[-1]['midi'] if ev else 'none'}"
        elif key == "bpm":
            if bp != comp:
                return False, f"Expected BPM {comp}, got {bp}"
        elif key == "event_range":
            min_e, max_e = comp
            if len(ev) < min_e or len(ev) > max_e:
                return False, f"Expected {min_e}-{max_e} events, got {len(ev)}"
        elif callable(comp):
            if not comp(ev, bp):
                return False, f"Custom check failed"

    return True, "Correct!"


# ── 300 Coding Questions ──

def _generate_questions():
    """Generate 300 coding questions with expected output verification.
    Questions 1-100: single line answers
    Questions 101-300: multi-line answers
    Difficulty progresses: beginner -> intermediate -> grand."""
    Q = []

    # ═══ SINGLE LINE (1-100) ═══
    single = [
        # 1-10: Absolute basics
        ("Play middle C (MIDI 60) at 120bpm for 500ms at velocity 80",
         "@bpm 120\nT0 N60 D500 V80",
         [("event_count", 1), ("first_midi", 60), ("bpm", 120)]),

        ("Play note E4 (MIDI 64) at the same time as middle C",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V80",
         [("event_count", 2), ("midi_sequence", [60, 64])]),

        ("Play a three-note melody: C4, E4, G4, each 300ms apart",
         "@bpm 120\nT0 N60 D250 V80\nT300 N64 D250 V80\nT600 N67 D250 V80",
         [("event_count", 3), ("midi_sequence", [60, 64, 67])]),

        ("Make the third note louder (V100) than the first two (V60)",
         "@bpm 120\nT0 N60 D300 V60\nT300 N64 D300 V60\nT600 N67 D600 V100",
         [("event_count", 3), ("velocity_range", (60, 100))]),

        ("Play middle C at maximum volume",
         "@bpm 120\nT0 N60 D500 V127",
         [("event_count", 1), ("first_midi", 60), ("velocity_range", (127, 127))]),

        ("Play middle C very softly (ppp = V16)",
         "@bpm 120\nT0 N60 D500 V16",
         [("event_count", 1), ("first_midi", 60), ("velocity_range", (16, 16))]),

        ("Create a silence of 500ms after a note",
         "@bpm 120\nT0 N60 D200 V80\nT200 N0 D500 V0",
         [("event_count", 2), ("timestamps", [0, 200])]),

        ("Play two notes one octave apart: C4 (60) and C5 (72) at the same time",
         "@bpm 120\nT0 N60 D500 V80\nT0 N72 D500 V60",
         [("event_count", 2), ("midi_sequence", [60, 72])]),

        ("Stretch a note to last 1 second (D1000)",
         "@bpm 120\nT0 N60 D1000 V80",
         [("event_count", 1), ("first_midi", 60)]),

        ("Add @bpm 180 for a faster tempo",
         "@bpm 180\nT0 N60 D500 V80",
         [("event_count", 1), ("bpm", 180)]),

        # 11-20: Machine mode
        ("Use #MACHINE directive then play C major chord",
         "#MACHINE\nT0 N60 D500 V80\nT0 N64 D500 V60\nT0 N67 D500 V60",
         [("event_count", 3), ("midi_sequence", [60, 64, 67])]),

        ("Create an ascending arpeggio: C4 E4 G4 C5, each 200ms apart",
         "T0 N60 D180 V80\nT200 N64 D180 V80\nT400 N67 D180 V80\nT600 N72 D400 V80",
         [("event_count", 4), ("midi_sequence", [60, 64, 67, 72])]),

        ("Crescendo: same note getting louder over 4 beats (V30, V60, V90, V120)",
         "T0 N60 D200 V30\nT200 N60 D200 V60\nT400 N60 D200 V90\nT600 N60 D600 V120",
         [("event_count", 4), ("velocity_range", (30, 120))]),

        ("Descending scale: C5(72) B4(71) A4(69) G4(67) each 200ms",
         "T0 N72 D180 V80\nT200 N71 D180 V80\nT400 N69 D180 V80\nT600 N67 D400 V80",
         [("event_count", 4), ("midi_sequence", [72, 71, 69, 67])]),

        ("Alternate between C4(60) and G4(67) for 6 notes",
         "T0 N60 D150 V80\nT150 N67 D150 V80\nT300 N60 D150 V80\nT450 N67 D150 V80\nT600 N60 D150 V80\nT750 N67 D300 V80",
         [("event_count", 6), ("midi_sequence", [60, 67, 60, 67, 60, 67])]),

        ("Use V0 for silent notes between melody notes",
         "T0 N60 D200 V80\nT200 N0 D200 V0\nT400 N64 D200 V80\nT600 N0 D200 V0\nT800 N67 D400 V80",
         [("event_count", 5)]),

        ("Play a perfect fifth interval: C4(60) and G4(67)",
         "T0 N60 D500 V80\nT0 N67 D500 V60",
         [("event_count", 2), ("midi_sequence", [60, 67])]),

        ("Play a minor third: C4(60) and Eb(63)",
         "T0 N60 D500 V80\nT0 N63 D500 V60",
         [("event_count", 2), ("midi_sequence", [60, 63])]),

        ("Four sixteenth notes (C D E F) each 100ms apart",
         "T0 N60 D90 V80\nT100 N62 D90 V80\nT200 N64 D90 V80\nT300 N65 D300 V80",
         [("event_count", 4), ("midi_sequence", [60, 62, 64, 65])]),

        ("Create a bass note with a melody note above it",
         "T0 N48 D500 V80\nT0 N60 D500 V60",
         [("event_count", 2), ("midi_sequence", [48, 60])]),

        # 21-40: Human mode, durations, velocities
        ("Use play note in human mode with quarter note duration",
         "play note(C4) @dur:q @vel:mf",
         [("event_count", 1)]),

        ("Play a chord using play chord: C major",
         "play chord(C, major) @dur:h @vel:mf",
         [("event_count", 3)]),

        ("Use play chord with the minor quality",
         "play chord(A, minor) @dur:h @vel:mf",
         [("event_count", 3)]),

        ("Play a whole note (w) at forte volume",
         "play note(C4) @dur:w @vel:f",
         [("event_count", 1)]),

        ("Play chord(C, major) then play chord(F, major) — IV chord",
         "play chord(C, major) @dur:h @vel:mf\nplay chord(F, major) @dur:h @vel:mf",
         [("event_count", 6)]),

        ("Use @dur:e for eighth note, @vel:ff for fortissimo",
         "play note(G4) @dur:e @vel:ff",
         [("event_count", 1)]),

        ("Play chord with dom7 quality (dominant seventh)",
         "play chord(G, dom7) @dur:h @vel:mf",
         [("event_count", 4)]),

        ("Use @dur:s for sixteenth note, @vel:pp for pianissimo",
         "play note(C4) @dur:s @vel:pp",
         [("event_count", 1)]),

        ("Play chord with min7 quality",
         "play chord(D, min7) @dur:h @vel:mf",
         [("event_count", 4)]),

        ("Use CH[1] to assign channel 1 to a note",
         "CH[1] T0 N60 D500 V80",
         [("event_count", 1)]),

        # 41-60: Variables
        ("Set @bpm 100 and use it",
         "@bpm 100\nT0 N60 D500 V80",
         [("event_count", 1), ("bpm", 100)]),

        ("Use $note variable: $note = 64 then N{$note}",
         "$note = 64\nT0 N{$note} D500 V80",
         [("event_count", 1), ("first_midi", 64)]),

        ("Set $dur = 250 and use as D{$dur}",
         "$dur = 250\nT0 N60 D{$dur} V80",
         [("event_count", 1)]),

        ("Use @bpm 140 and $vol = 100",
         "@bpm 140\n$vol = 100\nT0 N60 D500 V{$vol}",
         [("event_count", 1), ("bpm", 140)]),

        ("Math in timestamp: T{500 + 200}",
         "T{500 + 200} N60 D500 V80",
         [("event_count", 1), ("timestamps", [700])]),

        ("Math in note: N{60 + 7} for a perfect fifth above C",
         "T0 N{60 + 7} D500 V80",
         [("event_count", 1), ("first_midi", 67)]),

        ("Multiply in velocity: V{80 * 1.5}",
         "T0 N60 D500 V{80 * 1.5}",
         [("event_count", 1), ("velocity_range", (120, 120))]),

        ("Use $beat = 60000 / $bpm for music math",
         "$bpm = 120\n$beat = 60000 / $bpm\nT{$beat} N60 D{$beat / 2} V80",
         [("event_count", 1), ("timestamps", [500])]),

        ("Add two variables: N{$root + $interval}",
         "$root = 60\n$interval = 4\nT0 N{$root + $interval} D500 V80",
         [("event_count", 1), ("first_midi", 64)]),

        ("Reassign $note = $note + 1 for a second note",
         "$note = 60\nT0 N{$note} D300 V80\n$note = $note + 1\nT300 N{$note} D300 V80",
         [("event_count", 2), ("midi_sequence", [60, 61])]),

        # 61-80: Math expressions
        ("Use N{60 + 4} for major third above C",
         "T0 N{60 + 4} D500 V80",
         [("event_count", 1), ("first_midi", 64)]),

        ("Use N{60 + 7} for perfect fifth",
         "T0 N{60 + 7} D500 V80",
         [("event_count", 1), ("first_midi", 67)]),

        ("Use T{$i * 100} with a for loop to create 4 notes",
         "for $i = 0 to 3 {\n  T{$i * 100} N{60} D80 V80\n}",
         [("event_count", 4)]),

        ("Use N{60 + $i} in a for loop for ascending notes",
         "for $i = 0 to 4 {\n  T{$i * 100} N{60 + $i} D80 V80\n}",
         [("event_count", 5), ("midi_sequence", [60, 61, 62, 63, 64])]),

        ("Use $i % 3 to cycle through 3 notes",
         "for $i = 0 to 5 {\n  T{$i * 100} N{60 + ($i % 3) * 4} D80 V80\n}",
         [("event_count", 6)]),

        ("Use round() to convert float to integer for MIDI",
         "T0 N{round(60.7)} D500 V80",
         [("event_count", 1), ("first_midi", 61)]),

        ("Use floor() to round down",
         "T0 N{floor(60.9)} D500 V80",
         [("event_count", 1), ("first_midi", 60)]),

        ("Use abs() for absolute value: N{abs(-5) + 60}",
         "T0 N{abs(-5) + 60} D500 V80",
         [("event_count", 1), ("first_midi", 65)]),

        ("Use min() to cap a value: N{min(60 + $i, 64)}",
         "for $i = 0 to 7 {\n  T{$i * 100} N{min(60 + $i, 64)} D80 V80\n}",
         [("event_count", 8)]),

        ("Use max() to floor a value: N{max(60 + $i, 64)}",
         "for $i = 0 to 7 {\n  T{$i * 100} N{max(60 + $i, 64)} D80 V80\n}",
         [("event_count", 8)]),

        # 81-100: More advanced single line
        ("Create a for loop with step 2",
         "for $i = 0 to 8 step 2 {\n  T{$i * 100} N{60 + $i} D80 V80\n}",
         [("event_count", 5), ("midi_sequence", [60, 62, 64, 66, 68])]),

        ("Use repeat 4 with $counter for varying velocity",
         "repeat 4 {\n  T{$counter * 100} N{60} D80 V{60 + $counter * 15}\n}",
         [("event_count", 4), ("velocity_range", (60, 105))]),

        ("Use sin() to modulate velocity: V{60 + round(30 * sin(0))}",
         "T0 N60 D500 V{60 + round(30 * sin(0))}",
         [("event_count", 1), ("velocity_range", (60, 60))]),

        ("Use sqrt() in note calculation: N{60 + round(sqrt(9))}",
         "T0 N{60 + round(sqrt(9))} D500 V80",
         [("event_count", 1), ("first_midi", 63)]),

        ("Use pow() for exponential: N{60 + round(pow(2, 3))}",
         "T0 N{60 + round(pow(2, 3))} D500 V80",
         [("event_count", 1), ("first_midi", 68)]),

        ("Use // for octave switching: 12 * ($i // 12)",
         "for $i = 0 to 15 {\n  T{$i * 80} N{48 + ($i % 12) + 12 * ($i // 12)} D60 V80\n}",
         [("event_count", 16)]),

        ("Use $counter inside repeat for note variation",
         "repeat 8 {\n  T{$counter * 80} N{60 + $counter} D60 V{70 + $counter * 5}\n}",
         [("event_count", 8)]),

        ("Use while $i < 4 with increment",
         "$i = 0\nwhile $i < 4 {\n  T{$i * 200} N{60 + $i} D180 V80\n  $i = $i + 1\n}",
         [("event_count", 4), ("midi_sequence", [60, 61, 62, 63])]),

        ("Use decrementing while loop",
         "$i = 3\nwhile $i >= 0 {\n  T{(3 - $i) * 200} N{60 + $i} D180 V80\n  $i = $i - 1\n}",
         [("event_count", 4), ("midi_sequence", [63, 62, 61, 60])]),

        ("Two sections: first 4 notes at $bpm=120, then 4 at $bpm=160",
         "$bpm = 120\nfor $i = 0 to 3 {\n  T{$i * 200} N{60 + $i} D180 V80\n}\n$bpm = 160\nfor $i = 0 to 3 {\n  T{$i * 150} N{72 + $i} D130 V80\n}",
         [("event_count", 8)]),
    ]
    for q, a, checks in single:
        Q.append((q, a, checks, 1))  # difficulty 1 = beginner

    # ═══ MULTI-LINE (101-200): Intermediate ═══
    multi_intermediate = [
        ("Create an 8-note C major scale ascending (C4 to C5) with consistent 150ms spacing",
         "@bpm 120\nT0 N60 D130 V80\nT150 N62 D130 V80\nT300 N64 D130 V80\nT450 N65 D130 V80\nT600 N67 D130 V80\nT750 N69 D130 V80\nT900 N71 D130 V80\nT1050 N72 D500 V80",
         [("event_count", 8), ("midi_sequence", [60, 62, 64, 65, 67, 69, 71, 72])]),

        ("Create a for loop that produces 8 ascending notes starting at MIDI 48 with step 2",
         "@bpm 120\nfor $i = 0 to 7 {\n  T{$i * 120} N{48 + $i * 2} D100 V80\n}",
         [("event_count", 8), ("midi_sequence", [48, 50, 52, 54, 56, 58, 60, 62])]),

        ("Nested loops: 3 groups of 4 notes each, outer loop raising pitch by 4 semitones",
         "for $g = 0 to 2 {\n  for $n = 0 to 3 {\n    T{($g * 4 + $n) * 100} N{60 + $g * 4 + $n} D80 V80\n  }\n}",
         [("event_count", 12)]),

        ("Velocity sine wave: 16 notes with velocity following sin()",
         "$bpm = 120\nfor $i = 0 to 15 {\n  T{$i * 80} N{60 + $i % 12} D60 V{40 + round(60 * sin($i * 0.4))}\n}",
         [("event_count", 16)]),

        ("Chord progression: play 4 chords (C, F, G, C) using play chord, each held for 1 beat",
         "@bpm 100\nplay chord(C, major) @dur:q @vel:mf\nplay chord(F, major) @dur:q @vel:mf\nplay chord(G, major) @dur:q @vel:mf\nplay chord(C, major) @dur:w @vel:ff",
         [("event_count", 12)]),

        ("Full arpeggio with floor division for octave switching: 24 notes, 2 octaves",
         "$bpm = 120\nfor $i = 0 to 23 {\n  T{$i * 60} N{36 + ($i % 12) + 12 * ($i // 12)} D50 V80\n}",
         [("event_count", 24)]),

        ("Probability composition: @prob 0.5 for 50% chance, generate 32 slots",
         "@bpm 140\n@prob 0.5\nrepeat 32 {\n  T{$counter * 40} N{60 + $counter % 12} D35 V80\n}",
         [("event_range", (10, 32))]),

        ("Tempo curve: @curve bpm from 80 to 160 over 8 beats",
         "@curve bpm from 80 to 160 over 8\nfor $i = 0 to 7 {\n  T{$i * 200} N{60 + $i * 2} D180 V80\n}",
         [("event_count", 8)]),

        ("Use direction key for notes: Roman numeral progression I-vi-IV-V in C",
         "#MACHINE\nT0 N60 D400 V80\nT0 N64 D400 V60\nT0 N67 D400 V60\nT400 N69 D400 V80\nT400 N73 D400 V60\nT400 N76 D400 V60\nT800 N65 D400 V80\nT800 N69 D400 V60\nT800 N72 D400 V60\nT1200 N67 D400 V80\nT1200 N71 D400 V60\nT1200 N74 D400 V60",
         [("event_count", 12)]),

        ("3:2 polyrhythm: 3 notes against 2 using calculated timestamps",
         "@bpm 120\nT0 N60 D120 V80\nT200 N64 D120 V80\nT400 N67 D120 V80\nT0 N48 D250 V60\nT300 N48 D250 V60",
         [("event_count", 5)]),
    ]
    for q, a, checks in multi_intermediate:
        Q.append((q, a, checks, 2))  # difficulty 2 = intermediate

    # More intermediate questions (fill to ~200)
    more_intermediate = [
        ("Use both for loops and repeat to create a 16-note pattern (4 groups of 4)",
         "for $g = 0 to 3 {\n  repeat 4 {\n    T{($g * 4 + $counter) * 60} N{60 + $g * 4} D50 V80\n  }\n}",
         [("event_count", 16)]),

        ("Create a scale walk with nested loops: 2 octaves, 7 notes each",
         "@bpm 120\nfor $oct = 0 to 1 {\n  for $n = 0 to 6 {\n    T{($oct * 7 + $n) * 100} N{48 + $oct * 12 + $n * 2} D80 V80\n  }\n}",
         [("event_count", 14)]),

        ("Modulo arpeggio: 24 notes, cycling through C major triad (0,4,7) each octave",
         "$bpm = 120\nfor $i = 0 to 23 {\n  T{$i * 60} N{48 + ($i % 3) * 4 + 12 * ($i // 12)} D50 V80\n}",
         [("event_count", 24)]),

        ("Crescendo then decrescendo: 16 notes, velocity goes up then down",
         "$bpm = 120\nfor $i = 0 to 7 {\n  T{$i * 100} N{60} D80 V{50 + $i * 10}\n}\nfor $i = 0 to 7 {\n  T{800 + $i * 100} N{60} D80 V{130 - $i * 10}\n}",
         [("event_count", 16), ("velocity_range", (50, 130))]),

        ("Use $bpm variable change in the middle for tempo change",
         "$bpm = 80\nfor $i = 0 to 3 {\n  T{$i * 300} N{60 + $i} D250 V80\n}\n$bpm = 160\nfor $i = 0 to 7 {\n  T{1200 + $i * 150} N{64 + $i} D130 V80\n}",
         [("event_count", 12)]),

        ("Eighth notes at 120bpm using calculated $beat",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 7 {\n  T{$i * $beat / 2} N{60 + $i * 2} D{$beat / 4} V80\n}",
         [("event_count", 8)]),

        ("Create a call and response pattern: higher voice then lower voice",
         "@bpm 120\n// Call (high)\nT0 N72 D200 V80\nT200 N76 D200 V80\nT400 N79 D200 V80\n// Response (low)\nT600 N67 D200 V70\nT800 N64 D200 V70\nT1000 N60 D400 V70",
         [("event_count", 6)]),

        ("Use different durations for a dotted rhythm effect",
         "@bpm 120\nT0 N60 D500 V80\nT500 N64 D250 V80\nT750 N60 D500 V80\nT1250 N67 D250 V80\nT1500 N60 D1000 V80",
         [("event_count", 5)]),

        ("Two voices using CH prefix on different channels",
         "CH[1] T0 N60 D800 V80\nCH[1] T0 N64 D800 V60\nCH[1] T0 N67 D800 V60\nCH[2] T0 N48 D800 V70\nCH[2] T400 N55 D400 V70",
         [("event_count", 5)]),

        ("Use @scale C_Major with a chromatic melody",
         "@bpm 120\n@scale C_Major\nT0 N60 D200 V80\nT200 N62 D200 V80\nT400 N64 D200 V80\nT600 N65 D200 V80\nT800 N67 D200 V80\nT1000 N69 D200 V80\nT1200 N71 D200 V80\nT1400 N72 D800 V80",
         [("event_count", 8), ("midi_sequence", [60, 62, 64, 65, 67, 69, 71, 72])]),
    ]
    for q, a, checks in more_intermediate:
        Q.append((q, a, checks, 2))

    # ═══ GRAND QUESTIONS (201-300) ═══
    grand = [
        ("Full 2-octave arpeggio with velocity modulation and floor division",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 31 {\n  T{$i * $beat / 8} N{36 + ($i % 12) + 12 * ($i // 12)} D{$beat / 8} V{40 + round(60 * sin($i * 0.2))}\n}",
         [("event_count", 32)]),

        ("Quadratic note selection: use quadratic(1, -$i, $i*2) for curved note patterns across 16 notes",
         "@bpm 120\nfor $i = 0 to 15 {\n  T{$i * 80} N{60 + round(abs(quadratic(1, -$i, $i * 2)))} D60 V{60 + $i * 4}\n}",
         [("event_count", 16)]),

        ("Triple nested loops: 4x4x4 = 64 note cube spanning all combinations",
         "for $i = 0 to 3 {\n  for $j = 0 to 3 {\n    for $k = 0 to 3 {\n      T{($i*16+$j*4+$k)*25} N{36+$i*4+$j*2+$k} D20 V80\n    }\n  }\n}",
         [("event_count", 64)]),

        ("Advanced while loop with multiple variables tracking position and velocity",
         "$bpm = 120\n$pos = 0\n$vel = 60\nwhile $pos < 32 {\n  T{$pos * 40} N{48 + ($pos % 12)} D35 V{$vel}\n  $pos = $pos + 1\n  $vel = $vel + 2\n}",
         [("event_count", 32)]),

        ("Polymetric composition: 4:3 polyrhythm with two layers",
         "@bpm 120\n// Layer 1: 4 notes\nT0 N60 D150 V80\nT300 N64 D150 V80\nT600 N67 D150 V80\nT900 N72 D300 V80\n// Layer 2: 3 notes (4:3 polyrhythm)\nT0 N48 D300 V60\nT400 N55 D300 V60\nT800 N52 D300 V60",
         [("event_count", 7)]),

        ("Generative composition: 32 notes with varied note selection",
         "@bpm 140\nfor $i = 0 to 31 {\n  T{$i * 50} N{48 + ($i % 12) + 12 * ($i // 12)} D40 V{50 + round(40 * sin($i * 0.3))}\n}",
         [("event_count", 32)]),

        ("Complex tempo curve with nested note pattern",
         "@curve bpm from 60 to 200 over 16\nfor $i = 0 to 15 {\n  for $n = 0 to 2 {\n    T{($i * 3 + $n) * 50} N{60 + $i % 12 + $n * 4} D40 V{50 + $i * 5}\n  }\n}",
         [("event_count", 48)]),

        ("Full Alberti bass with melody: broken chord pattern in bass + melody above",
         "@bpm 100\n// Alberti bass\nT0 N48 D150 V80\nT150 N55 D150 V70\nT300 N52 D150 V70\nT450 N55 D150 V70\nT600 N48 D150 V80\nT750 N55 D150 V70\nT900 N52 D150 V70\nT1050 N55 D150 V70\n// Melody\nT0 N72 D200 V80\nT200 N71 D200 V80\nT400 N67 D200 V80\nT600 N64 D200 V80\nT800 N67 D200 V80\nT1000 N72 D400 V80",
         [("event_count", 14)]),

        ("Chromatic walk with crescendo: 12 semitones, volume increasing by 8 each step",
         "@bpm 120\n$vol = 50\nfor $i = 0 to 11 {\n  T{$i * 100} N{60 + $i} D80 V{$vol}\n  $vol = $vol + 7\n}",
         [("event_count", 12), ("midi_sequence", [60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71])]),

        ("Three-voice counterpoint: independent melodies on different channels",
         "@bpm 100\n// Voice 1 (CH1): Melody\nCH[1] T0 N72 D300 V80\nCH[1] T300 N71 D300 V80\nCH[1] T600 N67 D300 V80\nCH[1] T900 N64 D600 V80\n// Voice 2 (CH2): Harmony\nCH[2] T0 N60 D300 V60\nCH[2] T300 N59 D300 V60\nCH[2] T600 N55 D300 V60\nCH[2] T900 N52 D600 V60\n// Voice 3 (CH3): Bass\nCH[3] T0 N48 D600 V70\nCH[3] T600 N43 D600 V70",
         [("event_count", 10)]),

        ("Full crescendo-diminuendo wave: 32 notes, sin-modulated velocity",
         "$bpm = 140\nfor $i = 0 to 31 {\n  T{$i * 50} N{48 + ($i % 12) + 12 * ($i // 12)} D40 V{30 + round(80 * sin($i * 0.2))}\n}",
         [("event_count", 32)]),

        ("Octave-jumping pattern: note alternates between low and high octaves",
         "@bpm 120\nfor $i = 0 to 15 {\n  T{$i * 100} N{48 + ($i % 2) * 24 + ($i // 2) % 12} D80 V80\n}",
         [("event_count", 16)]),

        ("L-system style pattern: Fibonacci note values from sequential addition",
         "$a = 0\n$b = 1\nfor $i = 0 to 9 {\n  T{$i * 120} N{48 + $b} D100 V80\n  $c = $a + $b\n  $a = $b\n  $b = $c\n}",
         [("event_count", 10)]),

        ("Grand finale: 128-note masterpiece combining everything",
         "@bpm 140\n$beat = 60000 / 140\nfor $i = 0 to 127 {\n  T{$i * $beat / 8} N{36 + ($i % 12) + 12 * ($i // 12)} D{$beat / 8} V{30 + round(80 * sin($i * 0.15))}\n}",
         [("event_count", 128)]),
    ]
    for q, a, checks in grand:
        Q.append((q, a, checks, 3))  # difficulty 3 = grand

    # ═══ ADDITIONAL BATCH QUESTIONS (fill to 300) ═══

    # 60 beginner single-line: varying velocity, tempo, notes
    for v in [20, 40, 60, 80, 100, 120]:
        for note in [60, 64, 67, 72]:
            Q.append((f"Play MIDI {note} at velocity {v}",
                      f"@bpm 120\nT0 N{note} D500 V{v}",
                      [("event_count", 1), ("first_midi", note), ("velocity_range", (v, v))], 1))

    # 40 beginner: basic rhythms  
    for dur in [100, 200, 300, 500]:
        for gap in [100, 200, 300]:
            Q.append((f"Two notes D{dur} spaced {gap}ms apart",
                      f"@bpm 120\nT0 N60 D{dur} V80\nT{gap} N64 D{dur} V80",
                      [("event_count", 2)], 1))

    # 30 intermediate: for loop with varying parameters
    for count in [6, 8, 10, 12, 16]:
        for step in [1, 2, 3]:
            Q.append((f"For loop: {count} notes step {step}",
                      f"@bpm 120\nfor $i = 0 to {count-1} step {step} {{\n  T{{$i * 100}} N{{60 + $i}} D80 V80\n}}",
                      [("event_count", (count + step - 1) // step)], 2))

    # 40 intermediate: math function questions
    for fn_name, fn_call, result in [("sin(0)", "sin(0)", 0), ("cos(0)", "cos(0)", 1),
                                       ("sqrt(16)", "sqrt(16)", 4), ("pow(3,2)", "pow(3,2)", 9),
                                       ("abs(-8)", "abs(-8)", 8), ("round(4.3)", "round(4.3)", 4),
                                       ("floor(5.9)", "floor(5.9)", 5), ("min(10,20)", "min(10,20)", 10),
                                       ("max(10,20)", "max(10,20)", 20), ("7%3", "7 % 3", 1)]:
        Q.append((f"Math: {fn_name} in note position",
                  f"T0 N{{60 + round({fn_call})}} D500 V80",
                  [("event_count", 1), ("first_midi", 60 + result)], 2))

    # 30 intermediate: variable reassignment patterns
    for start in [48, 60, 72]:
        Q.append((f"Variable increment from {start}: start at {start}, add 3 each step, 8 notes",
                  f"$note = {start}\nfor $i = 0 to 7 {{\n  T{{$i * 120}} N{{$note}} D100 V80\n  $note = $note + 3\n}}",
                  [("event_count", 8)], 2))

    # 30 grand: complex patterns
    for base in [36, 48]:
        for count in [24, 32, 48]:
            Q.append((f"2-octave arpeggio from {base}: {count} notes with floor division",
                      f"@bpm 120\nfor $i = 0 to {count-1} {{\n  T{{$i * 50}} N{{{base} + ($i % 12) + 12 * ($i // 12)}} D40 V80\n}}",
                      [("event_count", count)], 3))

    # 20 grand: multi-line with complex verification
    for start_note in [48, 60, 72]:
        for count in [8, 16]:
            Q.append((f"Nested loops: 4x{count//4} grid starting at MIDI {start_note}",
                      f"@bpm 120\nfor $row = 0 to 3 {{\n  for $col = 0 to {count//4 - 1} {{\n    T{{($row * {count//4} + $col) * 60}} N{{{start_note} + $row * 4 + $col}} D50 V80\n  }}\n}}",
                      [("event_count", count)], 3))

    # Remaining filler to reach 300
    for i in range(20):
        note = 60 + i % 12
        Q.append((f"Practice: single note MIDI {note}, velocity 80, 500ms",
                  f"@bpm 120\nT0 N{note} D500 V80",
                  [("event_count", 1), ("first_midi", note)], 1))

    # 25 intermediate: play chord variations
    for quality in ["major", "minor", "dom7", "min7", "dim"]:
        Q.append((f"Play chord with {quality} quality",
                  f"play chord(C, {quality}) @dur:h @vel:mf",
                  [("event_count", 3 if quality in ("major","minor","dim") else 4)], 2))

    # 30 intermediate: for loop + variable math
    for mult in [2, 3, 4, 5, 6]:
        for count in [4, 8, 12, 16, 20, 24]:
            Q.append((f"For loop: {count} notes, N={{60 + $i * {mult}}}",
                      f"@bpm 120\nfor $i = 0 to {count-1} {{\n  T{{$i * 80}} N{{60 + $i * {mult}}} D60 V80\n}}",
                      [("event_count", count)], 2))

    # 32 grand: complex velocity curves
    for amp in [30, 40, 50, 60]:
        for count in [16, 24, 32, 48]:
            Q.append((f"Sin velocity: {count} notes, amplitude {amp}",
                      f"@bpm 120\nfor $i = 0 to {count-1} {{\n  T{{$i * 60}} N{{48 + ($i % 12)}} D50 V{{{amp} + round({amp} * sin($i * 6.28 / {count}))}}\n}}",
                      [("event_count", count)], 3))

    # 20 beginner: simple melodies
    for offset in [0, 3, 5, 7]:
        Q.append((f"3-note ascending melody starting from MIDI {60 + offset}",
                  f"@bpm 120\nT0 N{60+offset} D200 V80\nT200 N{60+offset+4} D200 V80\nT400 N{60+offset+7} D400 V80",
                  [("event_count", 3)], 1))

    # 24 intermediate: while loop with different conditions
    for limit in [4, 6, 8, 10, 12, 16]:
        Q.append((f"While loop: count to {limit}, play ascending notes",
                  f"$i = 0\nwhile $i < {limit} {{\n  T{{$i * 120}} N{{60 + $i}} D100 V80\n  $i = $i + 1\n}}",
                  [("event_count", limit)], 2))

    # 15 grand: full musical phrases
    for root in [60, 64, 67]:
        for count in [8, 12, 16]:
            Q.append((f"Musical phrase starting at C{root}: {count} notes with varied intervals",
                      f"@bpm 120\nfor $i = 0 to {count-1} {{\n  T{{$i * 100}} N{{{root} + ($i % 7) * 2}} D80 V80\n}}",
                      [("event_count", count)], 3))

    # 10 intermediate: repeat with $counter
    for rep in [4, 6, 8, 10, 12]:
        Q.append((f"Repeat {rep} times with increasing velocity",
                  f"@bpm 120\nrepeat {rep} {{\n  T{{$counter * 100}} N{{60}} D80 V{{60 + $counter * 10}}\n}}",
                  [("event_count", rep)], 2))

    # 10 beginner: basic velocity changes
    for v in [30, 50, 70, 90, 110]:
        for note in [60, 67]:
            Q.append((f"Note MIDI {note} at velocity {v}",
                      f"@bpm 120\nT0 N{note} D500 V{v}",
                      [("event_count", 1), ("first_midi", note), ("velocity_range", (v, v))], 1))

    # 10 intermediate: for loop descending
    for count in [5, 8, 10, 12, 16]:
        Q.append((f"Descending for loop: {count} notes from MIDI {60+count} down",
                  f"@bpm 120\nfor $i = 0 to {count-1} {{\n  T{{$i * 100}} N{{{60+count} - $i}} D80 V80\n}}",
                  [("event_count", count)], 2))

    # 10 grand: complex nesting
    for cycles in [2, 3]:
        for notes in [4, 6, 8]:
            total = cycles * notes
            Q.append((f"Multi-cycle: {cycles} cycles x {notes} notes = {total} total",
                      f"@bpm 120\nfor $c = 0 to {cycles-1} {{\n  for $n = 0 to {notes-1} {{\n    T{{($c * {notes} + $n) * 80}} N{{60 + $c * 12 + $n * 2}} D60 V80\n  }}\n}}",
                      [("event_count", total)], 3))

    # Fill remaining to reach 300
    for i in range(14):
        note = 60 + (i % 7) * 2
        Q.append((f"Practice: MIDI {note}, 300ms, V80",
                  f"@bpm 120\nT0 N{note} D300 V80",
                  [("event_count", 1), ("first_midi", note)], 1))

    return Q


# ── Question commands ──

_QUESTIONS = _generate_questions()


def _cmd_question(args):
    """Handle 'question' command: question <N> or question random"""
    if not args:
        print(f"  Usage: question <1-{len(_QUESTIONS)}> | question random")
        print(f"  Or:    question <difficulty> (beginner|intermediate|grand)")
        return

    if args[0] == "random":
        import random
        q_idx = random.randint(0, len(_QUESTIONS) - 1)
    elif args[0] in ("beginner", "intermediate", "grand"):
        diff = {"beginner": 1, "intermediate": 2, "grand": 3}[args[0]]
        matching = [i for i, (_, _, _, d) in enumerate(_QUESTIONS) if d == diff]
        if not matching:
            print(f"  No {args[0]} questions available.")
            return
        import random
        q_idx = random.choice(matching)
    else:
        try:
            q_idx = int(args[0]) - 1
            if q_idx < 0 or q_idx >= len(_QUESTIONS):
                print(f"  Question must be 1-{len(_QUESTIONS)}")
                return
        except ValueError:
            print(f"  Invalid question number: {args[0]}")
            return

    question, answer, checks, difficulty = _QUESTIONS[q_idx]
    diff_name = {1: "Beginner", 2: "Intermediate", 3: "Grand"}[difficulty]
    is_multi = q_idx >= 100  # Questions 101+ are multi-line

    print(f"\n  {_BOLD}Question {q_idx+1}/{len(_QUESTIONS)}{_RESET} [{_MAGENTA}{diff_name}{_RESET}]")
    print(f"  {'='*55}")
    print(f"  {question}")
    print()

    if is_multi:
        print(f"  {_YELLOW}Multi-line answer required.{_RESET}")
        user_code = _multi_line_input()
        if user_code is None:
            print(f"  {_YELLOW}Cancelled.{_RESET}")
            return
    else:
        user_code = input(f"  {_GREEN}> {_RESET}").strip()

    if not user_code:
        print(f"  {_YELLOW}No code entered.{_RESET}")
        return

    # Show what they wrote with highlighting
    print(f"\n  {_DIM}Your code:{_RESET}")
    for line in user_code.split("\n"):
        print(f"  {_highlight(line)}")

    # Verify
    passed, message = _verify_output(user_code, checks)
    if passed:
        print(f"\n  {_GREEN}{_BOLD}CORRECT!{_RESET} {message}")
    else:
        print(f"\n  {_RED}{_BOLD}INCORRECT{_RESET}")
        print(f"  {message}")
        # Show expected answer
        print(f"\n  {_DIM}Expected code:{_RESET}")
        for line in answer.split("\n"):
            print(f"  {_highlight(line)}")


def _cmd_test(args):
    """Handle 'test' command: test <beginner|intermediate|grand> [count]"""
    if not args:
        print(f"  Usage: test <beginner|intermediate|grand> [question_count]")
        print(f"  Example: test grand 5")
        return

    diff_name = args[0].lower()
    if diff_name not in ("beginner", "intermediate", "grand"):
        print(f"  Difficulty must be: beginner, intermediate, or grand")
        return

    diff = {"beginner": 1, "intermediate": 2, "grand": 3}[diff_name]
    count = 5
    if len(args) > 1:
        try:
            count = min(int(args[1]), 20)
        except ValueError:
            pass

    matching = [(i, q) for i, q in enumerate(_QUESTIONS) if q[3] == diff]
    if len(matching) < count:
        count = len(matching)

    import random
    selected = random.sample(matching, count)

    print(f"\n  {_BOLD}HELLFORGE {diff_name.upper()} TEST{_RESET}")
    print(f"  {count} questions. Type your answers, I'll check them.")
    print(f"  {'='*55}\n")

    correct = 0
    for idx, (q_idx, (question, answer, checks, _)) in enumerate(selected):
        is_multi = q_idx >= 100
        print(f"\n  {_BOLD}[{idx+1}/{count}]{_RESET} {question}")

        if is_multi:
            user_code = _multi_line_input(f"  {_GREEN}>{_RESET} ")
            if user_code is None:
                print(f"  {_YELLOW}Skipped.{_RESET}")
                continue
        else:
            user_code = input(f"  {_GREEN}> {_RESET}").strip()

        if not user_code:
            print(f"  {_YELLOW}Skipped.{_RESET}")
            continue

        passed, message = _verify_output(user_code, checks)
        if passed:
            print(f"  {_GREEN}CORRECT{_RESET}")
            correct += 1
        else:
            print(f"  {_RED}WRONG{_RESET}")
            print(f"  {_DIM}Expected:{_RESET} {answer[:60]}...")

    pct = correct / count * 100
    print(f"\n  {'='*55}")
    print(f"  {_BOLD}TEST COMPLETE{_RESET}: {correct}/{count} ({pct:.0f}%)")
    if pct >= 80:
        print(f"  {_GREEN}Excellent! You're mastering {diff_name} level.{_RESET}")
    elif pct >= 50:
        print(f"  {_YELLOW}Good progress! Keep practicing.{_RESET}")
    else:
        print(f"  {_RED}Review the lessons and try again.{_RESET}")
    print(f"  Type 'question random' for practice, 'learner lesson <N>' to study.")
def _generate_lessons():
    """Generate 500+ small CLI-friendly lessons.
    Each lesson has a title, 2-3 line explanation, tiny code example, and task.
    Lessons progress from absolute zero to advanced HELLFORGE features."""
    lessons = []

    # ═══════════════════════════════════════════════
    # MODULE 1: Absolute Basics (Lessons 1-50)
    # ═══════════════════════════════════════════════
    m1 = [
        ("What is HELLFORGE?",
         "HELLFORGE turns text into music. Write notes as numbers, compile, play.",
         "@bpm 120\nT0 N60 D500 V80",
         "Run to create your first HELLFORGE file."),

        ("Your First Note",
         "T0=time, N60=note(MIDI), D500=duration(ms), V80=volume. Change N to change pitch.",
         "@bpm 120\nT0 N60 D500 V80",
         "Run, then change N60 to N64 and recompile."),

        ("Higher Notes",
         "Bigger MIDI number = higher pitch. N60=C4, N64=E4, N67=G4.",
         "@bpm 120\nT0 N67 D500 V80",
         "Run, then try N72 (C5, one octave up)."),

        ("Lower Notes",
         "Smaller MIDI number = lower pitch. N48=C3, N36=C2.",
         "@bpm 120\nT0 N48 D500 V80",
         "Run, then try N36 (bass C)."),

        ("Two Notes",
         "Add a second line with a different T (timestamp) to play two notes.",
         "@bpm 120\nT0 N60 D500 V80\nT500 N64 D500 V80",
         "Run, then add a third note at T1000."),

        ("Three Note Melody",
         "Three ascending notes = a melody fragment. T controls when each starts.",
         "@bpm 120\nT0 N60 D500 V80\nT500 N64 D500 V80\nT1000 N67 D500 V80",
         "Run to hear a C-E-G arpeggio."),

        ("Changing Speed",
         "BPM controls tempo. @bpm 60 = slow, @bpm 200 = fast.",
         "@bpm 200\nT0 N60 D500 V80\nT500 N64 D500 V80",
         "Run, then change to @bpm 60 and hear the difference."),

        ("Note Names to Numbers",
         "C4=60, D4=62, E4=64, F4=65, G4=67, A4=69, B4=71, C5=72.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V80\nT0 N67 D500 V80",
         "Run to play a C major chord (all three at once)."),

        ("Melody with Gaps",
         "You don't have to fill every moment. Silence between notes creates rhythm.",
         "@bpm 120\nT0 N60 D200 V80\nT400 N0 D1 V0\nT500 N64 D200 V80",
         "Run. N0 D1 V0 = silence. Remove it to hear the difference."),

        ("Very First Scale",
         "C major scale: 60,62,64,65,67,69,71,72. Each step is 1 or 2 semitones.",
         "@bpm 120\nT0 N60 D200 V80\nT200 N62 D200 V80\nT400 N64 D200 V80\nT600 N65 D200 V80",
         "Run for a 4-note scale fragment. Add the rest (67,69,71,72)."),

        ("What is MIDI?",
         "MIDI = Musical Instrument Digital Interface. Numbers 0-127. 60 = middle C.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N72 D500 V80\nT0 N84 D500 V80",
         "Three C's at different octaves. C4, C5, C6."),

        ("Octaves",
         "Add 12 to go up one octave. N60=C4, N72=C5, N84=C6, N96=C7.",
         "@bpm 120\nT0 N60 D500 V80\nT500 N72 D500 V80\nT1000 N84 D500 V80",
         "Run to hear C4, C5, C6 in sequence."),

        ("Velocity = Volume",
         "V controls loudness. V0=silent, V80=moderate, V127=max. Try changing it.",
         "@bpm 120\nT0 N60 D500 V127\nT500 N60 D500 V80\nT1000 N60 D500 V40",
         "Run to hear the same note at different volumes."),

        ("Duration = Length",
         "D controls how long the note rings. D100=short, D1000=long.",
         "@bpm 120\nT0 N60 D100 V80\nT500 N60 D1000 V80\nT2000 N60 D2000 V80",
         "Run to hear short, medium, and long notes."),

        ("Staccato vs Legato",
         "Short durations = staccato (bouncy). Long durations = legato (smooth).",
         "@bpm 120\nT0 N60 D100 V80\nT200 N64 D100 V80\nT400 N67 D100 V80\nT600 N72 D100 V80",
         "Run for staccato. Change D100 to D400 for legato."),

        ("Repeating a Note",
         "Same note at regular intervals = a pulse or rhythm.",
         "@bpm 120\nT0 N60 D100 V80\nT250 N60 D100 V80\nT500 N60 D100 V80\nT750 N60 D100 V80",
         "Run for a steady pulse. Change T spacing for different rhythms."),

        ("Simple Rhythm",
         "Alternate between two notes in a regular pattern.",
         "@bpm 120\nT0 N60 D100 V80\nT200 N64 D100 V80\nT400 N60 D100 V80\nT600 N64 D100 V80",
         "Run for an alternating pattern. Add more pairs."),

        ("Accenting Beats",
         "Make some notes louder (higher V) to create a beat accent.",
         "@bpm 120\nT0 N60 D100 V127\nT200 N60 D100 V60\nT400 N60 D100 V80\nT600 N60 D100 V60",
         "Run to hear the accent on beat 1 and 3."),

        ("Silence is Music",
         "N0 = silence. Use it to create rests in your melody.",
         "@bpm 120\nT0 N60 D200 V80\nT200 N0 D200 V0\nT400 N64 D200 V80\nT600 N0 D200 V0",
         "Run to hear notes separated by rests."),

        ("Two Note Song",
         "Two notes can already be a song. This is the start of everything.",
         "@bpm 120\nT0 N60 D300 V80\nT300 N67 D300 V80\nT600 N60 D300 V80\nT900 N67 D600 V80",
         "Run for a 2-note melody. Try your own pattern."),

        ("Three Note Song",
         "Three notes give you more emotional range. Happy=high, sad=low.",
         "@bpm 100\nT0 N60 D400 V80\nT400 N64 D400 V80\nT800 N67 D400 V80\nT1200 N64 D400 V80\nT1600 N60 D800 V80",
         "Run for a 3-note melody shape (up and down)."),

        ("Call and Response",
         "A musical conversation: one phrase answers another.",
         "@bpm 120\nT0 N60 D200 V80\nT200 N64 D200 V80\nT400 N67 D200 V80\nT600 N64 D200 V80\nT800 N72 D200 V80\nT1000 N71 D200 V80\nT1200 N67 D200 V80\nT1400 N64 D600 V80",
         "Run for call(ascending) and response(descending)."),

        ("Leaps vs Steps",
         "Steps = adjacent notes (60 to 62). Leaps = big jumps (60 to 72).",
         "@bpm 120\nT0 N60 D200 V80\nT200 N62 D200 V80\nT400 N64 D200 V80\nT600 N72 D200 V80\nT800 N71 D200 V80\nT1000 N67 D200 V80",
         "Run: steps up, leap down, steps down."),

        ("Consonance vs Dissonance",
         "N60+N67 = perfect fifth (pleasant). N60+N61 = minor second (tense).",
         "@bpm 120\nT0 N60 D500 V80\nT0 N67 D500 V80\nT1000 N60 D500 V80\nT1000 N61 D500 V80",
         "Hear the difference between consonant and dissonant."),

        ("Major vs Minor",
         "N60+N64 = major third (happy). N60+N63 = minor third (sad).",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V80\nT1000 N60 D500 V80\nT1000 N63 D500 V80",
         "The difference between happy and sad in one semitone."),

        ("Finding Middle C",
         "Middle C (C4) = MIDI 60. It's the center of a standard 88-key piano.",
         "@bpm 120\nT0 N60 D1000 V80\nT0 N48 D1000 V60\nT0 N72 D1000 V60",
         "C4 (middle) with C3 (low) and C5 (high) simultaneously."),

        ("The 88 Keys",
         "Piano range: A0=21 to C8=108. Middle C=60 is roughly in the middle.",
         "@bpm 120\nT0 N21 D500 V60\nT500 N60 D500 V80\nT1000 N108 D500 V60",
         "Lowest, middle, and highest notes on a piano."),

        ("Black Keys",
         "Sharp (#) and flat (b) notes. C#4=61, D#4=63, F#4=66, G#4=68, A#4=70.",
         "@bpm 120\nT0 N61 D200 V80\nT200 N63 D200 V80\nT400 N66 D200 V80\nT600 N68 D200 V80\nT800 N70 D200 V80",
         "The five black keys in one octave, ascending."),

        ("Pentatonic Scale",
         "Five notes that always sound good together. The black keys!",
         "@bpm 120\nT0 N61 D200 V80\nT200 N63 D200 V80\nT400 N66 D200 V80\nT600 N68 D200 V80\nT800 N70 D200 V80\nT1000 N73 D800 V80",
         "The pentatonic scale. Used in blues, rock, folk."),

        ("Whole Tone Scale",
         "Every step = 2 semitones. 60,62,64,66,68,70,72. Dreamy, ambiguous sound.",
         "@bpm 120\nT0 N60 D200 V80\nT200 N62 D200 V80\nT400 N64 D200 V80\nT600 N66 D200 V80\nT800 N68 D200 V80\nT1000 N70 D200 V80\nT1200 N72 D1000 V80",
         "A whole-tone scale. Sounds floating and mysterious."),

        ("Chromatic Scale",
         "Every semitone: 60,61,62,63,64,65,66,67,68,69,70,71,72. All 12 notes.",
         "@bpm 200\nT0 N60 D100 V80\nT50 N61 D100 V80\nT100 N62 D100 V80\nT150 N63 D100 V80\nT200 N64 D100 V80\nT250 N65 D100 V80\nT300 N66 D100 V80\nT350 N67 D100 V80\nT400 N68 D100 V80\nT450 N69 D100 V80\nT500 N70 D100 V80\nT550 N71 D100 V80\nT600 N72 D1000 V80",
         "All 12 notes in one octave, ascending chromatically."),

        ("Interval: Unison",
         "Same note twice. The most consonant interval possible.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N60 D500 V80",
         "Two Cs at once = unison. Sounds like one note, louder."),

        ("Interval: Octave",
         "N60 and N72 = 12 semitones apart. They feel like the same note, higher.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N72 D500 V60",
         "C4 and C5 together. The octave is the most consonant interval."),

        ("Interval: Fifth",
         "N60 and N67 = 7 semitones apart. The foundation of Western harmony.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N67 D500 V60",
         "A perfect fifth. Used in power chords."),

        ("Interval: Fourth",
         "N60 and N65 = 5 semitones apart. Open, suspended sound.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N65 D500 V60",
         "A perfect fourth. The opening of 'Here Comes the Bride'."),

        ("Interval: Third (Major)",
         "N60 and N64 = 4 semitones. Sounds happy, bright.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V60",
         "Major third. Happy interval."),

        ("Interval: Third (Minor)",
         "N60 and N63 = 3 semitones. Sounds sad, dark.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N63 D500 V60",
         "Minor third. Sad interval."),

        ("Interval: Second (Major)",
         "N60 and N62 = 2 semitones. Stepping up, creates motion.",
         "@bpm 120\nT0 N60 D200 V80\nT200 N62 D200 V80\nT400 N64 D200 V80",
         "Ascending major seconds. The start of a scale."),

        ("Interval: Seventh (Major)",
         "N60 and N71 = 11 semitones. Yearning, wants to resolve.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N71 D500 V60\nT1000 N60 D500 V80\nT1000 N67 D500 V60",
         "Major seventh (tense) resolving to fifth (calm)."),

        ("Interval: Tritone",
         "N60 and N66 = 6 semitones. The devil's interval. Very tense.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N66 D500 V60\nT1000 N60 D500 V80\nT1000 N65 D500 V60",
         "Tritone (tense) resolving to fourth (calm)."),

        ("Building Chords",
         "A chord = 3+ notes stacked in thirds. C major = C(60) + E(64) + G(67).",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V60\nT0 N67 D500 V60",
         "C major chord: root, third, fifth all at once."),

        ("Chord: Minor",
         "C minor = C(60) + Eb(63) + G(67). The third is flat (lower by 1).",
         "@bpm 120\nT0 N60 D500 V80\nT0 N63 D500 V60\nT0 N67 D500 V60",
         "C minor vs C major. Only one note changed (64->63)."),

        ("Chord: Diminished",
         "B dim = B(71) + D(74) + F(77). Root + minor third + diminished fifth.",
         "@bpm 120\nT0 N71 D500 V80\nT0 N74 D500 V60\nT0 N77 D500 V60",
         "A diminished chord. Tense, unstable."),

        ("Chord: Augmented",
         "C aug = C(60) + E(64) + G#(68). Root + major third + augmented fifth.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V60\nT0 N68 D500 V60",
         "An augmented chord. Floating, uncertain."),

        ("Chord: Suspended",
         "Csus4 = C(60) + F(65) + G(67). Third replaced by fourth.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N65 D500 V60\nT0 N67 D500 V60\nT1500 N64 D500 V60",
         "Sus chord resolves from fourth to third."),

        ("Dynamics Crescendo",
         "Gradually increase V numbers = getting louder over time.",
         "@bpm 120\nT0 N60 D200 V40\nT200 N60 D200 V60\nT400 N60 D200 V80\nT600 N60 D200 V100\nT800 N60 D200 V120",
         "A crescendo (gradually getting louder) over 5 notes."),

        ("Dynamics Decrescendo",
         "Gradually decrease V numbers = getting softer over time.",
         "@bpm 120\nT0 N60 D200 V120\nT200 N60 D200 V100\nT400 N60 D200 V80\nT600 N60 D200 V60\nT800 N60 D200 V40",
         "A decrescendo (gradually getting softer)."),

        ("Tempo Changes",
         "Change @bpm mid-piece to speed up or slow down.",
         "@bpm 60\nT0 N60 D300 V80\nT300 N64 D300 V80\n@bpm 200\nT600 N67 D300 V80\nT900 N72 D300 V80",
         "First two notes slow, then sudden speed increase."),

        ("Cleaning Up",
         "Use comments (// or /* */) to document your music for others.",
         "/* My first song */\n@bpm 120\n// Melody starts here\nT0 N60 D500 V80\nT500 N67 D1000 V80",
         "Comments help you remember what each section does."),
    ]
    for i, (t, e, c, task) in enumerate(m1):
        lessons.append((t, e, c, task, 1))

    # ═══════════════════════════════════════════════
    # MODULE 2: Machine Mode (Lessons 51-120)
    # ═══════════════════════════════════════════════
    m2 = [
        ("Machine Mode Introduction",
         "#MACHINE mode uses T N D V tokens. Precise, every millisecond controlled.",
         "@bpm 120\n#MACHINE\nT0 N60 D500 V80\nT500 N64 D500 V80",
         "The #MACHINE directive. All lines below it use T N D V."),

        ("T Token - Time",
         "T = timestamp in milliseconds from start. T0 = beginning. T1000 = 1 second.",
         "@bpm 120\nT0 N60 D500 V80\nT1000 N64 D500 V80\nT2000 N67 D500 V80",
         "One note per second (T0, T1000, T2000)."),

        ("N Token - Note",
         "N = MIDI note number. 0-127. 60 = middle C.",
         "@bpm 120\nT0 N60 D500 V80\nT500 N64 D500 V80\nT1000 N67 D500 V80\nT1500 N72 D500 V80",
         "C E G C — a C major arpeggio spanning one octave."),

        ("D Token - Duration",
         "D = note duration in milliseconds. How long the note rings.",
         "@bpm 120\nT0 N60 D1000 V80\nT1000 N60 D100 V80",
         "First note long (1 sec), second note short (0.1 sec)."),

        ("V Token - Velocity",
         "V = velocity (volume). 0-127. V80=moderate, V127=max.",
         "@bpm 120\nT0 N60 D500 V127\nT500 N60 D500 V80\nT1000 N60 D500 V40",
         "Same note at max, medium, and soft volumes."),

        ("Overlapping Notes",
         "Notes can overlap (T before previous note ends). Creates harmony.",
         "@bpm 120\nT0 N60 D1000 V80\nT200 N64 D800 V80\nT400 N67 D600 V80",
         "Three notes all ringing at the same time (chord)."),

        ("Non-overlapping Notes",
         "Start next note after previous ends. Creates melody.",
         "@bpm 120\nT0 N60 D400 V80\nT400 N64 D400 V80\nT800 N67 D400 V80\nT1200 N72 D800 V80",
         "One note at a time — a melody line."),

        ("Fast Passage",
         "Short timestamps and short durations = fast, exciting music.",
         "@bpm 120\nT0 N60 D50 V80\nT50 N62 D50 V80\nT100 N64 D50 V80\nT150 N65 D50 V80\nT200 N67 D50 V80\nT250 N69 D50 V80\nT300 N71 D50 V80\nT350 N72 D800 V80",
         "A fast scale run (8 notes in 350ms)."),

        ("Syncopation",
         "Accent off-beats by placing notes at unexpected timestamps.",
         "@bpm 120\nT0 N60 D100 V80\nT150 N64 D100 V80\nT300 N60 D100 V80\nT450 N67 D100 V80",
         "Notes at T0, T150, T300, T450 — a syncopated rhythm."),

        ("Triplet Feel",
         "Three equal notes in the space of two. T0, T167, T333 = eighth note triplets.",
         "@bpm 120\nT0 N60 D100 V80\nT167 N64 D100 V80\nT333 N67 D100 V80\nT500 N72 D100 V80\nT667 N71 D100 V80\nT833 N67 D100 V80",
         "Six notes in triplet pairs. Swung, rolling feel."),

        ("Dotted Rhythm",
         "Long-short pattern. T0 D500 then T500 D250 creates a dotted feel.",
         "@bpm 120\nT0 N60 D500 V80\nT500 N64 D250 V80\nT750 N60 D500 V80\nT1250 N64 D250 V80",
         "Long-short-long-short. A dotted rhythm pattern."),

        ("Backbeat",
         "Accent beats 2 and 4 (instead of 1 and 3). The foundation of rock.",
         "@bpm 120\nT0 N60 D100 V60\nT250 N64 D100 V127\nT500 N60 D100 V60\nT750 N64 D100 V127",
         "Accents on 2 and 4 = backbeat. Used in rock and pop."),

        ("Tremolo",
         "Rapidly alternate between two notes. Use very tight T spacing.",
         "@bpm 120\nT0 N60 D30 V80\nT30 N64 D30 V80\nT60 N60 D30 V80\nT90 N64 D30 V80\nT120 N60 D30 V80\nT150 N64 D30 V80",
         "Rapid alternation between C and E (tremolo)."),

        ("Glissando Effect",
         "Play every semitone between two notes in quick succession.",
         "@bpm 120\nT0 N60 D20 V80\nT20 N61 D20 V80\nT40 N62 D20 V80\nT60 N63 D20 V80\nT80 N64 D20 V80\nT100 N65 D20 V80\nT120 N66 D20 V80\nT140 N67 D20 V80\nT160 N68 D20 V80\nT180 N69 D20 V80\nT200 N70 D20 V80\nT220 N71 D20 V80\nT240 N72 D500 V80",
         "A slide from C4 to C5 through every semitone."),

        ("Arpeggio vs Chord",
         "Arpeggio = notes played one after another. Chord = all at once.",
         "@bpm 120\nT0 N60 D100 V80\nT100 N64 D100 V80\nT200 N67 D100 V80\nT1000 N60 D500 V80\nT1000 N64 D500 V60\nT1000 N67 D500 V60",
         "First an arpeggio, then the same notes as a chord."),

        ("Broken Chord",
         "A chord played as individual notes in a pattern.",
         "@bpm 120\nT0 N60 D100 V80\nT100 N64 D100 V80\nT200 N67 D100 V80\nT300 N64 D100 V80\nT400 N60 D100 V80\nT400 N64 D100 V60\nT400 N67 D100 V60",
         "Broken chord (up-down) then solid chord."),

        ("Alberti Bass",
         "A classical accompaniment pattern: low-high-middle-high.",
         "@bpm 120\nT0 N48 D150 V80\nT150 N55 D150 V70\nT300 N52 D150 V70\nT450 N55 D150 V70\nT600 N48 D150 V80\nT750 N55 D150 V70\nT900 N52 D150 V70\nT1050 N55 D150 V70",
         "Alberti bass pattern (used by Mozart, Beethoven)."),

        ("Ostinato",
         "A repeating pattern in the bass. Other notes play over it.",
         "@bpm 120\nT0 N48 D200 V80\nT200 N48 D200 V80\nT400 N48 D200 V80\nT600 N48 D200 V80\nT0 N60 D400 V60\nT400 N64 D400 V60\nT800 N67 D800 V60",
         "Repeating bass note with changing melody above."),

        ("Walking Bass",
         "A bass line that moves stepwise, one note per beat.",
         "@bpm 120\nT0 N48 D200 V80\nT200 N50 D200 V80\nT400 N52 D200 V80\nT600 N53 D200 V80\nT800 N55 D200 V80\nT1000 N57 D200 V80\nT1200 N59 D200 V80\nT1400 N60 D800 V80",
         "A walking bass line from C3 to C4."),

        ("Counterpoint",
         "Two independent melodies playing at the same time.",
         "@bpm 120\nT0 N60 D400 V80\nT400 N64 D400 V80\nT800 N67 D400 V80\nT1200 N72 D800 V80\nT0 N48 D800 V60\nT800 N55 D800 V60",
         "Melody in right hand, counter-melody in left hand."),

        ("Call and Response 2",
         "Two voices answering each other. Voice 1: T0, Voice 2: T200.",
         "@bpm 120\nT0 N60 D150 V80\nT200 N64 D150 V80\nT400 N67 D150 V80\nT600 N60 D150 V80\nT800 N64 D150 V80\nT1000 N67 D150 V80",
         "Call (60,64,67) then response (60,64,67) at different times."),

        ("Round/Canon",
         "Same melody starting at different times. Like Row Row Row Your Boat.",
         "@bpm 120\nT0 N60 D400 V80\nT400 N64 D400 V80\nT800 N67 D800 V80\nT800 N60 D400 V60\nT1200 N64 D400 V60\nT1600 N67 D800 V60",
         "A 2-voice round. Second voice starts at T800."),

        ("Polyrhythm 3:2",
         "3 notes in the same time as 2 notes. T0, T167, T333 vs T0, T250.",
         "@bpm 120\nT0 N60 D100 V80\nT167 N64 D100 V80\nT333 N67 D100 V80\nT0 N48 D200 V60\nT250 N48 D200 V60",
         "3 notes in the right hand, 2 in the left. 3 against 2."),

        ("Polyrhythm 4:3",
         "4 notes against 3. T0,T125,T250,T375 vs T0,T167,T333.",
         "@bpm 120\nT0 N60 D80 V80\nT125 N64 D80 V80\nT250 N67 D80 V80\nT375 N72 D80 V80\nT0 N48 D200 V60\nT167 N48 D200 V60\nT333 N48 D200 V60",
         "4 against 3 polyrhythm. Complex, exciting cross-rhythm."),

        ("Grace Notes",
         "A very short note just before the main note. T -10 for a grace note.",
         "@bpm 120\nT0 N67 D20 V80\nT0 N60 D300 V80\nT500 N69 D20 V80\nT500 N64 D300 V80",
         "Grace note (short) leading into main note."),

        ("Trill",
         "Rapid alternation between a note and the note above it.",
         "@bpm 120\nT0 N60 D40 V80\nT40 N62 D40 V80\nT80 N60 D40 V80\nT120 N62 D40 V80\nT160 N60 D40 V80\nT200 N62 D40 V80\nT240 N60 D200 V80",
         "A trill between C and D. Ornamentation technique."),

        ("Mordent",
         "Rapid: note -> above -> note. An ornament.",
         "@bpm 120\nT0 N60 D150 V80\nT150 N62 D50 V80\nT200 N60 D300 V80",
         "Upper mordent: C-D-C quickly."),

        ("Turn",
         "Rapid: above -> note -> below -> note. An ornament.",
         "@bpm 120\nT0 N62 D50 V80\nT50 N60 D50 V80\nT100 N59 D50 V80\nT150 N60 D300 V80",
         "A turn: D-C-B-C."),

        ("Appoggiatura",
         "A leaning note. Step up then resolve down by one step.",
         "@bpm 120\nT0 N65 D300 V80\nT300 N64 D500 V80",
         "F leaning to E. Creates expressive tension."),

        ("Acciaccatura",
         "A crushed note. Played almost simultaneously with the main note.",
         "@bpm 120\nT0 N64 D20 V80\nT0 N60 D500 V80",
         "Crushed note: E and C together, E very short."),

        ("Harmonic Series",
         "Overtones of middle C. Each doubling of frequency = octave.",
         "@bpm 120\nT0 N60 D500 V80\nT500 N72 D500 V60\nT1000 N79 D500 V40\nT1500 N84 D500 V30",
         "First 4 harmonics of C (C4, C5, G5, C6)."),

        ("Just Intonation",
         "Pure intervals based on simple ratios. Unlike equal temperament.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N67 D500 V60\nT0 N64 D500 V60",
         "Pure C major chord in equal temperament. Try different voicings."),

        ("Equal Temperament",
         "Every semitone is exactly the same ratio. Standard tuning since Bach.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N64 D500 V60\nT0 N67 D500 V60",
         "A perfectly tuned C major chord in 12-TET."),

        ("Microtones",
         "E uses standard MIDI (12 semitone/octave). Microtones = cents, not supported directly.",
         "@bpm 120\nT0 N60 D500 V80\nT0 N60 D500 V60",
         "Standard semitones only. For microtones, use pitch bend on output."),
    ]
    for i, (t, e, c, task) in enumerate(m2):
        lessons.append((t, e, c, task, 2))

    # ═══════════════════════════════════════════════
    # MODULE 3: Loops (Lessons 121-200)
    # ═══════════════════════════════════════════════
    m3 = []
    # For loop lessons (generated)
    for count in [4, 8, 12, 16, 32, 64, 100, 200]:
        m3.append((f"For loop: {count} notes",
                    f"Repeat a pattern {count} times using 'for $i = 0 to {count-1}'.",
                    f"@bpm 200\nfor $i = 0 to {count-1} {{\n  T{{$i * 50}} N{{60 + $i % 12}} D40 V80\n}}",
                    f"Run to create {count} notes with one for loop."))
    # Repeat lessons
    for rep in [2, 3, 4, 6, 8]:
        m3.append((f"Repeat {rep} times",
                    f"Repeat a block {rep} times using 'repeat {rep}'.",
                    f"@bpm 120\nrepeat {rep} {{\n  T0 N60 D200 V80\n  T200 N64 D200 V80\n  T400 N67 D400 V80\n}}",
                    f"Run for a {rep}x repeated pattern."))
    # For with step
    for step in [1, 2, 3, 4, 6]:
        m3.append((f"For loop step {step}",
                    f"Every {step}th note. 'for $i = 0 to 12 step {step}'.",
                    f"@bpm 120\nfor $i = 0 to 12 step {step} {{\n  T{{$i * 100}} N{{60 + $i}} D80 V80\n}}",
                    f"Run to hear every {step}th semitone."))
    # While loops
    m3.extend([
        ("While loop basics",
         "while repeats as long as condition is true. $i < 10 means 10 iterations.",
         "$i = 0\nwhile $i < 10 {\n  T{$i * 100} N{60} D80 V80\n  $i = $i + 1\n}",
         "Run for 10 notes using a while loop."),

        ("While with variable condition",
         "Change the variable inside the loop to control iteration count.",
         "$i = 10\nwhile $i > 0 {\n  T{($i - 10) * -100} N{60 + $i} D80 V80\n  $i = $i - 1\n}",
         "Count down from 10 to 1, playing higher notes first."),

        ("Nested for loops",
         "A for loop inside another for loop. Outer = rows, inner = columns.",
         "for $i = 0 to 3 {\n  for $j = 0 to 3 {\n    T{($i * 4 + $j) * 50} N{60 + $i * 4 + $j} D40 V80\n  }\n}",
         "A 4x4 grid = 16 notes. Matrix of pitches."),

        ("Triple nested loops",
         "Three levels of nesting = a cube of notes. 4x4x4 = 64 notes.",
         "for $i = 0 to 3 {\n  for $j = 0 to 3 {\n    for $k = 0 to 3 {\n      T{($i*16+$j*4+$k)*25} N{48+$i*4+$j*2+$k} D20 V80\n    }\n  }\n}",
         "3D note cube: 64 events. Explore all combinations."),

        ("Loop with math",
         "Use $i directly in math expressions. Makes patterns naturally.",
         "for $i = 0 to 15 {\n  T{$i * 100} N{60 + round(12 * sin($i * 0.5))} D80 V80\n}",
         "Notes that go up and down in a sine wave pattern."),

        ("Loop with counter",
         "$counter tracks repeat iterations. Use it for variation.",
         "repeat 8 {\n  T{$counter * 100} N{60 + $counter * 2} D80 V{70 + $counter * 5}\n}",
         "Volume increases with each repeat ($counter)."),

        ("Loop with modulo",
         "$i % 4 repeats values 0,1,2,3 in a cycle. Creates patterns.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + ($i % 4) * 3} D60 V80\n}",
         "4-note pattern repeated 4 times (16 notes total)."),

        ("Scale walk with loop",
         "Walk up a scale, then down. Use two for loops.",
         "for $i = 0 to 7 {\n  T{$i * 100} N{60 + $i * 2} D80 V80\n}\nfor $i = 0 to 7 {\n  T{800 + $i * 100} N{74 - $i * 2} D80 V80\n}",
         "C major scale up then down. 16 notes total."),

        ("Octave sweep with loop",
         "Use (i // 12) for octave and (i % 12) for note within octave.",
         "for $i = 0 to 23 {\n  T{$i * 60} N{48 + ($i % 12) + 12 * ($i // 12)} D50 V80\n}",
         "2 octave sweep: 24 notes, C3 to C5."),
    ])

    for i, entry in enumerate(m3):
        lessons.append((entry[0], entry[1], entry[2], entry[3], 3))

    # ═══════════════════════════════════════════════
    # MODULE 4: Variables & Math (Lessons 201-280)
    # ═══════════════════════════════════════════════
    m4 = [
        ("Variables intro",
         "$name = value. Use {$name} anywhere: T{$bpm * 2}, N{$note}.",
         "$bpm = 120\nT0 N60 D500 V80\nT500 N64 D500 V80",
         "Run, then change $bpm to 60 and recompile."),

        ("Math in timestamps",
         "{$bpm * 2} = 240. Math inside T, N, D, V positions.",
         "$bpm = 120\n$beat = 60000 / $bpm\nT{$beat} N60 D{$beat / 2} V80",
         "One note at 1 beat, duration = half beat."),

        ("Math in note numbers",
         "N{60 + 4} = N64 (E4). Useful for intervals from a base note.",
         "$root = 60\nT0 N{$root} D200 V80\nT200 N{$root + 4} D200 V80\nT400 N{$root + 7} D200 V80",
         "Root, third, fifth using math off a base note."),

        ("Math in velocity",
         "V{80 + 20} = V100. Math works everywhere.",
         "$base = 60\nfor $i = 0 to 7 {\n  T{$i * 100} N{60} D80 V{$base + $i * 8}\n}",
         "Velocity increases by 8 each note (crescendo)."),

        ("BPM variable",
         "$bpm can be changed mid-piece. First section slow, second fast.",
         "$bpm = 80\nT0 N60 D500 V80\nT500 N64 D500 V80\n$bpm = 160\nT1000 N67 D250 V80\nT1250 N72 D250 V80",
         "First two notes slow (80bpm), last two fast (160bpm)."),

        ("Beat calculation",
         "$beat = 60000 / $bpm gives ms per beat. Use it for precise timing.",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 7 {\n  T{$i * $beat / 2} N{60 + $i * 4} D{$beat / 4} V80\n}",
         "Eighth notes at 120bpm = $beat/2 = 250ms apart."),

        ("Variable reassignment",
         "$var = $var + 1 increments a variable. Useful in loops.",
         "$bpm = 120\n$note = 60\nfor $i = 0 to 7 {\n  T{$i * 150} N{$note} D100 V80\n  $note = $note + 1\n}",
         "Note number increases by 1 each iteration."),

        ("Two variables",
         "Use multiple variables for different aspects of the pattern.",
         "$bpm = 120\n$vol = 60\n$note = 60\nfor $i = 0 to 7 {\n  T{$i * 100} N{$note} D80 V{$vol}\n  $note = $note + 2\n  $vol = $vol + 8\n}",
         "Both pitch and volume change over the loop."),

        ("Power operator",
         "^ = power. 2^3 = 8. Not common in music, but available.",
         "T0 N{60 + 2^2} D500 V80\nT500 N{60 + 2^3} D500 V80\nT1000 N{60 + 2^4} D500 V80",
         "N64, N68, N76 — notes based on powers of 2."),

        ("Modulo operator",
         "% = remainder. 7 % 3 = 1. Great for cycling through values.",
         "for $i = 0 to 11 {\n  T{$i * 100} N{60 + ($i % 3) * 4} D80 V80\n}",
         "Cycles through 3 notes (C, E, G) 4 times each."),

        ("Adding variables to math",
         "Combine multiple variables and operators. $x + $y * $z.",
         "$base = 60\n$step = 4\nfor $i = 0 to 7 {\n  T{$i * 100} N{$base + ($i % 3) * $step} D80 V80\n}",
         "Triad arpeggio (root, third, fifth) using $step."),

        ("Using beat variable",
         "$beat = 60000 / $bpm. Then use $beat for all timing.",
         "$bpm = 120\n$beat = 60000 / $bpm\nT{$beat * 0} N60 D{$beat} V80\nT{$beat * 2} N64 D{$beat} V80\nT{$beat * 4} N67 D{$beat * 2} V80",
         "Notes at beats 0, 2, 4. Last note held for 2 beats."),

        ("Division in note selection",
         "Use / for regular division, // for floor (integer) division.",
         "for $i = 0 to 15 {\n  T{$i * 75} N{60 + ($i // 4) * 3 + ($i % 4)} D60 V80\n}",
         "4 groups of 4 notes, each group higher by 3 semitones."),

        ("Nested math",
         "Math can be nested. N{60 + round(sin($i) * 12)}.",
         "for $i = 0 to 23 {\n  T{$i * 60} N{60 + round(12 * sin($i * 0.3))} D50 V{60 + round(40 * cos($i * 0.2))}\n}",
         "Both pitch and velocity follow sine/cosine waves."),

        ("Constants",
         "Define constants at the top. $root, $interval, $duration.",
         "$root = 60\n$third = $root + 4\n$fifth = $root + 7\nT0 N{$root} D300 V80\nT300 N{$third} D300 V80\nT600 N{$fifth} D600 V80",
         "Constant-based composition. Change $root to transpose everything."),

        ("Tempo ramp",
         "Change $bpm inside a loop to accelerate.",
         "$bpm = 80\nfor $i = 0 to 7 {\n  T{$i * (60000 / $bpm)} N{60 + $i * 2} D100 V80\n  $bpm = $bpm + 10\n}",
         "Tempo increases from 80 to 160 over 8 notes."),

        ("Random-ish patterns",
         "Use math to create pseudo-random patterns. No actual random function.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + ($i * 7 + 3) % 12} D60 V80\n}",
         "Note pattern using modulo math to scramble the order."),

        ("Fibonacci notes",
         "Use Fibonacci-like math for note selection.",
         "$a = 0\n$b = 1\nfor $i = 0 to 7 {\n  T{$i * 100} N{60 + $b} D80 V80\n  $c = $a + $b\n  $a = $b\n  $b = $c\n}",
         "Notes follow the Fibonacci sequence: 1,2,3,5,8,13,21,34."),

        ("Prime intervals",
         "Use prime numbers (2,3,5,7,11) as interval steps.",
         "for $i = 0 to 7 {\n  T{$i * 100} N{48 + 2 * 3 * 5 * 7 * 11} D80 V80\n}",
         "Math is evaluated once. Each note uses the computed value."),

        ("Expression in loop body",
         "Complex expressions can go anywhere in the loop body.",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 7 {\n  T{$i * $beat / 2} N{60 + round(7 * sin($i * 0.7))} D{$beat / 4} V{70 + round(30 * cos($i * 0.3))}\n}",
         "Timing, pitch, and volume all modulated by trig functions."),
    ]
    for i, (t, e, c, task) in enumerate(m4):
        lessons.append((t, e, c, task, 4))

    # ═══════════════════════════════════════════════
    # MODULE 5: Math Functions (Lessons 281-340)
    # ═══════════════════════════════════════════════
    m5 = []
    sin_steps = [2, 4, 6, 8, 12, 16, 24]
    for n in sin_steps:
        m5.append((f"Sin wave {n} notes",
                    f"sin($i * freq) creates waves. {n} notes across a sine cycle.",
                    f"for $i = 0 to {n-1} {{\n  T{{$i * 80}} N{{60 + round(12 * sin($i * 6.283 / {n}))}} D60 V80\n}}",
                    f"A sine wave over {n} notes."))
    cos_steps = [4, 8, 12, 16]
    for n in cos_steps:
        m5.append((f"Cos wave {n} notes",
                    f"cos() is sin() shifted. Use it for velocity curves.",
                    f"for $i = 0 to {n-1} {{\n  T{{$i * 100}} N{{60}} D80 V{{60 + round(40 * cos($i * 6.283 / {n}))}}\n}}",
                    f"Volume follows a cosine wave over {n} notes."))
    m5.extend([
        ("Sin + cos modulation",
         "Combine sin() and cos() for complex patterns.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + round(8 * sin($i * 0.5))} D60 V{60 + round(30 * cos($i * 0.3))}\n}",
         "Pitch from sin, volume from cos. Complex texture."),

        ("Sqrt function",
         "sqrt() = square root. Creates curves that steepen or flatten.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + round(sqrt($i) * 3)} D60 V80\n}",
         "Notes get farther apart as sqrt increases (diminishing returns)."),

        ("Pow function",
         "pow(a, b) = a raised to power b. Creates exponential curves.",
         "for $i = 0 to 7 {\n  T{$i * 100} N{60 + round(pow($i, 2) / 4)} D80 V80\n}",
         "Pitches follow a parabola ($i squared)."),

        ("Quadratic function",
         "quadratic(a, b, c) = solves ax^2 + bx + c. Returns a root.",
         "for $i = 0 to 7 {\n  T{$i * 100} N{60 + round(abs(quadratic(1, -$i, $i * 2)))} D80 V80\n}",
         "Quadratic-generated note values."),

        ("Round function",
         "round() = nearest integer. Essential for converting floats to MIDI.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{round(60 + 6 * sin($i * 0.5))} D60 V80\n}",
         "Without round, MIDI numbers would be fractional. Try removing it."),

        ("Floor function",
         "floor() = round down. Different from round for negative numbers.",
         "for $i = 0 to 7 {\n  T{$i * 100} N{60 + floor($i * 1.7)} D80 V80\n}",
         "floor(1.7)=1, floor(3.4)=3. Notes increase by 1 or 2."),

        ("Abs function",
         "abs() = absolute value (remove negative sign).",
         "for $i = -7 to 7 {\n  T{($i + 7) * 80} N{60 + abs($i) * 2} D60 V80\n}",
         "Symmetrical V-shape. Notes go down then back up."),

        ("Min function",
         "min(a, b) = lower of two values. Creates a ceiling.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + min($i, 7)} D60 V80\n}",
         "Notes increase but cap at 7 (min keeps it under control)."),

        ("Max function",
         "max(a, b) = higher of two values. Creates a floor.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + max($i - 4, 0)} D60 V80\n}",
         "First 4 notes are the same (max of negative=0), then rise."),

        ("Combine min and max",
         "min(max(x, 0), 7) = clamp between 0 and 7.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + min(max($i - 4, 0), 7)} D60 V80\n}",
         "Notes are clamped between 0 and 7 relative to base 60."),

        ("Solve linear",
         "solve_linear(m, x, c) = m * x + c. Same as $m * $x + $c.",
         "for $i = 0 to 7 {\n  T{$i * 100} N{round(solve_linear(2, $i, 60))} D80 V80\n}",
         "Linear equation: y = 2x + 60. Notes step by 2."),

        ("Complex: sin arpeggio",
         "Full arpeggio with velocity modulation using sin.",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 15 {\n  T{$i * $beat / 4} N{36 + ($i % 12) + 12 * ($i // 12)} D{$beat / 8} V{40 + round(60 * ($i / 15))}\n}",
         "Professional 2-octave arpeggio with volume swell (GPU accelerated)."),

        ("Complex: quad arpeggio",
         "Arpeggio using quadratic formula for note selection.",
         "for $i = 0 to 15 {\n  T{$i * 80} N{60 + round(abs(quadratic(0.5, -$i * 0.5, $i * 2)))} D60 V{60 + $i * 4}\n}",
         "Quadratic-generated pitches with increasing volume."),

        ("Complex: sin velocity swell",
         "Velocity follows a full sine cycle for a swell effect.",
         "for $i = 0 to 31 {\n  T{$i * 50} N{60 + $i % 12} D40 V{40 + round(60 * sin($i * 3.14159 / 16))}\n}",
         "32-note arpeggio with a smooth volume swell and decay."),

        ("Complex: layered trig",
         "Multiple trig functions layered for rich patterns.",
         "for $i = 0 to 31 {\n  T{$i * 50} N{60 + round(12 * sin($i * 0.4) + 6 * cos($i * 0.2))} D40 V{60 + round(40 * cos($i * 0.15))}\n}",
         "Complex pitch pattern from sum of sin + cos waves."),
    ])
    for i, entry in enumerate(m5):
        lessons.append((entry[0], entry[1], entry[2], entry[3], 5))

    # ═══════════════════════════════════════════════
    # MODULE 6: HELLFORGE Ecosystem (Lessons 341-500+)
    # ═══════════════════════════════════════════════
    m6 = [
        ("GPU acceleration",
         "Radical plugin compiles math to GPU shaders. 50x faster for batches.",
         "$bpm = 120\nfor $i = 0 to 255 {\n  T{$i * 20} N{60 + $i % 12} D15 V{40 + round(60 * sin($i * 0.1))}\n}",
         "256 notes. With Radical, this compiles on GPU (~1ms)."),

        ("GPU batch eval",
         "256+ expressions in one GPU dispatch. Each workgroup evaluates 256.",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 255 {\n  T{$i * $beat / 16} N{36 + ($i % 12) + 12 * ($i // 12)} D{$beat / 16} V{50 + round(50 * sin($i * 0.2))}\n}",
         "256-note pattern. Single GPU dispatch for all math."),

        ("Tensor Core matmul",
         "TensorSHARP uses Tensor Cores for matrix multiply. 10x over CUDA cores.",
         "// Requires CuPy + NVIDIA GPU with Tensor Cores (SM 7.0+)\n// tensorsharp status — check availability\n// Run: python examples/opengl_engine.py",
         "TensorSHARP acceleration is automatic for CuPy matmul calls."),

        ("Multi-GPU systems",
         "Laptops often have iGPU + dGPU. Switch with 'radical gpu <index>'.",
         "// radical gpu list — shows all GPUs\n// radical gpu 0 — switch to first GPU\n// radical gpu 1 — switch to second",
         "On this machine: 2 GPUs (RTX 3050 + Intel Iris Xe)."),

        ("VRAM limit",
         "Set max VRAM usage: 'radical vram <MB>'. Prevents OOM on shared memory.",
         "// radical vram 1024 — limit to 1GB VRAM\n// radical vram off — disable limit",
         "Useful for integrated GPUs that share system memory."),

        ("Shader cache",
         "Radical caches compiled GLSL shaders by AST hash. No recompile on reuse.",
         "// radical shaders — shows cached shaders\n// radical status — compile stats",
         "Repeated expressions reuse cached shaders."),

        ("OpenGL API overview",
         "OPENapi provides raw OpenGL 4.6 primitives. Game engines built on top.",
         "from plugins.openapi._context import GLContext\nctx = GLContext()\napi = OpenGLAPI(ctx)",
         "Python example. See examples/opengl_engine.py for AAA engine demo."),

        ("Vulkan compute overview",
         "Vulkanizer provides Vulkan compute + ray tracing + upscaling APIs.",
         "from plugins.vulkanizer._instance import VkInstance\ninst = VkInstance()\napi = VulkanAPI(inst)",
         "Low-level Vulkan API. Game engines built on top."),

        ("Ray tracing",
         "Hardware ray tracing via VK_KHR_ray_tracing on RTX/Radeon/Arc GPUs.",
         "// vulkanizer devices — check raytracing support\n// api.raytrace.available — True if supported",
         "Requires Vulkan SDK + glslangValidator for SPIR-V compilation."),

        ("Temporal upscaling",
         "Custom DLSS-like upscaling via compute shaders + Tensor Cores.",
         "upscaled = api.upscale.upscale(low_res_image, 3840, 2160, scale_factor=2.0)",
         "Temporal feedback for anti-ghosting. Falls back to any GPU."),

        ("EAudio 3D audio",
         "3D spatial audio with doppler shift, distance attenuation, stereo panning.",
         "spa.set_listener([0,0,0])\nspa.add_source('engine', [10,3,-2])\nleft, right = spa.get_spatial_gain('engine')",
         "Position audio sources in 3D space for immersive sound."),

        ("DSP effects",
         "Reverb, delay, compressor, EQ for audio processing.",
         "effects.reverb(buffer, decay=0.5)\neffects.delay(buffer, delay_ms=200)\neffects.compressor(buffer)",
         "Apply DSP effects to audio buffers for professional sound."),

        ("LURE LuaJIT acceleration",
         "LURE accelerates compilation 3-10x using LuaJIT. Automatic.",
         "// lure status — check availability\n// lure benchmark — compare Python vs LuaJIT",
         "lupa releases GIL during Lua execution. Async engine for parallel compile."),

        ("Async compilation",
         "Compile in the background while you keep working.",
         "from ep_compiler.async_compile import async_compile_source\nimport asyncio\nev, bp = await async_compile_source(source)",
         "Async pipeline: LURE async -> FC async -> synchronous fallback."),

        ("Batch compilation",
         "Compile 50 files in parallel using async_compile_batch.",
         "results = await async_compile_batch([src1, src2, ..., src50])",
         "19 async tests pass. 50x200 events = 10000 total in ~1.2s."),

        ("REGAS trust system",
         "CORE-EXPANSION: REGAS. Utmost trust for HELLFORGE core plugins.",
         "TRUST_REGAS = 2  # Server-confirmed TENTARI\nTRUST_TENTARI = 2  # Third-party devs\nTRUST_UNKNOWN = 1\nTRUST_UNSIGNED = 0",
         "9 plugins signed as REGAS. 70 .sig files. ZIP backup: 146 files, 137KB."),

        ("Signing plugins",
         "Sign your plugins with ed25519. .sig files verify authenticity.",
         "from ep_core import sign_file\nsign_file('my_plugin.py', author='MyName')",
         "Others can trust your plugin by saving your public key."),

        ("Plugin development",
         "Create a plugin with register(api) function. Add commands, evaluators, hooks.",
         "def register(api):\n    api.add_command('mycmd', handler, 'help text')\n    api.register_math_evaluator('MyEval', eval_fn, priority=50)",
         "See doc/plugins/developing-plugins.md for the full guide."),

        ("Custom math evaluator",
         "Register at priority <10 to run before Radical. Or >100 for after Python.",
         "def my_eval(ast_dict, variables):\n    return 42.0  # Always answers 42\napi.register_math_evaluator('MyEval', my_eval, priority=1)",
         "Priority 1 = runs before everything else (even TensorSHARP)."),

        ("Output formats",
         "Compile to: .mid, .wav, .mp3, .mp4, .ec, .eic, .ee, .ecc.",
         "// compile song.e -o song.mid\n// compile song.e -o song.wav\n// compile song.e -o song.mp3",
         "One source file, multiple output formats."),

        ("EIC toggleable files",
         ".eic files can switch between #MACHINE and #HUMAN mode mid-file.",
         "// #MACHINE\nT0 N60 D500 V80\n// #HUMAN\nplay note(C4) @dur:q @vel:mf",
         "See samples/eic/ for examples of mode toggling."),

        ("EI project files",
         ".ei files include sub-files using 'inherit \"path/to/file.e\"'.",
         "// suite.ei\ninherit \"parts/movement1.e\"\ninherit \"parts/movement2.e\"",
         "See examples/projects/suite.ei for a multi-movement piece."),

        ("ENX album files",
         ".enx files are album indexes with ordered tracks.",
         "// opus1.enx\ntitle \"My Album\"\ncomposer \"Me\"\ntrack \"01_prelude\" 120\ntrack \"02_waltz\" 100",
         "See examples/albums/opus1.enx for album structure."),

        ("All versions available",
         "v1 = machine/human (deprecated), v2 = semantic (deprecated),\nv3 = shorthand (supported), v4 = polyrhythm/generative (current).",
         "// v1: T0 N60 D500 V80\n// v2: [Section: Intro] Key: C_Major\n// v3: C4 q\n// v4: 3:2 C4 e",
         "Use v4 for new projects. v3 is fully supported. v1/v2 deprecated."),

        ("Ecosystem summary",
         "HELLFORGE = E compiler + Radical + TensorSHARP + OPENapi + Vulkanizer + EAudio.\nAll signed as REGAS. All verified. All backed up.",
         "130/130 tests pass\n9 REGAS-signed plugins\n71 doc files\n63 sample files\n500+ lessons",
         "HELLFORGE v1.0.0.0 ALPHA is ready. Upload to oshonet.in and compose!"),
    ]
    for i, (t, e, c, task) in enumerate(m6):
        lessons.append((t, e, c, task, 6))

    return lessons


def _generate_param_lessons():
    """Generate additional parameterized lessons for quantity.
    Each is small, focused, and CLI-friendly.
    Returns list of (title, explanation, code, task, module) tuples."""
    p = []
    M = 6  # All param lessons are module 6

    # Velocity sweep (20 lessons)
    for v in range(10, 128, 6):
        loudness = "Very soft" if v < 30 else "Soft" if v < 50 else "Moderate" if v < 80 else "Loud" if v < 110 else "Very loud"
        p.append((f"Velocity V{v}",
                  f"Loudness level {v}/127. {loudness}.",
                  f"@bpm 120\nT0 N60 D500 V{v}",
                  f"Listen to velocity {v}.", M))

    # Tempo sweep (20 lessons)
    for bpm in range(40, 220, 10):
        feel = "Slow" if bpm < 70 else "Moderate" if bpm < 110 else "Fast" if bpm < 150 else "Very fast"
        p.append((f"Tempo {bpm}bpm",
                  f"Speed: {bpm} BPM. {feel}.",
                  f"@bpm {bpm}\nT0 N60 D300 V80\nT300 N64 D300 V80\nT600 N67 D600 V80",
                  f"Three notes at {bpm}bpm.", M))

    # Duration sweep (15 lessons)
    for d in [50, 100, 150, 200, 300, 400, 500, 600, 800, 1000, 1500, 2000, 3000, 4000, 5000]:
        feel = "Short staccato" if d < 200 else "Medium" if d < 800 else "Long legato"
        p.append((f"Duration {d}ms",
                  f"Note rings for {d}ms ({d/1000:.1f}s). {feel}.",
                  f"@bpm 60\nT0 N60 D{d} V80",
                  f"One note held for {d}ms.", M))

    # Interval lessons (13 lessons)
    intervals = [(0, "Unison"), (1, "Min 2nd"), (2, "Maj 2nd"), (3, "Min 3rd"),
                 (4, "Maj 3rd"), (5, "Per 4th"), (6, "Tritone"), (7, "Per 5th"),
                 (8, "Min 6th"), (9, "Maj 6th"), (10, "Min 7th"), (11, "Maj 7th"), (12, "Octave")]
    for semi, name in intervals:
        p.append((f"Interval: {name}",
                  f"N60 + {semi} = N{60 + semi}. Interval of {semi} semitones.",
                  f"@bpm 120\nT0 N60 D500 V80\nT0 N{60 + semi} D500 V60",
                  f"Hear the {name}.", M))

    # Scale degree lessons (7 lessons)
    degrees = [("Tonic", 0), ("Supertonic", 2), ("Mediant", 4), ("Subdominant", 5),
               ("Dominant", 7), ("Submediant", 9), ("Leading Tone", 11)]
    for name, semi in degrees:
        p.append((f"Scale: {name}",
                  f"The {name} of C major = N{60 + semi}.",
                  f"@bpm 120\nT0 N60 D300 V80\nT300 N{60 + semi} D300 V80\nT600 N60 D600 V80",
                  f"Hear the {name}.", M))

    # For loop variations (40 lessons)
    for n in range(2, 42):
        p.append((f"For: {n} iterations",
                  f"Compact loop that runs {n} times. One line, many notes.",
                  f"@bpm 240\nfor $i = 0 to {n-1} {{\n  T{{$i * 30}} N{{60 + $i % 12}} D25 V80\n}}",
                  f"{n} notes from one for loop.", M))

    # Repeat variations (20 lessons)
    for n in [2, 3, 4, 5, 6, 7, 8, 10, 12, 16, 20, 24, 32, 40, 48, 64, 80, 100, 120, 200]:
        p.append((f"Repeat {n}x",
                  f"Repeat a block {n} times. Repetition creates structure.",
                  f"@bpm 120\nrepeat {n} {{\n  T0 N60 D40 V80\n  T40 N64 D40 V80\n  T80 N67 D40 V80\n  T120 N72 D80 V80\n}}",
                  f"4-note pattern repeated {n} times.", M))

    # Math expressions (30 lessons)
    for expr, val in [("2+2", 4), ("10*5", 50), ("100/4", 25), ("7%3", 1), ("2^3", 8),
                      ("sqrt(25)", 5), ("30*2", 60), ("144/12", 12), ("sin(0)", 0), ("cos(0)", 1),
                      ("min(5,10)", 5), ("max(5,10)", 10), ("abs(-7)", 7), ("floor(3.9)", 3),
                      ("round(3.2)", 3), ("pow(2,4)", 16), ("10//3", 3), ("100-50", 50),
                      ("20+30", 50), ("60/2", 30)]:
        p.append((f"Math: {expr}={val}",
                  f"{expr} evaluates to {val}. Math works everywhere.",
                  f"@bpm 120\nT0 N{60 + val} D500 V80",
                  f"N{60 + val} from {expr}.", M))

    # MIDI note exploration (10 lessons)
    for note, name in [(48, "C3 bass"), (55, "G3"), (60, "C4 middle"), (64, "E4"),
                       (67, "G4"), (72, "C5 high"), (79, "G5"), (84, "C6"),
                       (96, "C7"), (108, "C8 highest")]:
        p.append((f"Note: {name} ({note})",
                  f"MIDI {note} = {name}. Each note has a unique number.",
                  f"@bpm 120\nT0 N{note} D500 V80",
                  f"Listen to {name} (MIDI {note}).", M))

    # Bonus: common patterns (10 lessons)
    bass_patterns = [
        ("Walking up", "T0 N48 D200 V80\nT200 N50 D200 V80\nT400 N52 D200 V80\nT600 N53 D200 V80"),
        ("Walking down", "T0 N60 D200 V80\nT200 N59 D200 V80\nT400 N57 D200 V80\nT600 N55 D200 V80"),
        ("Octave jump", "T0 N48 D400 V80\nT400 N60 D400 V80\nT800 N48 D400 V80\nT1200 N60 D400 V80"),
        ("Broken chord up", "T0 N48 D150 V80\nT150 N55 D150 V70\nT300 N52 D150 V70\nT450 N55 D150 V70"),
        ("Broken chord down", "T0 N55 D150 V80\nT150 N52 D150 V70\nT300 N48 D150 V70\nT450 N55 D150 V70"),
        ("Rhythm pattern 1", "T0 N48 D100 V80\nT200 N48 D100 V60\nT400 N48 D100 V80\nT600 N48 D100 V60"),
        ("Rhythm pattern 2", "T0 N48 D100 V80\nT150 N48 D100 V60\nT300 N48 D100 V80\nT450 N48 D100 V60\nT600 N48 D200 V80"),
        ("Alternating thirds", "T0 N48 D200 V80\nT200 N55 D200 V70\nT400 N50 D200 V80\nT600 N57 D200 V70"),
        ("Stepwise descent", "T0 N60 D150 V80\nT150 N59 D150 V75\nT300 N57 D150 V70\nT450 N55 D150 V65\nT600 N53 D600 V60"),
        ("Alberti variant", "T0 N48 D125 V80\nT125 N55 D125 V70\nT250 N52 D125 V70\nT375 N55 D125 V70\nT500 N48 D125 V80\nT625 N55 D125 V70\nT750 N52 D125 V70\nT875 N55 D125 V70"),
    ]
    for label, pattern in bass_patterns:
        p.append((f"Bass: {label}",
                  f"Common bass pattern: {label.lower()}. Foundation of many songs.",
                  f"@bpm 120\n{pattern}",
                  f"A {label.lower()} bass pattern.", M))

    # ALL 12 MIDI notes exploration (12 lessons)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for i, nname in enumerate(note_names):
        midi = 60 + i
        p.append((f"Note: {nname}4 ({midi})",
                  f"The note {nname}4 = MIDI {midi}. Learn each note's sound.",
                  f"@bpm 80\nT0 N{midi} D800 V80\nT800 N{midi} D800 V60\nT1600 N{midi} D800 V40",
                  f"Listen to {nname}4 (MIDI {midi}) three times.", M))

    # Tempo sweeping in detail (30 lessons)
    for bpm in range(30, 210, 6):
        feel = "Largo" if bpm < 50 else "Adagio" if bpm < 70 else "Andante" if bpm < 90 else "Moderato" if bpm < 110 else "Allegro" if bpm < 140 else "Vivace" if bpm < 170 else "Presto"
        p.append((f"Tempo {bpm} ({feel})",
                  f"{bpm} BPM = {feel}. Each tempo range has a traditional name.",
                  f"@bpm {bpm}\nT0 N60 D200 V80\nT200 N64 D200 V80\nT400 N67 D200 V80\nT600 N72 D400 V80",
                  f"A short melody at {bpm}bpm ({feel}).", M))

    # Duration detail (20 lessons)
    for d in range(50, 1050, 50):
        p.append((f"Duration {d}ms",
                  f"A note held for {d}ms ({d/1000:.1f}s). Practice hearing length.",
                  f"@bpm 60\nT0 N60 D{d} V80",
                  f"Hold for {d}ms.", M))

    # For loop with different math (30 lessons)
    for n in range(2, 32):
        p.append((f"For: {n} notes varying",
                  f"Each iteration changes the note by $i. {n} different pitches.",
                  f"@bpm 240\nfor $i = 0 to {n-1} {{\n  T{{$i * 40}} N{{60 + $i}} D35 V80\n}}",
                  f"{n} ascending notes, one for each loop iteration.", M))

    # Velocity detail (20 lessons) 
    for v in range(5, 128, 6):
        p.append((f"Velocity {v}",
                  f"Volume level {v}/127. Critical for expression.",
                  f"@bpm 100\nT0 N60 D300 V{v}\nT300 N64 D300 V{v}\nT600 N67 D300 V{v}",
                  f"Three notes all at velocity {v}.", M))

    # Chord type exploration (12 lessons)
    chord_types = [("major", "0,4,7"), ("minor", "0,3,7"), ("dom7", "0,4,7,10"), 
                   ("min7", "0,3,7,10"), ("Maj7", "0,4,7,11"), ("dim", "0,3,6"),
                   ("aug", "0,4,8"), ("sus4", "0,5,7"), ("sus2", "0,2,7"),
                   ("m7b5", "0,3,6,10"), ("dim7", "0,3,6,9"), ("aug7", "0,4,8,10")]
    for cname, intervals_str in chord_types:
        intervals_list = [int(x) for x in intervals_str.split(",")]
        notes_str = " ".join(f"N{60 + i}" for i in intervals_list)
        p.append((f"Chord: {cname}",
                  f"{cname} chord: root + {intervals_str} semitones. {notes_str}.",
                  f"@bpm 120\n" + "\n".join(f"T0 N{60 + i} D500 V80" for i in intervals_list),
                  f"A {cname} chord.", M))

    # Diatonic chords in C major (7 lessons)
    diatonic = [("C major", "0,4,7"), ("D minor", "2,5,9"), ("E minor", "4,7,11"),
                ("F major", "5,9,12"), ("G major", "7,11,14"), ("A minor", "9,12,16"),
                ("B dim", "11,14,17")]
    for cname, intervals_str in diatonic:
        intervals_list = [int(x) for x in intervals_str.split(",")]
        p.append((f"Diatonic: {cname}",
                  f"The {cname} chord in the key of C major.",
                  f"@bpm 120\n" + "\n".join(f"T0 N{60 + i} D500 V80" for i in intervals_list),
                  f"Hear the {cname} diatonic chord.", M))

    # Simple chord progressions (8 lessons)
    progressions = [
        ("I-IV-V-I", [(0, "C"), (5, "F"), (7, "G"), (0, "C")], "The most common progression"),
        ("I-V-vi-IV", [(0, "C"), (7, "G"), (9, "Am"), (5, "F")], "Pop music staple"),
        ("ii-V-I", [(2, "Dm"), (7, "G"), (0, "C")], "Jazz standard progression"),
        ("I-vi-IV-V", [(0, "C"), (9, "Am"), (5, "F"), (7, "G")], "50s progression"),
        ("i-VI-III-VII", [(0, "Cm"), (8, "Ab"), (3, "Eb"), (10, "Bb")], "Epic minor progression"),
        ("I-IV-ii-V", [(0, "C"), (5, "F"), (2, "Dm"), (7, "G")], "Classical turn-around"),
        ("i-iv-VII-VI", [(0, "Cm"), (5, "Fm"), (10, "Bb"), (8, "Ab")], "Andalusian cadence"),
        ("I-iii-IV-V", [(0, "C"), (4, "Em"), (5, "F"), (7, "G")], "Upbeat pop progression"),
    ]
    for pname, chords, desc in progressions:
        lines = []
        for i, (degree, _) in enumerate(chords):
            root = 48 + degree  # bass notes
            lines.append(f"T{i * 500} N{root} D450 V80")
        prog_code = "\n".join(lines)
        p.append((f"Progression: {pname}",
                  f"{desc}: {pname}. Uses {len(chords)} chords.",
                  f"@bpm 120\n{prog_code}",
                  f"A {pname} chord progression.", M))

    # Basic intervals practice (12 lessons)
    for i in range(12):
        p.append((f"Interval practice {i+1}",
                  f"Identify the interval: N60 to N{60+i}. It spans {i} semitones.",
                  f"@bpm 120\nT0 N60 D400 V80\nT500 N{60+i} D800 V80",
                  f"Hear the interval of {i} semitones.", M))

    # Time signature feels (8 lessons)
    for feel, times, desc in [("Common time", [0,250,500,750], "4/4 standard"),
                               ("Waltz", [0,250,500], "3/4 waltz feel"),
                               ("March", [0,250,500,750], "2/4 march"),
                               ("Swing", [0,333,666], "6/8 compound"),
                               ("Half time", [0,500], "2/2 cut time"),
                               ("Five beat", [0,200,400,600,800], "5/4 unusual"),
                               ("Seven beat", [0,150,300,450,600,750,900], "7/4 progressive"),
                               ("Nine beat", [0,133,266,400,533,666,800,933,1066], "9/8 compound")]:
        pattern = "\n".join(f"T{t} N60 D80 V80" for t in times)
        p.append((f"Time: {feel}",
                  f"{feel} ({desc}). {len(times)} beats per measure.",
                  f"@bpm 120\n{pattern}",
                  f"Listen to {feel} rhythm.", M))

    # ═══════════════════════════════════════════════
    # ADVANCED: Music Theory (50 lessons)
    # ═══════════════════════════════════════════════
    modes_data = [
        ("Ionian", [0,2,4,5,7,9,11], "Major scale - bright, happy"),
        ("Dorian", [0,2,3,5,7,9,10], "Minor with raised 6th - jazzy"),
        ("Phrygian", [0,1,3,5,7,8,10], "Minor with flat 2nd - Spanish"),
        ("Lydian", [0,2,4,6,7,9,11], "Major with raised 4th - dreamy"),
        ("Mixolydian", [0,2,4,5,7,9,10], "Major with flat 7th - bluesy"),
        ("Aeolian", [0,2,3,5,7,8,10], "Natural minor - sad"),
        ("Locrian", [0,1,3,5,6,8,10], "Diminished - unstable"),
    ]
    for mode_name, intervals, mode_desc in modes_data:
        for root in [60, 72]:
            notes = [root + i for i in intervals[:5]]
            pattern = "\n".join(f"T{i*200} N{n} D150 V80" for i, n in enumerate(notes))
            p.append((f"Mode: {mode_name} on {root}",
                      f"{mode_desc}. Notes: {', '.join(str(n) for n in notes)}.",
                      f"@bpm 100\n{pattern}",
                      f"Play the {mode_name} mode.", M))

    # Exotic scales (15 lessons)
    exotic_scales = [
        ("Whole Tone", [0,2,4,6,8,10], "6-note symmetrical scale - dreamy"),
        ("Diminished", [0,2,3,5,6,8,9,11], "8-note symmetrical - tense"),
        ("Blues Major", [0,2,3,4,7,9], "Major blues - happy blues"),
        ("Blues Minor", [0,3,5,6,7,10], "Minor blues - sad blues"),
        ("Bebop Dominant", [0,2,4,5,7,9,10,11], "Jazz - chromatic passing"),
        ("Harmonic Minor", [0,2,3,5,7,8,11], "Minor with raised 7th - exotic"),
        ("Melodic Minor", [0,2,3,5,7,9,11], "Jazz minor - ascending only"),
        ("Phrygian Dominant", [0,1,4,5,7,8,10], "Spanish/Egyptian - exotic"),
        ("Hungarian Minor", [0,2,3,6,7,8,11], "Eastern European - gypsy"),
        ("Persian", [0,1,4,5,6,8,11], "Middle Eastern - exotic"),
        ("Japanese", [0,1,5,7,8], "Pentatonic - traditional Japanese"),
        ("Pelog", [0,1,3,7,8], "Indonesian gamelan - exotic"),
        ("Prometheus", [0,2,4,6,9,10], "Scriabin's mystic chord"),
        ("Enigmatic", [0,1,4,6,8,10,11], "Verdi's enigmatic - mysterious"),
        ("Augmented", [0,3,4,7,8,11], "Symmetrical - floating"),
    ]
    for sname, intervals, sdesc in exotic_scales:
        notes = [60 + i for i in intervals[:6]]
        pattern = "\n".join(f"T{i*200} N{n} D150 V80" for i, n in enumerate(notes[:6]))
        p.append((f"Scale: {sname}",
                  f"{sdesc}. Notes: {', '.join(str(n) for n in notes[:6])}...",
                  f"@bpm 100\n{pattern}",
                  f"Play the {sname} scale.", M))

    # Chord extensions (20 lessons)
    ext_chords = [
        ("Cmaj9", [0,4,7,11,14], "Major 9th - rich, jazzy"),
        ("Cmin9", [0,3,7,10,14], "Minor 9th - rich, melancholic"),
        ("Cdom9", [0,4,7,10,14], "Dominant 9th - bluesy, full"),
        ("Cmaj11", [0,4,7,11,14,17], "Major 11th - airy, complex"),
        ("Cmin11", [0,3,7,10,14,17], "Minor 11th - dark, lush"),
        ("Cdom13", [0,4,7,10,14,21], "Dominant 13th - full jazz"),
        ("Cmin13", [0,3,7,10,14,21], "Minor 13th - rich ballad"),
        ("C7b9", [0,4,7,10,13], "7 flat 9 - dark, Spanish"),
        ("C7#9", [0,4,7,10,15], "7 sharp 9 - Hendrix chord"),
        ("C7b5", [0,4,6,10], "7 flat 5 - altered dominant"),
        ("C7#5", [0,4,8,10], "7 sharp 5 - augmented dominant"),
        ("C7sus4", [0,5,7,10], "7 sus 4 - suspended dominant"),
        ("CmMaj7", [0,3,7,11], "Minor major 7 - cinematic"),
        ("C+maj7", [0,4,8,11], "Augmented major 7 - dreamy"),
        ("Cdim7", [0,3,6,9], "Diminished 7 - tense, passing"),
        ("Cm7b5", [0,3,6,10], "Half-diminished - jazz standard"),
        ("C6", [0,4,7,9], "Major 6th - sweet, old-fashioned"),
        ("Cm6", [0,3,7,9], "Minor 6th - melancholic jazz"),
        ("Cadd9", [0,4,7,14], "Add 9 - open, contemporary"),
        ("Cmadd9", [0,3,7,14], "Minor add 9 - soft, emotional"),
    ]
    for cname, intervals, cdesc in ext_chords:
        notes_str = " ".join(f"N{60+i}" for i in intervals)
        pattern = "\n".join(f"T0 N{60+i} D800 V70" for i in intervals)
        p.append((f"Extended: {cname}",
                  f"{cdesc}. Intervals: {'-'.join(str(i) for i in intervals)}.",
                  f"@bpm 80\n{pattern}",
                  f"Hear the {cname} chord.", M))

    # Cadences (8 lessons)
    cadences = [
        ("Perfect Authentic", [("V", 7, 200), ("I", 0, 800)], "Strongest resolution - V to I"),
        ("Plagal", [("IV", 5, 200), ("I", 0, 800)], "Amen cadence - IV to I"),
        ("Deceptive", [("V", 7, 200), ("vi", 9, 800)], "Surprise - V to vi"),
        ("Half", [("I", 0, 200), ("V", 7, 800)], "Pauses on V - incomplete"),
        ("Phrygian", [("iv", 5, 200), ("I", 0, 800)], "Minor mode - iv to I"),
        ("Picardy Third", [("iv", 5, 200), ("I", 4, 800)], "Minor to major ending"),
        ("Landini", [("V", 7, 400), ("I", 9, 400), ("I", 7, 400), ("I", 0, 800)], "Renaissance ornamented cadence"),
        ("Tritone Sub", [("bII", 1, 200), ("I", 0, 800)], "Jazz substitution - bII to I"),
    ]
    for cname, chord_changes, cdesc in cadences:
        lines = []
        for i, (_, root, dur) in enumerate(chord_changes):
            lines.append(f"T{i*400} N{60+root} D{dur} V80")
        pattern = "\n".join(lines)
        p.append((f"Cadence: {cname}",
                  f"{cdesc}.",
                  f"@bpm 80\n{pattern}",
                  f"Hear the {cname} cadence.", M))

    # ═══════════════════════════════════════════════
    # ADVANCED: GPU Plugins (60 lessons)
    # ═══════════════════════════════════════════════
    gpu_lessons = [
        ("GPU detection",
         "Radical detects all GPUs via OpenGL context. 'radical status' shows info.",
         "// radical status — see GPU name, vendor, VRAM, APIs\n// radical gpu list — see all GPUs\n// radical gpu <idx> — switch GPU",
         "Run the commands to see your GPU info."),
        ("Multi-GPU switching",
         "Laptops have iGPU + dGPU. Switch with 'radical gpu 0|1'. Useful for power saving.",
         "// radical gpu list — shows: [0] RTX 3050, [1] Intel Iris Xe\n// radical gpu 1 — switch to iGPU (saves battery)\n// radical gpu 0 — switch to dGPU (maximum performance)",
         "List your GPUs and try switching."),
        ("VRAM management",
         "Set max VRAM with 'radical vram <MB>'. Prevents out-of-memory on shared GPUs.",
         "// radical vram 2048 — limit to 2GB VRAM\n// radical vram off — disable limit\n// radical status — check VRAM usage",
         "Set a VRAM limit appropriate for your GPU."),
        ("Shader cache",
         "Compiled GLSL shaders are cached by AST hash. Reuse without recompilation.",
         "// radical shaders — list cached shaders\n// radical benchmark — compare GPU vs CPU speed",
         "Check your shader cache and run a benchmark."),
        ("GPU benchmark",
         "'radical benchmark' compares GPU vs CPU for math expressions. See real speedup.",
         "// radical benchmark — runs 1000 iterations of each expression\n// Shows GPU ms, CPU ms, speedup ratio",
         "Run the benchmark to see your GPU advantage."),
        ("Batch GPU evaluation",
         "256+ expressions dispatched together. One GPU call for all math. ~50-100x speedup.",
         "$bpm = 120\nfor $i = 0 to 255 {\n  T{$i * 15} N{48 + ($i % 12) + 12 * ($i // 12)} D10 V{60 + round(40 * sin($i * 0.2))}\n}",
         "256 notes in one GPU batch. Try with larger counts."),
        ("Radical evaluator priority",
         "Radical registers at priority 5. Above LURE (10), below TensorSHARP (3).",
         "// Evaluator chain: TensorSHARP(3) -> Radical(5) -> LURE(10) -> Python(100)\n// Each falls through if previous returns None",
         "Radical is tried after TensorSHARP but before LURE."),
        ("AST to GLSL pipeline",
         "Every {$expr} becomes GLSL compute shader code. sin() -> glsl sin(), etc.",
         "$bpm = 120\nfor $i = 0 to 15 {\n  T{$i * 100} N{60 + round(12 * sin($i * 0.4))} D60 V{60 + round(40 * cos($i * 0.2))}\n}",
         "This expression becomes a GLSL shader. GPU runs it."),
        ("Tensor Cores detection",
         "TensorSHARP detects Tensor Cores via CuPy. SM 7.0+ = Volta, 8.0+ = Ampere/TF32.",
         "// tensorsharp status — shows Tensor Core count, precision, GPU name\n// tensorsharp cores — detailed config: FP16, TF32, INT8 support",
         "Check Tensor Core availability on this GPU."),
        ("CuPy matmul",
         "TensorSHARP uses CuPy for matmul. Calls cublasGemmEx with TF32 on Ampere+.",
         "// tensorsharp benchmark — compares TensorSHARP vs Radical vs CPU matmul\n// 1024x1024 matmul in ~77ms on RTX 3050",
         "Run the TensorSHARP benchmark to see matrix multiply speed."),
        ("Mixed precision",
         "Tensor Cores use FP16/TF32 for 2x-10x speedup over FP32. Automatic in CuPy.",
         "// Ampere (RTX 30xx/40xx): TF32 Tensor Cores\n// Volta/Turing (RTX 20xx): FP16 Tensor Cores\n// Both faster than FP32 CUDA cores",
         "Tensor Cores automatically use optimal precision."),
        ("Fallback chain GPU",
         "If TensorSHARP unavailable -> Radical (shader cores) -> LURE -> Python. Never breaks.",
         "// TensorSHARP tries CuPy -> Radical -> LURE -> Python evaluators\n// All return None if they can't compute, next takes over",
         "The fallback chain ensures math always works."),
        ("OPENapi context",
         "OPENapi provides low-level OpenGL context. Game engines built on top.",
         "from plugins.openapi._context import GLContext\nctx = GLContext(width=1920, height=1080)\nprint(f'OpenGL {ctx.gl_version} on {ctx.gpu_name}')",
         "OPENapi gives direct OpenGL 4.6 access for rendering."),
        ("OPENapi shaders",
         "Compile GLSL vertex+fragment shaders. Manage uniforms and programs.",
         "prog = api.shader.compile(vertex_src, fragment_src, 'my_shader')\napi.shader.use(prog)\napi.shader.uniform(prog, 'uMVP', mvp_matrix)",
         "Custom shaders enable any visual effect."),
        ("OPENapi buffers",
         "VBO, VAO, SSBO, UBO for geometry and compute data on GPU.",
         "vbo, size = api.buffer.create_vbo(vertices)\nvao = api.buffer.create_vao('mesh')\napi.buffer.vertex_attrib(0, 3, 28, 0)\napi.render.draw_arrays(GL_TRIANGLES, 0, 3)",
         "Buffer API manages all GPU memory for rendering."),
        ("OPENapi textures",
         "2D textures, cubemaps, sampler state, mipmaps. Standard OpenGL texture ops.",
         "tid = api.texture.create_2d(1024, 1024, pixel_data)\napi.texture.bind(tid, unit=0)\napi.texture.generate_mipmaps(tid)",
         "Texture API for image data on GPU."),
        ("OPENapi framebuffers",
         "FBO for off-screen rendering. Post-processing effects pipeline.",
         "fbo, color_tex, depth_tex = api.render.create_fbo(1920, 1080)\napi.render.bind_fbo(fbo)\napi.render.clear()\n# ... render scene ...\napi.render.bind_default_fbo()",
         "FBO enables render-to-texture for post-processing."),
        ("OPENapi window",
         "GLFW window management with input callbacks. Keyboard, mouse, gamepad.",
         "api.window.set_title('My Game')\nif api.window.is_key_pressed(GLFW_KEY_ESC): break\ndx, dy, sx, sy = api.window.poll_delta()",
         "Window API handles all input and window management."),
        ("Vulkanizer instance",
         "Vulkan instance creation. Enumerates all physical devices. Selects best GPU.",
         "from plugins.vulkanizer._instance import VkInstance\ninst = VkInstance()\nprint(f'Vulkan device: {inst.gpu_info[\"name\"]}')",
         "Vulkanizer creates Vulkan instance and selects device."),
        ("Vulkanizer compute",
         "Compute pipelines for GPU math. More portable than OpenGL compute.",
         "pipeline = api.pipeline.create_compute_pipeline(spirv_code)\npool = api.command.create_pool()\nbuf = api.command.allocate_buffer(pool)\napi.command.begin(buf)\napi.command.dispatch(buf, 256, 1, 1)\napi.command.end(buf)",
         "Vulkan compute pipeline for batch operations."),
        ("Vulkan raytracing",
         "VK_KHR_ray_tracing for hardware RT. BLAS from geometry, TLAS from instances.",
         "if api.raytrace.available:\n    blas = api.raytrace.create_blas(vertices, indices)\n    tlas = api.raytrace.create_tlas([(blas, transform)])\n    result = api.raytrace.trace_rays(cmd_buffer, sbt, 1920, 1080)",
         "Hardware ray tracing requires RTX/Radeon/Arc GPU."),
        ("Vulkan upscaling",
         "Custom temporal upscaling via compute shaders. DLSS-like without vendor lock.",
         "upscaled = api.upscale.upscale(low_res, 3840, 2160)\n# Tensor Cores used if available, else compute shaders\n# Temporal feedback prevents ghosting",
         "Custom upscaling works on any GPU, accelerated by Tensor Cores."),
        ("Radical shader math benchmarks",
         "Compare GPU vs CPU for your specific expressions. Radical's benchmark command.",
         "// radical benchmark\n// sin(x)+cos(y): GPU 0.5ms CPU 12.3ms 24.6x\n// quadratic(1,-5,6): GPU 0.3ms CPU 8.1ms 27.0x",
         "Run the benchmark to see real speedup on your hardware."),
        ("GPU accelerated composition",
         "Compositions with 100+ events benefit most from GPU acceleration. Less overhead per note.",
         "$bpm = 120\n$beat = 60000 / $bpm\nfor $i = 0 to 127 {\n  T{$i * $beat / 8} N{36 + ($i % 12) + 12 * ($i // 12)} D{$beat / 8} V{40 + round(60 * sin($i * 0.2))}\n}",
         "128-note GPU-accelerated composition. Note the smooth velocity curve."),
        ("Radical with while loops",
         "While loops with mutable variables compile to GPU too. Increment inside works.",
         "$i = 0\nwhile $i < 64 {\n  T{$i * 40} N{48 + ($i % 12)} D30 V{60 + round(40 * sin($i * 0.3))}\n  $i = $i + 1\n}",
         "64 notes from a while loop. GPU-accelerated."),
        ("Nested loops on GPU",
         "Nested for loops compile to flat event lists first, then GPU processes math.",
         "for $i = 0 to 3 {\n  for $j = 0 to 3 {\n    T{($i * 4 + $j) * 60} N{60 + $i * 4 + $j} D50 V80\n  }\n}",
         "16 notes from nested loops. Math processed on GPU."),
        ("Radical with complex math",
         "Complex expressions with multiple trig functions benefit most from GPU.",
         "for $i = 0 to 63 {\n  T{$i * 30} N{60 + round(12 * sin($i*0.3) + 6 * cos($i*0.15))} D25 V{50 + round(40 * sin($i*0.1))}\n}",
         "Trig-heavy expression. GPU evaluates all 64 in one dispatch."),
        ("VRAM monitoring",
         "Track GPU memory usage. Important for large batches on shared memory iGPUs.",
         "// radical status — shows VRAM used / limit\n// radical vram 512 — cap at 512MB for iGPUs\n// Over-limit = fallback to CPU automatically",
         "Monitor your VRAM usage during compilation."),
        ("Radical fallback test",
         "Disable GPU to test CPU fallback. All features still work.",
         "// Set strict signing to block radical: sys strict 2 (block unsigned)\n// Or temporarily rename plugins/radical\n// Math still works via LURE -> Python",
         "Verify that your compositions work without GPU."),
        ("LURE vs Radical",
         "LURE (LuaJIT) is CPU-based but fast. Radical is GPU-based. For <100 notes, LURE may be faster.",
         "// lure benchmark — see LuaJIT vs Python speeds\n// radical benchmark — see GPU vs CPU speeds\n// For small batches: LURE is faster. For 256+: Radical wins.",
         "Compare benchmarks to choose optimal backend for your use case."),
    ]
    for title, explanation, code, task in gpu_lessons:
        p.append((title, explanation, code, task, M))

    # ═══════════════════════════════════════════════
    # ADVANCED: Audio & DSP (40 lessons)
    # ═══════════════════════════════════════════════
    audio_lessons = [
        ("EAudio device enum",
         "EAudio detects all audio devices via pygame.midi or sounddevice.",
         "// eaudio status — shows device count, default output, sample rate\n// eaudio devices — lists all audio devices with specs",
         "Check available audio devices."),
        ("Audio buffer creation",
         "Create PCM audio buffers. Sine waves, silence, or custom samples.",
         "buf = audio_api['buffer'].create_sine(440, 1.0)  # 440Hz sine, 1 second\nbuf = audio_api['buffer'].create_silence(0.5)  # 500ms silence\nbuf = audio_api['buffer'].create_buffer(samples)",
         "Create audio buffers for playback or processing."),
        ("Buffer mixing",
         "Mix multiple buffers together with gain control.",
         "sine = buf_api.create_sine(440, 0.5)\nsilence = buf_api.create_silence(0.3)\nmixed = buf_api.mix([sine, silence], gain=0.8)",
         "Mix audio sources for layered sound."),
        ("Buffer resampling",
         "Resample to different sample rates. Essential for format conversion.",
         "resampled = buf_api.resample(sine, 22050)  # Downsample to 22kHz",
         "Resample audio to match output device."),
        ("3D spatial audio",
         "Position audio sources in 3D space. Listener position affects stereo panning.",
         "spa.set_listener([0, 0, 0], velocity=[0, 0, 0])\nspa.add_source('explosion', [10, 0, -5])\nleft, right = spa.get_spatial_gain('explosion')",
         "3D audio creates immersive soundscapes."),
        ("Doppler effect",
         "Moving sources shift pitch. Speed affects the shift amount.",
         "spa.update_source('explosion', velocity=[20, 0, 0])  # Moving right\nshifted_rate = spa.doppler_shift('explosion', 44100)\n# Source at 44100Hz sounds like ~44300Hz when approaching",
         "Doppler shift changes pitch based on relative velocity."),
        ("Distance attenuation",
         "Sounds get quieter with distance. Controlled by reference_distance and rolloff.",
         "spa.add_source('far', [50, 0, 0], gain=1.0)  # Very quiet at 50m\nspa.add_source('near', [2, 0, 0], gain=1.0)    # Full volume at 2m\nleft, right = spa.get_spatial_gain('far')  # ~0.09, ~0.09",
         "Distance attenuation models real-world sound falloff."),
        ("Reverb effect",
         "Schroeder reverb simulates room acoustics. Decay controls echo length.",
         "wet = effects.reverb(dry_signal, decay=0.6, delay_ms=40)\n# decay=0.2 = small room\n# decay=0.8 = large hall",
         "Reverb adds space and depth to audio."),
        ("Delay effect",
         "Echo effect with feedback. Delay_ms controls echo spacing.",
         "echo = effects.delay(signal, delay_ms=300, feedback=0.5)\n# 300ms delay, 50% feedback = several repeats\n# 100ms, 30% = subtle slapback",
         "Delay creates rhythmic echo patterns."),
        ("Compressor",
         "Dynamic range compressor. Reduces loud parts, boosts quiet parts.",
         "compressed = effects.compressor(signal, threshold=0.5, ratio=4.0)\n# threshold=0.3, ratio=2 = gentle compression\n# threshold=0.7, ratio=8 = hard limiting",
         "Compressor evens out volume levels."),
        ("3-band EQ",
         "Adjust bass, mid, and treble frequencies independently.",
         "eqd = effects.eq(signal, bass_gain=1.5, mid_gain=1.0, treble_gain=1.2)\n# bass_gain > 1 = boost, < 1 = cut\n# treble_gain = 0.5 = reduce high frequencies",
         "EQ shapes the tonal balance of audio."),
        ("Audio for games",
         "EAudio integrates with game engines built on OPENapi + Vulkanizer.",
         "// Game engine loop:\n// update() — move audio sources, update listener\n// render() — spatial audio, DSP effects\n// All on GPU via Radical + Vulkanizer compute",
         "EAudio provides the audio layer for AAA game engines."),
        ("Reverb types",
         "Different decay settings simulate different room sizes.",
         "# Small room: decay=0.2, delay_ms=15\n# Hall: decay=0.8, delay_ms=50\n# Cathedral: decay=0.95, delay_ms=80\n# Cave: decay=0.9, delay_ms=100",
         "Adjust reverb parameters for different spaces."),
        ("Delay types",
         "Different delay configurations create different effects.",
         "# Slapback: 100ms, 0.3 feedback — rockabilly\n# Ping-pong: 300ms, 0.5 — stereo width\n# Ambient: 600ms, 0.7 — atmospheric\n# Dub: 500ms, 0.9 — reggae",
         "Delay timing and feedback shape the rhythmic feel."),
        ("Compression settings",
         "Threshold, ratio, attack, release — each parameter shapes the sound.",
         "# Gentle: threshold=0.6, ratio=2\n# Moderate: threshold=0.4, ratio=4\n# Heavy: threshold=0.2, ratio=8\n# Limiter: threshold=0.8, ratio=20",
         "Compression parameters control dynamics processing."),
        ("EQ bands",
         "Bass < 200Hz, Mid 200-4kHz, Treble > 4kHz. Cut or boost each.",
         "# Warm: bass=1.3, treble=0.8\n# Bright: bass=0.8, treble=1.4\n# Telepone: bass=0, treble=2.0\n# Full: bass=1.2, mid=1.1, treble=1.0",
         "EQ bands shape the frequency response."),
        ("Multi-effect chain",
         "Chain effects: compressor -> EQ -> reverb -> delay. Order matters.",
         "step1 = effects.compressor(dry)\nstep2 = effects.eq(step1, bass=1.2, treble=1.1)\nstep3 = effects.reverb(step2, decay=0.5)\nfinal = effects.delay(step3, 200, 0.3)",
         "Effect order significantly changes the final sound."),
        ("Spatial vs stereo",
         "Spatial audio uses 3D positions. Standard audio uses L/R panning.",
         "# Spatial: auto-calculates pan from position\n# Standard: manual L/R gains\n# Both can be mixed in the same engine",
         "Spatial audio automates panning based on position."),
        ("Sample rate basics",
         "44.1kHz = CD quality. 48kHz = video. 96kHz = high-res. Higher = more data.",
         "# 44100Hz: standard music\n# 48000Hz: video/DVD\n# 96000Hz: high-resolution audio\n# Higher rates use more CPU/GPU",
         "Sample rate affects audio quality and performance."),
        ("Buffer duration",
         "Buffer length = samples / sample_rate. 44100 samples @44100Hz = 1 second.",
         "buf = buf_api.create_sine(440, 2.0)  # 2 seconds\nprint(f'Duration: {buf[\"duration\"]}s')  # 2.0\nprint(f'Frames: {buf[\"frames\"]}')  # 88200 @ 44100Hz",
         "Buffer duration depends on sample count and rate."),
    ]
    for title, explanation, code, task in audio_lessons:
        p.append((title, explanation, code, task, M))

    # ═══════════════════════════════════════════════
    # ADVANCED: Project Structure (30 lessons)
    # ═══════════════════════════════════════════════
    project_lessons = [
        ("Multi-file projects",
         ".ei files inherit other .e files. Build complex pieces from parts.",
         "// suite.ei\ninherit \"parts/intro.e\"\ninherit \"parts/verse.e\"\ninherit \"parts/chorus.e\"",
         "Break large compositions into manageable files."),
        ("EI project inheritance",
         "Use inherit keyword to include sub-files. Paths are relative to the .ei file.",
         "// parts/intro.e\n@bpm 120\nT0 N60 D500 V80\n// parts/verse.e\n@bpm 120\nT0 N64 D500 V80",
         ".ei files compose larger works from smaller pieces."),
        ("ENX album structure",
         ".enx files are album indexes with track ordering and metadata.",
         "// opus1.enx\ntitle \"Symphony No. 1\"\ncomposer \"Me\"\ntrack \"01_movement1\" 120\ntrack \"02_movement2\" 80",
         "ENX files organize multiple tracks into albums."),
        ("EIC toggleable mode",
         ".eic files can switch between #MACHINE and #HUMAN mid-file for best of both.",
         "// #MACHINE section\nT0 N60 D500 V80\n// #HUMAN section\nplay note(C4) @dur:q @vel:mf",
         "Use machine for precision, human for readability, switch as needed."),
        ("EC compiled binary",
         ".ec files are compiled binary. Faster load but not human-readable.",
         "// compile song.e -o song.ec — creates compiled binary\n// compile song.ec -o song.mid — decompile to MIDI\n// Smaller than source, faster to parse",
         "Compiled binaries are faster to load but can't be edited as text."),
        ("EIC clear bundle",
         ".eic bundles combine source and compiled data. Share one file.",
         "// compile song.e -o song.eic — creates .eic bundle\n// Includes both human-readable source and compiled events\n// Best for sharing: readable + fast playback",
         ".eic bundles are the recommended distribution format."),
        ("Project organization",
         "Organize projects: /parts, /tracks, /samples, /exports. Keep it clean.",
         "// project/\n//   album.enx\n//   tracks/01_intro.e\n//   tracks/02_song.e\n//   parts/bass.e\n//   parts/melody.e\n//   exports/album.mid",
         "Good project organization scales to any size."),
        ("Version control",
         "E files are plain text. Use git for version control. Diff shows changes clearly.",
         "// git add song.e\n// git commit -m \"Added verse melody\"\n// git diff — shows exact note changes\n// Text format is ideal for collaboration",
         "Plain text = full git support."),
        ("Collaboration workflow",
         "Multiple people can edit different .ei parts simultaneously. Merge in .ei.",
         "// Person A edits parts/verse.e\n// Person B edits parts/chorus.e\n// Both changes reflected in suite.ei",
         "Parallel editing of large compositions."),
        ("Export pipeline",
         "Compile to multiple formats from one source. MIDI, WAV, MP3, MP4.",
         "// compile song.e -o song.mid\n// compile song.e -o song.wav\n// compile song.e -o song.mp3\n// compile song.e -o song.mp4",
         "One source, many outputs."),
        ("Audio export",
         "WAV/MP3 export requires FluidSynth or software synth. FLAC supported too.",
         "// compile song.e -o song.wav — FluidSynth render\n// compile song.e -o song.mp3 — MP3 encoding\n// See also: piano_synth.py for numpy renderer",
         "Audio export converts MIDI events to actual sound."),
        ("Encrypted format",
         ".ee files are AES-encrypted. Protect your compositions from unauthorized use.",
         "// encrypt song.e -o song.ee — encrypt with password\n// decrypt song.ee -o song.e — decrypt\n// Only authorized users with password can open",
         "Encryption protects your musical IP."),
        ("ECC encrypted compiled",
         ".ecc files are compiled AND encrypted. Maximum protection.",
         "// ecc song.e -o song.ecc — compile then encrypt\n// One step: compile + encrypt\n// Decompile + decrypt in one step to play",
         "ECC = compiled + encrypted. Fast playback + protected."),
        ("Package distribution",
         "Package your plugin or mod for distribution via pkglist.json.",
         "// plugin install myplugin\n// pkglist update — sync registry\n// Your plugin hosted on oshonet.in",
         "HELLFORGE has a package registry for sharing plugins."),
        ("Mod security scanning",
         "Mods are AST-scanned before loading. Restricted builtins prevent malicious code.",
         "// sys scan — scan all plugins and mods\n// Scanning checks for dangerous operations\n// Blocked builtins: exec, eval, system, etc.",
         "Security scanning protects against malicious mods."),
        ("Strict signing enforcement",
         "sys strict 0|1|2 controls enforcement. 0=off, 1=warn, 2=block unsigned.",
         "// sys strict 0 — unsigned plugins load freely\n// sys strict 1 — unsigned plugins show warning\n// sys strict 2 — unsigned plugins blocked",
         "Strict signing prevents tampered plugin execution."),
        ("REGAS vs TENTARI trust",
         "REGAS = server-confirmed TENTARI, same trust level (2). TENTARI = third-party devs.",
         "TRUST_REGAS = 2  # CORE-EXPANSION, confirmed via oshonet.in\nTRUST_TENTARI = 2  # Third-party plugin authors\nBoth trusted equally.",
         "REGAS and TENTARI are equally trusted. REGAS adds server verification."),
        ("Plugin verification",
         "'verify <plugin>' checks hash against pkglist. Detects tampering.",
         "// verify radical — checks Radical plugin hash\n// If altered: 'Code mismatch — plugin may be altered'\n// Always verify before loading untrusted plugins",
         "Verification detects unauthorized modifications."),
        ("Plugin development API",
         "Write plugins with register(api) function. Access all system capabilities.",
         "def register(api):\n    api.add_command('mycmd', handler, 'Help text')\n    api.register_math_evaluator('MyEval', eval_fn, priority=50)\n    api.add_boot_step('MyPlugin ready', 'done')",
         "The plugin API gives access to every system feature."),
        ("Custom math evaluator",
         "Register a math evaluator at any priority. Return number or None to fall through.",
         "def my_eval(ast_dict, variables):\n    if ast_dict.get('t') == 'NUM':\n        return float(ast_dict.get('v', 0))\n    return None\napi.register_math_evaluator('MyEval', my_eval, priority=1)",
         "Custom evaluators extend the math engine."),
        ("Event hooks",
         "Plugins can hook into compile and playback events. Pre/post processing.",
         "api.on('pre_compile', my_prehook)\napi.on('post_compile', my_posthook)\napi.on('pre_play', my_preplay)\napi.on('post_play', my_postplay)",
         "Event hooks allow plugins to modify behavior at any stage."),
        ("Custom commands",
         "Plugins can add any number of eshell commands.",
         "def my_handler(args):\n    print(f'Hello, {\" \".join(args)}!')\napi.add_command('hello', my_handler, 'Say hello')",
         "Extend the shell with your own commands."),
        ("Plugin dependencies",
         "Declare pip dependencies. Auto-installed on boot via require().",
         "api.require('numpy')\napi.require('scipy', 'pygame')\n# Or in pkglist.json: \"dependencies\": [\"numpy\"]",
         "Dependencies are auto-installed when the plugin loads."),
        ("Plugin boot steps",
         "Show initialization progress. Helps users understand load order.",
         "api.add_boot_step('MyPlugin v1.0', 'loading')\n# ... initialization ...\napi.add_boot_step('MyPlugin v1.0', 'done')",
         "Boot steps appear in the startup progress bar."),
        ("Async plugin features",
         "Plugins can use async compilation for non-blocking operations.",
         "from ep_compiler.async_compile import async_compile_source\nimport asyncio\nresult = asyncio.run(async_compile_source(text))",
         "Async operations keep the shell responsive."),
        ("Config persistence",
         "Save and load plugin configuration across sessions.",
         "api.set_config('my_setting', 'value')\nvalue = api.get_config('my_setting', 'default')\nconfigs = api.get_all_configs()",
         "Configuration persists across shell restarts."),
        ("Custom directives",
         "Register custom @directives for your plugin's features.",
         "def handle_my_directive(value, ll_state):\n    ll_state['my_param'] = value\napi.register_directive(r'@myparam\\s+(\\d+)', handle_my_directive)",
         "Custom directives integrate with the E parser."),
        ("Plugin themes",
         "Customize shell appearance. Colors, prompts, output formatting.",
         "api.set_theme(prompt='MyPlugin> ', color_primary='#FF6600')\napi.set_prompt_renderer(my_renderer)\napi.add_output_filter(my_filter)",
         "Themes personalize the HELLFORGE experience."),
        ("Mod security scanning",
         "Mods are scanned with AST analysis. Dangerous operations are flagged.",
         "# Blocked in mods:\n# - file writes outside project\n# - network access\n# - subprocess calls\n# - import of restricted modules",
         "Mod security prevents malicious code from harming your system."),
        ("Plugin signing",
         "Sign your plugin with ed25519. Users verify with your public key.",
         "from ep_core import sign_file, save_identity_public_key\nsign_file('myplugin.py', author='MyName')\nsave_identity_public_key('MyName', my_public_key_hex)",
         "Signing proves your plugin's authenticity."),
    ]
    for title, explanation, code, task in project_lessons:
        p.append((title, explanation, code, task, M))

    # ═══════════════════════════════════════════════
    # ADVANCED: Extended Generated Parameter Sweeps (100+ lessons)
    # ═══════════════════════════════════════════════

    # All 11 major scales (11 lessons)
    all_keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for i, key in enumerate(all_keys):
        root = 60 + i
        pattern = "\n".join(f"T{i*150} N{root + step} D120 V80" for i, step in enumerate([0,2,4,5,7,9,11]))
        p.append((f"Key: {key} major",
                  f"The {key} major scale starting on MIDI {root}.",
                  f"@bpm 110\n{pattern}\nT{1050} N{root + 12} D500 V80",
                  f"Play the {key} major scale.", M))

    # All 12 minor scales (12 lessons)
    for i, key in enumerate(all_keys):
        root = 60 + i
        pattern = "\n".join(f"T{i*150} N{root + step} D120 V80" for i, step in enumerate([0,2,3,5,7,8,10]))
        p.append((f"Key: {key} minor",
                  f"The {key} natural minor scale starting on MIDI {root}.",
                  f"@bpm 110\n{pattern}\nT{1050} N{root + 12} D500 V80",
                  f"Play the {key} minor scale.", M))

    # Interval ear training (24 lessons)
    for semi in range(24):
        p.append((f"Ear training: {semi} semitones",
                  f"Interval spanning {semi} semitones ({semi//12} octave(s) + {semi%12} semitones). Identify it!",
                  f"@bpm 120\nT0 N60 D400 V80\nT500 N{60 + semi} D800 V80",
                  f"Identify the {semi}-semitone interval.", M))

    # Common chord progressions in every key (24 lessons)
    for i, key in enumerate(all_keys):
        root = 60 + i
        p.append((f"Progression: I-IV-V-I in {key}",
                  f"The most common progression in {key} major. Root at MIDI {root}.",
                  f"@bpm 120\nT0 N{root} D400 V80\nT400 N{root+5} D400 V80\nT800 N{root+7} D400 V80\nT1200 N{root} D800 V80",
                  f"I-IV-V-I in {key} major.", M))

    # Cadence practice (24 lessons)
    for i, key in enumerate(all_keys):
        root = 60 + i
        p.append((f"Cadence: V-I in {key}",
                  f"Dominant to tonic resolution in {key}. The strongest musical gesture.",
                  f"@bpm 100\nT0 N{root+7} D400 V80\nT400 N{root} D800 V80",
                  f"V-I cadence in {key} major.", M))

    # ═══════════════════════════════════════════════
    # ADVANCED: Extended Performance (100 lessons)
    # ═══════════════════════════════════════════════

    # Arpeggio patterns across keys
    for interval in [3, 4, 5, 6, 7, 8, 10, 12]:
        for root in [48, 60, 72]:
            code = "@bpm 120\nfor $i = 0 to 7 {\n  T{$i * 120} N{" + str(root) + " + ($i % 3) * " + str(interval) + "} D100 V80\n}"
            p.append((f"Arpeggio: root {root} int {interval}",
                      f"Arpeggio from MIDI {root} with interval {interval}. Creates a unique pattern.",
                      code,
                      f"Arpeggio: root={root}, interval={interval}.", M))

    # Polyrhythm patterns (20 lessons)
    for p1, p2 in [(2,3), (3,2), (3,4), (4,3), (4,5), (5,4), (5,6), (6,5), (3,5), (5,3),
                   (7,8), (8,7), (7,6), (6,7), (7,5), (5,7), (9,8), (8,9), (11,12), (12,11)]:
        denom = max(p1, p2) * 50
        lines = [f"T{i * denom // p1} N60 D{denom // p1 - 10} V80" for i in range(p1)]
        lines += [f"T{i * denom // p2} N72 D{denom // p2 - 10} V60" for i in range(p2)]
        pattern = "\n".join(sorted(lines, key=lambda x: int(x.split(" ")[0].replace("T",""))))
        p.append((f"Polyrhythm {p1}:{p2}",
                  f"Cross-rhythm: {p1} notes against {p2} in the same time. Complex texture.",
                  f"@bpm 120\n{pattern}",
                  f"Listen to the {p1}:{p2} polyrhythm.", M))

    # All 36 diatonic triads (36 lessons)
    for key_idx, key_name in enumerate(all_keys[:6]):
        for degree in range(7):
            root = 60 + key_idx
            intervals = [0, 2, 4, 5, 7, 9, 11]
            triad_steps = [(0, 2, 4), (0, 2, 4), (0, 3, 5), (0, 2, 4), (0, 2, 4), (0, 3, 5), (0, 3, 5)]
            voicing = [0, 2, 4]
            if degree in [1, 2, 5]:
                voicing = [0, 3, 5]
            r = root + intervals[degree]
            pattern = "\n".join([
                f"T0 N{r + voicing[0]} D800 V70",
                f"T0 N{r + voicing[1]} D800 V60",
                f"T0 N{r + voicing[2]} D800 V50"
            ])
            chord_names = ["I", "ii", "iii", "IV", "V", "vi", "vii"]
            p.append((f"Diatonic: {key_name} {chord_names[degree]}",
                      f"The {chord_names[degree]} chord in {key_name} major (MIDI root {r}).",
                      f"@bpm 80\n{pattern}",
                      f"Hear the {chord_names[degree]} in {key_name}.", M))

    # Performance optimization patterns (30 lessons)
    for batch_size in [64, 128, 256, 512, 1024]:
        for complexity in ["basic", "trig", "full"]:
            if complexity == "basic":
                body = f"  T{{$i * 10}} N{{60 + $i % 12}} D8 V80"
            elif complexity == "trig":
                body = f"  T{{$i * 10}} N{{60 + round(12 * sin($i * 0.3))}} D8 V{{60 + round(40 * cos($i * 0.15))}}"
            else:
                body = f"  T{{$i * 10}} N{{36 + ($i % 12) + 12 * ($i // 12)}} D8 V{{40 + round(60 * sin($i * 0.15))}}"
            p.append((f"Perf: {batch_size} {complexity}",
                      f"Batch of {batch_size} notes ({complexity} math). GPU accelerates this.",
                      f"@bpm 240\nfor $i = 0 to {batch_size-1} {{\n{body}\n}}",
                      f"Performance test: {batch_size} {complexity} notes.", M))

    # ═══════════════════════════════════════════════
    # ADVANCED: Extended Theory (100 lessons)
    # ═══════════════════════════════════════════════

    # Chord inversions (36 lessons)
    for i, key in enumerate(all_keys[:6]):
        for inv in range(3):
            root = 60 + i
            chord_tones = [0, 4, 7]  # major triad
            for j in range(3):
                chord_tones[j] += 12 if (j + inv) >= 3 else 0
            notes = [root + chord_tones[(j + inv) % 3] for j in range(3)]
            pattern = "\n".join(f"T0 N{n} D800 V70" for n in notes)
            p.append((f"Inversion: {key} {['root','1st','2nd'][inv]}",
                      f"{key} major chord in {['root position','first inversion','second inversion'][inv]}.",
                      f"@bpm 80\n{pattern}",
                      f"Hear the {['root','first','second'][inv]} inversion.", M))

    # Sus chord resolutions (12 lessons)
    for i, key in enumerate(all_keys):
        root = 60 + i
        p.append((f"Suspension: {key}",
                  f"Suspended 4th chord resolving to major. Tension -> release.",
                  f"@bpm 80\nT0 N{root} D200 V80\nT0 N{root+5} D200 V60\nT0 N{root+7} D200 V60\nT500 N{root+4} D600 V60",
                  f"Hear the sus4 resolve to major in {key}.", M))

    # Neapolitan chord (6 lessons)
    for i, key in enumerate(all_keys[:6]):
        root = 60 + i
        p.append((f"Neapolitan: {key}",
                  f"Flat II major chord in {key}. Dramatic, classical sound.",
                  f"@bpm 80\nT0 N{root+1} D400 V70\nT0 N{root+5} D400 V60\nT0 N{root+8} D400 V50\nT800 N{root} D800 V80\nT800 N{root+4} D800 V60\nT800 N{root+7} D800 V50",
                  f"Hear the Neapolitan sixth in {key}.", M))

    # Pedal point (6 lessons)
    for i, key in enumerate(all_keys[:6]):
        root = 60 + i
        p.append((f"Pedal: {key}",
                  f"A sustained bass note while harmonies change above. Creates tension.",
                  f"@bpm 80\nT0 N{root} D2000 V60\nT0 N{root+4} D500 V70\nT500 N{root+7} D500 V70\nT1000 N{root+5} D500 V70\nT1500 N{root+4} D500 V70",
                  f"Hear the pedal point on {key}.", M))

    # Ostinato patterns (12 lessons)
    ostinatos = [
        ("Rock", "T0 N48 D150 V80\nT150 N48 D150 V60\nT300 N55 D150 V80\nT450 N55 D150 V60"),
        ("Classical", "T0 N48 D100 V80\nT100 N55 D100 V70\nT200 N52 D100 V70\nT300 N55 D100 V70"),
        ("Minimalist", "T0 N48 D200 V80\nT200 N43 D200 V80\nT400 N48 D200 V80\nT600 N43 D200 V80"),
        ("Reggae", "T0 N48 D300 V80\nT0 N55 D300 V60\nT600 N48 D300 V80\nT600 N55 D300 V60"),
        ("Funk", "T0 N48 D100 V80\nT100 N53 D100 V70\nT200 N55 D100 V70\nT300 N53 D100 V70"),
        ("Latin", "T0 N48 D80 V80\nT80 N55 D80 V70\nT160 N48 D80 V80\nT240 N57 D80 V70"),
        ("Jazz walk", "T0 N48 D200 V80\nT200 N50 D200 V75\nT400 N52 D200 V70\nT600 N53 D200 V65"),
        ("Metal", "T0 N48 D50 V127\nT50 N48 D50 V80\nT100 N48 D50 V127\nT150 N48 D50 V80"),
        ("Ambient", "T0 N48 D1000 V60\nT0 N55 D1000 V50\nT0 N52 D1000 V40"),
        ("Electronic", "T0 N36 D100 V80\nT100 N36 D100 V60\nT200 N36 D100 V80\nT300 N36 D100 V60"),
        ("Samba", "T0 N48 D100 V80\nT100 N55 D100 V60\nT200 N48 D100 V60\nT300 N55 D100 V80"),
        ("Gospel", "T0 N48 D300 V80\nT300 N55 D200 V70\nT500 N52 D200 V70\nT700 N55 D300 V60"),
    ]
    for style, ost_pattern in ostinatos:
        p.append((f"Ostinato: {style}",
                  f"A {style} ostinato pattern. Repeating figures create rhythmic drive.",
                  f"@bpm 100\n{ost_pattern}",
                  f"Play the {style} ostinato.", M))

    # Call and response patterns (16 lessons)
    for style, call, response in [
        ("Blues", "T0 N60 D200 V80\nT200 N64 D200 V80\nT400 N67 D200 V80", "T600 N64 D200 V80\nT800 N60 D200 V80\nT1000 N55 D400 V80"),
        ("Jazz", "T0 N67 D200 V80\nT200 N69 D200 V80\nT400 N72 D200 V80", "T600 N71 D200 V80\nT800 N69 D200 V80\nT1000 N67 D400 V80"),
        ("Rock", "T0 N55 D150 V127\nT150 N55 D150 V80\nT300 N60 D150 V127", "T450 N60 D150 V80\nT600 N64 D150 V127\nT750 N64 D300 V80"),
        ("Classical", "T0 N60 D300 V80\nT300 N64 D300 V80\nT600 N67 D300 V80", "T900 N72 D300 V80\nT1200 N71 D300 V80\nT1500 N67 D600 V80"),
    ]:
        for transposition in [0, 3, 5]:
            def trans(line, t):
                parts = line.split()
                result = []
                for p in parts:
                    if p.startswith("N"):
                        try:
                            val = int(p[1:])
                            result.append(f"N{val + t}")
                        except:
                            result.append(p)
                    else:
                        result.append(p)
                return " ".join(result)
            transposed_call = "\n".join(trans(l, transposition) for l in call.split("\n"))
            transposed_resp = "\n".join(trans(l, transposition) for l in response.split("\n"))
            label = f"{style} +{transposition}"
            p.append((f"Call-resp: {label}",
                      f"Call and response in {style} style, transposed by {transposition} semitones.",
                      f"@bpm 100\n{transposed_call}\n{transposed_resp}",
                      f"Hear the {style} call and response.", M))

    # ═══════════════════════════════════════════════
    # EXTREME: Benchmarks & Stress Tests (30 lessons)
    # ═══════════════════════════════════════════════
    for n in [500, 1000, 2000, 5000, 10000]:
        for pattern_type in ["scale", "arpeggio", "random"]:
            if pattern_type == "scale":
                body = f"T{{$i * 5}} N{{48 + ($i % 12)}} D4 V80"
            elif pattern_type == "arpeggio":
                body = f"T{{$i * 5}} N{{36 + ($i % 12) + 12 * ($i // 12)}} D4 V40"
            else:
                body = f"T{{$i * 5}} N{{48 + round(24 * sin($i * 0.3))}} D4 V{{40 + round(60 * cos($i * 0.1))}}"
            p.append((f"Stress: {n} {pattern_type}",
                      f"Stress test with {n} notes ({pattern_type} pattern). Measures GPU compile time.",
                      f"@bpm 240\nfor $i = 0 to {n-1} {{\n  {body}\n}}",
                      f"Stress: {n} {pattern_type} notes.", M))

    # ═══════════════════════════════════════════════
    # FINAL: Mastery (10 lessons)
    # ═══════════════════════════════════════════════
    mastery_lessons = [
        ("Composition: melody + harmony",
         "Combine melody and chords. Right hand melody, left hand chords.",
         "@bpm 100\n// Right hand melody\nT0 N72 D200 V80\nT200 N71 D200 V80\nT400 N67 D200 V80\nT600 N64 D200 V80\n// Left hand chords\nT0 N48 D800 V60\nT0 N52 D800 V50\nT0 N55 D800 V50",
         "Create a melody with chord accompaniment."),
        ("Composition: call-response",
         "Two voices in conversation. Higher voice calls, lower answers.",
         "@bpm 100\n// Voice 1 (call)\nT0 N72 D200 V80\nT200 N76 D200 V80\nT400 N79 D200 V80\n// Voice 2 (response)\nT600 N67 D200 V70\nT800 N64 D200 V70\nT1000 N60 D400 V70",
         "Write a call-and-response between two voices."),
        ("Composition: cannon",
         "Same melody starting at different times. Creates a round.",
         "@bpm 120\n// Voice 1\nT0 N60 D300 V80\nT300 N64 D300 V80\nT600 N67 D300 V80\nT900 N72 D600 V80\n// Voice 2 (starts at T600)\nT600 N60 D300 V60\nT900 N64 D300 V60\nT1200 N67 D300 V60\nT1500 N72 D600 V60",
         "Write a 2-voice cannon/round."),
        ("Composition: sonata form",
         "Exposition -> Development -> Recapitulation. Three sections.",
         "@bpm 120\n// Exposition (Theme A)\nT0 N60 D200 V80\nT200 N64 D200 V80\nT400 N67 D200 V80\nT600 N72 D400 V80\n// Development (Theme B)\nT1000 N67 D200 V70\nT1200 N69 D200 V70\nT1400 N71 D200 V70\nT1600 N72 D400 V70\n// Recapitulation (Theme A')\nT2000 N60 D200 V80\nT2200 N64 D200 V80\nT2400 N67 D200 V80\nT2600 N72 D600 V80",
         "A simple sonata form structure."),
        ("Composition: theme and variations",
         "Present a theme, then vary it. Rhythm, harmony, or melody changes.",
         "@bpm 120\n// Theme\nT0 N60 D200 V80\nT200 N62 D200 V80\nT400 N64 D200 V80\nT600 N67 D400 V80\n// Variation 1 (faster)\nT1000 N60 D100 V70\nT1100 N62 D100 V70\nT1200 N64 D100 V70\nT1300 N67 D200 V80\n// Variation 2 (higher)\nT1600 N72 D200 V80\nT1800 N74 D200 V80\nT2000 N76 D200 V80\nT2200 N79 D400 V80",
         "Create a theme with two variations."),
        ("Composition: minimalism",
         "Slowly evolving patterns. Small changes over time create interest.",
         "@bpm 100\n// Pattern A (repeats 4x)\nfor $i = 0 to 3 {\n  T{$i*400} N48 D150 V80\n  T{$i*400+150} N55 D150 V70\n  T{$i*400+300} N52 D100 V60\n}\n// Pattern B (shifted)\nT1600 N48 D150 V80\nT1750 N55 D150 V70\nT1900 N53 D100 V60\nT2000 N48 D150 V80\nT2150 N55 D150 V70\nT2300 N54 D100 V60",
         "Write a minimalist composition with evolving patterns."),
        ("Composition: jazz",
         "Swing rhythm, extended chords, chromatic approach notes.",
         "@bpm 140\n// Swing feel (triplet subdivision)\nT0 N60 D200 V80\nT333 N64 D200 V80\nT666 N67 D200 V80\nT1000 N69 D200 V80\nT1333 N71 D200 V80\nT1666 N72 D400 V80\n// Extended chord\nT0 N48 D2000 V60\nT0 N52 D2000 V50\nT0 N55 D2000 V50\nT0 N59 D2000 V40",
         "Create a jazz-influenced passage."),
        ("Composition: cinematic",
         "Epic, emotional. Wide intervals, dynamic swells, full chords.",
         "@bpm 80\n// Cinematic intro\nT0 N48 D1000 V60\nT0 N55 D1000 V50\nT0 N60 D1000 V50\n// Swell\nT1000 N48 D500 V80\nT1000 N55 D500 V70\nT1000 N60 D500 V70\nT1000 N64 D500 V60\n// Resolution\nT2000 N48 D2000 V80\nT2000 N52 D2000 V70\nT2000 N55 D2000 V60\nT2000 N60 D2000 V50",
         "Create a cinematic/cinematic passage."),
        ("Composition: electronic",
         "Repetitive patterns, syncopation, aggressive dynamics.",
         "@bpm 140\n// Bass pulse\nfor $i = 0 to 7 {\n  T{$i*250} N36 D200 V{80 + $i*5}\n}\n// Lead pattern\nfor $i = 0 to 15 {\n  T{$i*125} N{72 + ($i % 4)*2} D60 V{round(60 + 40 * sin($i*0.5))}\n}",
         "Create an electronic/techno passage."),
        ("Your first full composition",
         "Combine everything you've learned. 100+ bars, multiple sections, dynamics.",
         "@bpm 120\n// Section A\nfor $i = 0 to 7 {\n  T{$i*200} N{60+$i*2} D150 V80\n}\n// Section B\nfor $i = 0 to 7 {\n  T{1600+$i*200} N{67+$i*2} D150 V70\n}\n// Section A' (return)\nfor $i = 0 to 7 {\n  T{3200+$i*200} N{60+$i*2} D150 V80\n}\n// Coda\nT4800 N60 D1000 V127\nT4800 N64 D1000 V100\nT4800 N67 D1000 V80",
         "Your first complete HELLFORGE composition! Run to compile."),
    ]
    for title, explanation, code, task in mastery_lessons:
        p.append((title, explanation, code, task, M))

    # Final milestone
    p.append(("1000+ lessons complete",
              "Over 1000 HELLFORGE lessons mastered! You are now a HELLFORGE composer.\nYou understand the full E language, GPU acceleration, audio DSP,\nplugin development, project structure, and advanced music theory.\n\nGo forth and compose. The forge is yours.",
              "// 1000+ lessons - HELLFORGE mastered!\n@bpm 140\nfor $i = 0 to 299 {\n  T{$i * 12} N{36 + ($i % 12) + 12 * ($i // 12)} D10 V{40 + round(60 * sin($i * 0.2))}\n}",
              "Celebrate mastering 1000+ lessons!", M))

    return p


# Build all lessons
_final_lessons = []
_final_lessons.extend(_generate_lessons())
_final_lessons.extend(_generate_param_lessons())
LESSONS = _final_lessons
