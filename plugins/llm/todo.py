"""Agent-managed TODO.md checklist engine — load / render / apply.

The copilot agent maintains TODO.md through the plan key
"todo": [{"item": "...", "status": "open"|"done"}]:
  - open: append "- [ ] item" (dedupe by text, case-insensitive)
  - done: check off the first case-insensitive match; when the item is
    absent, append it already checked ("- [x] item")
Items are never deleted; "## Section" headers and unknown lines survive
because apply_todo edits the file in place instead of re-rendering it."""

import os
import re

STATUS_OPEN = "open"
STATUS_DONE = "done"

_ITEM_RE = re.compile(r"^-\s*\[\s*([ xX])\s*\]\s+(.*)$")


def load_todo(path):
    """Parse TODO.md → {items: [{text, status}], sections: [names]}.

    "- [ ] item" → status "open", "- [x] item" → status "done",
    "## Name" → section. Missing file → empty structure."""
    data = {"items": [], "sections": []}
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return data
    for ln in lines:
        if ln.startswith("## "):
            data["sections"].append(ln[3:].strip())
            continue
        m = _ITEM_RE.match(ln)
        if m:
            data["items"].append({
                "text": m.group(2).strip(),
                "status": STATUS_DONE if m.group(1).lower() == "x" else STATUS_OPEN,
            })
    return data


def render_todo(path):
    """Render TODO.md as markdown text (for the model and `ai todo`).

    Missing file → empty string."""
    if not os.path.exists(path):
        return ""
    data = load_todo(path)
    done = sum(1 for i in data["items"] if i["status"] == STATUS_DONE)
    lines = ["# TODO — agent-managed checklist",
             f"({len(data['items'])} items, {done} done)"]
    if data["sections"]:
        lines.append("")
        lines.append("Sections: " + ", ".join(data["sections"]))
    if data["items"]:
        lines.append("")
        for item in data["items"]:
            box = "x" if item["status"] == STATUS_DONE else " "
            lines.append(f"- [{box}] {item['text']}")
    return "\n".join(lines) + "\n"


def apply_todo(plan_todo, path):
    """Apply plan "todo" entries to TODO.md. Returns (added, marked_done).

    Open items are appended "- [ ] " deduped by case-insensitive text;
    done items check off the first case-insensitive match or append
    "- [x] " when absent. Existing items are never deleted."""
    added = 0
    marked = 0
    entries = [e for e in (plan_todo or [])
               if isinstance(e, dict) and str(e.get("item", "")).strip()]
    if not entries:
        return 0, 0
    existing = load_todo(path)
    known = {i["text"].lower(): i["status"] for i in existing["items"]}
    lines = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.read().split("\n")
    for e in entries:
        item = str(e["item"]).strip()
        key = item.lower()
        done = str(e.get("status", STATUS_OPEN)).lower() == STATUS_DONE
        if done:
            if key in known:
                if known[key] != STATUS_DONE:
                    for i, ln in enumerate(lines):
                        m = _ITEM_RE.match(ln)
                        if m and m.group(2).strip().lower() == key:
                            lines[i] = ln[:m.start(1)] + "x" + ln[m.end(1):]
                            known[key] = STATUS_DONE
                            marked += 1
                            break
            else:
                lines.append(f"- [x] {item}")
                known[key] = STATUS_DONE
                added += 1
        elif key not in known:
            lines.append(f"- [ ] {item}")
            known[key] = STATUS_OPEN
            added += 1
    while lines and not lines[-1].strip():
        lines.pop()
    text = "\n".join(lines)
    if text and not text.endswith("\n"):
        text += "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return added, marked
