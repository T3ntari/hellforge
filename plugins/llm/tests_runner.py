#!/usr/bin/env python3
"""In-app test runner + auto-fix loop. Discovers/executes the project's
tests/*_test.py harness files (each prints PASS/FAIL per test plus a
"TESTS: N/M passed" summary), parses the results, summarizes them for the
model, and drives a baseline → apply → retest → fix loop until green."""

import json
import os
import re
import subprocess
import sys

SUMMARY_RE = re.compile(r"TESTS:\s*(\d+)\s*/\s*(\d+)\s+passed", re.IGNORECASE)

OUTPUT_CAP = 4000
TRUNCATED_OUTPUT = 600


def discover_test_files(project_dir):
    """List tests/*_test.py relative paths, sorted; skip directories."""
    tdir = os.path.join(project_dir, "tests")
    if not os.path.isdir(tdir):
        return []
    return sorted(
        os.path.join("tests", f)
        for f in os.listdir(tdir)
        if f.endswith("_test.py") and os.path.isfile(os.path.join(tdir, f))
    )


def _as_text(chunk):
    if chunk is None:
        return ""
    if isinstance(chunk, bytes):
        return chunk.decode("utf-8", errors="replace")
    return chunk


def _interpreter(project_dir):
    """Prefer the project venv python — the bridge can run under a bare
    system python (no numpy/mido), which makes every test file crash on
    import with '0/0 passed (exit 1)'."""
    from pathlib import Path
    venv = Path(project_dir) / ".venv" / "bin" / "python"
    if venv.exists():
        return str(venv)
    return sys.executable


def run_test_file(project_dir, rel_path, timeout=180):
    """Run one harness file in project_dir; parse its summary line. Returns
    {file, total, passed, failed, exit_code, output, ok}. Output capped at
    4000 chars (keeps the tail, where the summary lives)."""
    try:
        proc = subprocess.run([_interpreter(project_dir), rel_path], cwd=project_dir,
                              capture_output=True, text=True, timeout=timeout)
        exit_code = proc.returncode
        output = (_as_text(proc.stdout) + _as_text(proc.stderr))[-OUTPUT_CAP:]
    except subprocess.TimeoutExpired as e:
        exit_code = None
        output = (_as_text(e.stdout) + _as_text(e.stderr))[-OUTPUT_CAP:]
    m = SUMMARY_RE.search(output)
    if m:
        total = int(m.group(2))
        passed = int(m.group(1))
        failed = total - passed
    else:
        passed = output.count("PASS")
        failed = output.count("FAIL")
        total = passed + failed
    ok = exit_code == 0 and failed == 0
    return {"file": rel_path, "total": total, "passed": passed, "failed": failed,
            "exit_code": exit_code, "output": output, "ok": ok}


def run_tests(project_dir, files=None, smoke=False, timeout=180):
    """Run all discovered files (or the given subset). smoke=True runs only
    files with 'smoke' in the name, else the 2 smallest files."""
    if files is None:
        files = discover_test_files(project_dir)
    if smoke:
        smoke_hits = [f for f in files if "smoke" in os.path.basename(f).lower()]
        if smoke_hits:
            files = smoke_hits
        else:
            files = sorted(
                files, key=lambda f: os.path.getsize(os.path.join(project_dir, f))
            )[:2]
    return [run_test_file(project_dir, f, timeout=timeout) for f in files]


def summarize(results):
    """Compact summary for the model, with ✓/✗ markers per file and the
    first ~600 chars of the worst failing file's output."""
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)
    lines = [f"TESTS: {len(results)} files, {total_passed} passed / {total_failed} failed"]
    for r in sorted(results, key=lambda r: r["file"]):
        mark = "\u2713" if r["ok"] else "\u2717"
        line = f"{mark} {r['file']} \u2014 {r['passed']}/{r['total']} passed"
        if r["exit_code"] not in (0, None):
            line += f" (exit {r['exit_code']})"
        lines.append(line)
    worst = None
    for r in results:
        if not r["ok"] and (worst is None or r["failed"] > worst["failed"]):
            worst = r
    if worst is not None:
        out = (worst["output"] or "").strip()
        lines.append("")
        lines.append(f"\u2717 {worst['file']} output (truncated):")
        lines.append(out[:TRUNCATED_OUTPUT])
    return "\n".join(lines)


def plan_test_targets(plan):
    """'tests': 'all' → None (run all files); list → that subset;
    absent → None (no tests to run)."""
    tests = (plan or {}).get("tests")
    if tests is None:
        return None
    if tests == "all":
        return None
    return list(tests)


def parse_plan(text):
    """Extract a JSON plan object from a model reply; None when unparseable."""
    if not text:
        return None
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except (ValueError, TypeError):
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except (ValueError, TypeError):
            pass
    return None


def fix_request_messages(results):
    """Messages asking the model for a JSON fix plan given the failures."""
    return [{
        "role": "user",
        "content": (
            "The tests below are failing. Produce a JSON fix plan "
            "(\"tests\": \"all\" | [file, ...], \"files\": [{\"path\", "
            "\"action\", ...}]) that fixes the failures. Reply with ONLY "
            "the JSON object.\n\n" + summarize(results)
        ),
    }]


def auto_fix_loop(project_dir, model_fn, plan, apply_fn, max_rounds=3, timeout=180):
    """Baseline → apply → retest → ask model for a fix plan → retest, until
    green or max_rounds. apply_fn(plan, project_dir) -> (applied, skipped,
    msgs); model_fn(messages) -> text. Returns {rounds, final_results,
    fixes_applied}. If the plan carries no 'tests' key, nothing runs."""
    if not plan or "tests" not in plan:
        return {"rounds": 0, "final_results": [], "fixes_applied": []}
    targets = plan_test_targets(plan)
    results = run_tests(project_dir, files=targets, timeout=timeout)
    fix_plan = plan
    rounds = 0
    fixes_applied = []
    while rounds < max_rounds:
        rounds += 1
        applied, skipped, msgs = apply_fn(fix_plan, project_dir)
        fixes_applied.append(applied)
        results = run_tests(project_dir, files=targets, timeout=timeout)
        if all(r["ok"] for r in results):
            break
        if rounds >= max_rounds:
            break
        fix_plan = parse_plan(model_fn(fix_request_messages(results)))
        if not fix_plan:
            break
    return {"rounds": rounds, "final_results": results, "fixes_applied": fixes_applied}
