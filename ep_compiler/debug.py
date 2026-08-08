"""Centralized debug/trace logging system. Multi-level, timestamped, file-backed."""

import os
import time
import inspect
import threading

# Levels
NONE = 0
ERROR = 1
WARN = 2
INFO = 3
DEBUG = 4
TRACE = 5

LEVEL_NAMES = {0: "NONE", 1: "ERROR", 2: "WARN", 3: "INFO", 4: "DEBUG", 5: "TRACE"}
_NAME_TO_LEVEL = {v: k for k, v in LEVEL_NAMES.items()}

_instances = {}
_global_level = INFO


class DebugSession:
    """Per-compilation debug session with ring buffer and optional file output."""

    def __init__(self, level=None, log_file=None, max_buffer=2000):
        self.level = level if level is not None else _global_level
        self.start_time = time.time()
        self.log_file = log_file
        self.buffer = []
        self.max_buffer = max_buffer
        self._lock = threading.Lock()
        self.compile_count = 0

    def _log(self, level, module, msg, data=None):
        if level > self.level:
            return
        now = time.time()
        wall = time.strftime("%H:%M:%S", time.localtime(now))
        ms = int((now - int(now)) * 1000)
        elapsed = now - self.start_time
        level_name = LEVEL_NAMES.get(level, f"LVL{level}")
        entry = f"[{wall}.{ms:03d} +{elapsed:7.3f}s] [{level_name:5s}] [{module}] {msg}"
        if data is not None:
            entry += f" | {data}"
        with self._lock:
            self.buffer.append(entry)
            if len(self.buffer) > self.max_buffer:
                self.buffer.pop(0)
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(entry + "\n")
            except Exception:
                pass

    def trace(self, module, msg, data=None):
        self._log(TRACE, module, msg, data)

    def debug(self, module, msg, data=None):
        self._log(DEBUG, module, msg, data)

    def info(self, module, msg, data=None):
        self._log(INFO, module, msg, data)

    def warn(self, module, msg, data=None):
        self._log(WARN, module, msg, data)

    def error(self, module, msg, data=None):
        self._log(ERROR, module, msg, data)

    def dump(self, n=50):
        """Print last n entries to stdout."""
        entries = self.buffer[-n:]
        for e in entries:
            print(f"  {e}")

    def save(self, path):
        """Save full buffer to file."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                for e in self.buffer:
                    f.write(e + "\n")
            print(f"  Debug log saved: {path} ({len(self.buffer)} entries)")
        except Exception as ex:
            print(f"  Failed to save debug log: {ex}")

    def flush(self):
        """Write buffer to log_file if set."""
        if self.log_file and self.buffer:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    for e in self.buffer[-100:]:
                        f.write(e + "\n")
            except Exception:
                pass

    @property
    def summary(self):
        counts = {}
        for e in self.buffer:
            for lname in ("TRACE", "DEBUG", "INFO", "WARN", "ERROR"):
                if f"[{lname}]" in e:
                    counts[lname] = counts.get(lname, 0) + 1
                    break
        return {
            "level": LEVEL_NAMES.get(self.level, str(self.level)),
            "entries": len(self.buffer),
            "elapsed": time.time() - self.start_time,
            "counts": counts,
        }


def get_session(name="default"):
    """Get or create a named debug session."""
    if name not in _instances:
        _instances[name] = DebugSession(level=_global_level)
    return _instances[name]


def set_global_level(level):
    """Set debug level for all sessions."""
    global _global_level
    _global_level = level
    for s in _instances.values():
        s.level = level


def reset_sessions():
    """Clear all debug sessions."""
    _instances.clear()


# Convenience module-level functions for quick logging
def trace(module, msg, data=None):
    get_session().trace(module, msg, data)

def debug(module, msg, data=None):
    get_session().debug(module, msg, data)

def info(module, msg, data=None):
    get_session().info(module, msg, data)

def warn(module, msg, data=None):
    get_session().warn(module, msg, data)

def error(module, msg, data=None):
    get_session().error(module, msg, data)
