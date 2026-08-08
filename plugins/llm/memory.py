"""Long-form memory, global notes, and tickets — agent-managed project files.

Maintains three project-root markdown files (mirrors todo.py):

MEMORY.md — long-form memory, kept SEPARATE from the working prompt; the
  orchestrator injects it as its own bounded context section. Bullets,
  deduped case-insensitively on add. Plan key contract:
    "memory": [{"point": "...", "action": "add"|"remove"}]
  (action defaults to "add"). Read back via load_memory() / render_memory().

NOTES.md — global scratchpad made by the main agent; survives sessions.
  Timestamped append-only: "## <date> <time>" header + text. Plan key:
    "note": {"text": "..."}

TICKETS.md — tickets for OTHER bots (the orchestrator hands these to
  sub-agents). Block format:
    ## TICKET-<n>: <title>
    status: open|in_progress|done
    assignee: <bot name>
    body: <task description>
  Plan key contract:
    "tickets": [{"action": "create", "title", "body", "assignee": ""} |
                {"action": "update", "num", "status"?, "assignee"?, "body"?}]
  create numbers increment (TICKET-1, TICKET-2, ...); update rewrites the
  block in place.

All three files start with their "# X.md" header when missing; files are
never deleted wholesale."""

import os
import re
from datetime import datetime

_BULLET_RE = re.compile(r"^\s*-\s+(.*)$")
_TICKET_RE = re.compile(r"^##\s*TICKET-(\d+)\s*:\s*(.*)$")
_STATUS = ("open", "in_progress", "done")


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _write_text(path, text):
    if text and not text.endswith("\n"):
        text += "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _read_lines(path):
    text = _read_text(path)
    return text.split("\n") if text else []


def _write_lines(path, lines):
    while lines and not lines[-1].strip():
        lines.pop()
    _write_text(path, "\n".join(lines))


def _ensure_header(path, title):
    """Start the file with "# <title>" when missing; create it otherwise."""
    if _read_text(path).lstrip("\ufeff").startswith(f"# {title}"):
        return
    text = f"# {title}\n" + _read_text(path)
    _write_text(path, text)


def _cap(text, cap):
    """Bound text to cap characters, cutting the tail with a marker."""
    if cap and len(text) > cap:
        return text[:cap].rstrip() + "\n...\n"
    return text


# ── MEMORY.md ──


def load_memory(path):
    """Parse MEMORY.md → list of bullet strings (without the "- " prefix).
    Missing file → []."""
    return [m.group(1).strip()
            for ln in _read_lines(path)
            for m in [_BULLET_RE.match(ln)] if m]


def add_memory(path, points):
    """Append "- <point>" bullets, deduped case-insensitively.
    Returns the number of new bullets added."""
    pts = [str(p).strip() for p in (points or []) if str(p).strip()]
    if not pts:
        return 0
    _ensure_header(path, "MEMORY.md")
    lines = _read_lines(path)
    known = {b.lower() for b in load_memory(path)}
    added = 0
    for p in pts:
        if p.lower() in known:
            continue
        lines.append(f"- {p}")
        known.add(p.lower())
        added += 1
    if added:
        _write_lines(path, lines)
    return added


def remove_memory(path, points):
    """Remove bullets matching the given points (case-insensitive).
    Returns the number of bullets removed. The file itself is kept."""
    pts = {str(p).strip().lower() for p in (points or []) if str(p).strip()}
    if not pts:
        return 0
    lines = _read_lines(path)
    out, removed = [], 0
    for ln in lines:
        m = _BULLET_RE.match(ln)
        if m and m.group(1).strip().lower() in pts:
            removed += 1
            continue
        out.append(ln)
    if removed:
        _write_lines(path, out)
    return removed


def render_memory(path, cap=3000):
    """Render MEMORY.md as bounded section text (for context injection).
    Missing file → ""; capped at cap characters, tail cut."""
    points = load_memory(path)
    if not points:
        return "" if not os.path.exists(path) else "# MEMORY.md (no entries)\n"
    text = "\n".join([f"- {p}" for p in points])
    return _cap(f"# MEMORY.md — long-form memory\n{text}\n", cap)


def apply_memory(plan_memory, path):
    """Apply plan "memory" entries to MEMORY.md.
    Returns (added, removed) counts."""
    added = removed = 0
    for e in plan_memory or []:
        if not isinstance(e, dict):
            continue
        point = str(e.get("point", "")).strip()
        if not point:
            continue
        action = str(e.get("action", "add")).lower()
        if action == "remove":
            removed += remove_memory(path, [point])
        else:
            added += add_memory(path, [point])
    return added, removed


# ── NOTES.md ──


def add_note(path, text):
    """Append a timestamped note: "## <date> <time>" header + text.
    Returns True when appended, False for blank text."""
    text = str(text).strip()
    if not text:
        return False
    _ensure_header(path, "NOTES.md")
    body = _read_text(path).rstrip("\n")
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _write_text(path, f"{body}\n\n## {stamp}\n{text}")
    return True


def load_notes(path, cap=4000):
    """Notes text (timestamped append-only log), capped at cap characters.
    Missing file → ""."""
    if not os.path.exists(path):
        return ""
    return _cap(_read_text(path), cap)


def apply_note(plan_note, path):
    """Apply plan "note": {"text": "..."} → True when appended."""
    if not isinstance(plan_note, dict):
        return False
    return add_note(path, str(plan_note.get("text", "")))


# ── TICKETS.md ──


def _parse_tickets(path):
    """Parse TICKETS.md → [{num, title, status, assignee, body}] in order."""
    tickets = []
    cur = None
    for ln in _read_lines(path):
        m = _TICKET_RE.match(ln)
        if m:
            cur = {"num": int(m.group(1)), "title": m.group(2).strip(),
                   "status": "open", "assignee": "", "body": ""}
            tickets.append(cur)
            continue
        if cur is None:
            continue
        low = ln.strip().lower()
        if low.startswith("status:"):
            cur["status"] = ln.split(":", 1)[1].strip() or "open"
        elif low.startswith("assignee:"):
            cur["assignee"] = ln.split(":", 1)[1].strip()
        elif low.startswith("body:"):
            cur["body"] = ln.split(":", 1)[1].strip()
        elif cur["body"] and ln.strip():
            cur["body"] += "\n" + ln.rstrip()
    return tickets


def _block_text(t):
    return (f"## TICKET-{t['num']}: {t['title']}\n"
            f"status: {t['status']}\n"
            f"assignee: {t['assignee']}\n"
            f"body: {t['body']}")


def create_ticket(path, title, body="", assignee=""):
    """Create TICKET-<n> with the next free number (max existing + 1, else 1).
    Returns the new ticket number."""
    title = str(title).strip()
    if not title:
        raise ValueError("ticket title required")
    nums = [t["num"] for t in _parse_tickets(path)]
    n = max(nums) + 1 if nums else 1
    _ensure_header(path, "TICKETS.md")
    text = _read_text(path).rstrip("\n")
    block = (f"## TICKET-{n}: {title}\n"
             f"status: open\n"
             f"assignee: {str(assignee).strip()}\n"
             f"body: {str(body).strip()}")
    _write_text(path, f"{text}\n\n{block}")
    return n


def list_tickets(path, status=None):
    """[{num, title, status, assignee}] in file order. Optional status filter
    (case-insensitive). Missing file → []."""
    tickets = _parse_tickets(path)
    if status is None:
        return tickets
    want = str(status).lower()
    return [t for t in tickets if t["status"].lower() == want]


def update_ticket(path, num, status=None, assignee=None, body=None):
    """Rewrite the TICKET-<num> block: status/assignee/body fields, in place.
    Title is never rewritten. Returns True; ValueError when the ticket is
    missing. A given status must be one of open|in_progress|done."""
    num = int(num)
    lines = _read_lines(path)
    idx = next((i for i, ln in enumerate(lines) if _TICKET_RE.match(ln)
                and int(_TICKET_RE.match(ln).group(1)) == num), None)
    if idx is None:
        raise ValueError(f"ticket TICKET-{num} not found")
    end = next((j for j in range(idx + 1, len(lines))
                if _TICKET_RE.match(lines[j])), len(lines))
    target = next(t for t in _parse_tickets(path) if t["num"] == num)
    if status is not None:
        st = str(status).strip().lower()
        if st not in _STATUS:
            raise ValueError(f"invalid ticket status: {status}")
        target["status"] = st
    if assignee is not None:
        target["assignee"] = str(assignee).strip()
    if body is not None:
        target["body"] = str(body).strip()
    lines[idx:end] = _block_text(target).split("\n")
    _write_lines(path, lines)
    return True


def render_tickets(path, cap=4000):
    """Render TICKETS.md as bounded section text (for context injection).
    Missing file → ""; capped at cap characters, tail cut."""
    if not os.path.exists(path):
        return ""
    tickets = _parse_tickets(path)
    lines = [f"# TICKETS.md — {len(tickets)} ticket(s)"]
    for t in tickets:
        lines.append("")
        lines.append(f"## TICKET-{t['num']}: {t['title']}")
        lines.append(f"status: {t['status']}")
        lines.append(f"assignee: {t['assignee']}")
        lines.append(f"body: {t['body']}")
    return _cap("\n".join(lines) + "\n", cap)


def apply_tickets(plan_tickets, path):
    """Apply plan "tickets" entries to TICKETS.md.
    Returns (created, updated) counts."""
    created = updated = 0
    for e in plan_tickets or []:
        if not isinstance(e, dict):
            continue
        action = str(e.get("action", "create")).lower()
        if action == "update":
            num = e.get("num")
            try:
                num = int(num)
            except (TypeError, ValueError):
                continue
            try:
                update_ticket(path, num, status=e.get("status"),
                              assignee=e.get("assignee"), body=e.get("body"))
            except ValueError:
                continue
            updated += 1
        elif action == "create":
            title = str(e.get("title", "")).strip()
            if not title:
                continue
            create_ticket(path, title, str(e.get("body", "")),
                          str(e.get("assignee", "")))
            created += 1
    return created, updated
