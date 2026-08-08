"""Project listing, session save/restore, multi-session management."""

import json
import os
import re
from datetime import datetime

from .config import (
    c, D, CYAN, GREEN, YELLOW, RED,
    GENERATED_DIR, PROJECT_DIR, PROJECTS_FILE, SESSION_FILE, SESSION_INDEX,
)


def save_project_list():
    projects = []
    if os.path.exists(PROJECTS_FILE):
        try:
            with open(PROJECTS_FILE, "r") as f:
                projects = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    if not os.path.exists(GENERATED_DIR):
        try:
            with open(PROJECTS_FILE, "w") as f:
                json.dump([], f)
        except IOError:
            pass
        return
    seen = set()
    for d in sorted(os.listdir(GENERATED_DIR), reverse=True):
        dp = os.path.join(GENERATED_DIR, d)
        if os.path.isdir(dp) and not d.startswith("."):
            seen.add(dp)
            note_count = 0
            parts = os.path.join(dp, "parts")
            if os.path.isdir(parts):
                for f in os.listdir(parts):
                    if f.endswith(".e"):
                        with open(os.path.join(parts, f), "r") as fh:
                            note_count += sum(1 for l in fh if l.strip().startswith("T"))
            existing = [p for p in projects if p["path"] == dp]
            if existing:
                existing[0]["notes"] = note_count
            else:
                projects.append({"name": d, "path": dp, "notes": note_count, "has_ei": os.path.exists(os.path.join(dp, "index.ei"))})
    projects = [p for p in projects if p["path"] in seen]
    projects.sort(key=lambda p: p["name"], reverse=True)
    try:
        with open(PROJECTS_FILE, "w") as f:
            json.dump(projects[:50], f, indent=2)
    except IOError:
        pass


def list_projects():
    if not os.path.exists(PROJECTS_FILE):
        return []
    try:
        with open(PROJECTS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_session():
    from .config import (
        CONVERSATION,
        CURRENT_PROJECT,
        SAVED_PLAN,
        TOKEN_ESTIMATE,
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    data = {
        "conversation": CONVERSATION[-40:],
        "project": CURRENT_PROJECT,
        "plan": SAVED_PLAN,
        "tokens": TOKEN_ESTIMATE,
        "saved_at": ts,
    }
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        # Keep rolling history: read existing, prepend new, keep 200
        history = []
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r") as f:
                    existing = json.load(f)
                    if isinstance(existing, list):
                        history = existing
                    elif isinstance(existing, dict):
                        history = [existing]
            except (json.JSONDecodeError, IOError):
                pass
        history.insert(0, data)
        history = history[:200]
        with open(SESSION_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except (IOError, TypeError):
        pass


def load_session():
    from .config import (
        CONVERSATION,
        CURRENT_PROJECT,
        SAVED_PLAN,
        TOKEN_ESTIMATE,
    )
    if not os.path.exists(SESSION_FILE):
        return False
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
        # New format: list of sessions — load most recent
        if isinstance(data, list) and data:
            latest = data[0]
        elif isinstance(data, dict):
            latest = data
        else:
            return False
        CONVERSATION[:] = latest.get("conversation", [])
        CURRENT_PROJECT = latest.get("project", None)
        SAVED_PLAN = latest.get("plan", "")
        TOKEN_ESTIMATE = latest.get("tokens", 0)
        return True
    except (json.JSONDecodeError, IOError, IndexError):
        return False


def save_session_snapshot(name=""):
    from .config import (
        CONVERSATION,
        CURRENT_PROJECT,
        SAVED_PLAN,
        TOKEN_ESTIMATE,
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = re.sub(r'[^a-zA-Z0-9]+', '_', name)[:20] if name else ts
    fname = f".session_{safe_name}_{ts}.json"
    path = os.path.join(GENERATED_DIR, fname)
    data = {
        "name": name or f"Session {ts}",
        "conversation": CONVERSATION[-40:],
        "project": CURRENT_PROJECT,
        "plan": SAVED_PLAN,
        "tokens": TOKEN_ESTIMATE,
        "saved_at": ts,
    }
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        index = []
        if os.path.exists(SESSION_INDEX):
            try:
                with open(SESSION_INDEX, "r") as f:
                    index = json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        index.insert(0, {"file": fname, "name": data["name"], "time": ts, "msgs": len(CONVERSATION)})
        index = index[:20]
        with open(SESSION_INDEX, "w") as f:
            json.dump(index, f, indent=2)
        return fname
    except (IOError, TypeError):
        return None


def list_sessions():
    if not os.path.exists(SESSION_INDEX):
        return []
    try:
        with open(SESSION_INDEX, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def load_session_file(fname):
    from .config import (
        CONVERSATION,
        CURRENT_PROJECT,
        SAVED_PLAN,
        TOKEN_ESTIMATE,
    )
    path = os.path.join(GENERATED_DIR, fname)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r") as f:
            data = json.load(f)
        CONVERSATION[:] = data.get("conversation", [])
        CURRENT_PROJECT = data.get("project", None)
        SAVED_PLAN = data.get("plan", "")
        TOKEN_ESTIMATE = data.get("tokens", 0)
        return True
    except (json.JSONDecodeError, IOError):
        return False
