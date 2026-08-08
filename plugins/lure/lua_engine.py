"""LuaJIT runtime bridge — loads .lua accelerator modules, exposes Python API.

GIL RELEASE NOTES
=================
lupa (LuaJIT Python bindings) releases Python's Global Interpreter Lock
during Lua code execution. This means:

1. TRUE PARALLELISM: Multiple calls to parse_lines_batch() from separate
   threads can execute simultaneously across CPU cores. The GIL is only
   held during Python→Lua bridge crossings (function call + return value
   conversion), not during actual LuaJIT execution.

2. BRIDGE CROSSING COST: Each Python→Lua→Python round-trip has overhead
   from data conversion. To maximize performance:
   - GOOD: compiler.parse_batch(1000 lines) — 1 bridge crossing
   - BAD:  compiler.parse(line) × 1000 — 1000 bridge crossings
   Keep execution chunks self-contained in Lua whenever possible.

3. CALLBACK WARNING: If Lua code calls back into Python (e.g., via a
   Python function passed to Lua), the GIL is RE-ACQUIRED. This kills
   parallelism. Avoid Python callbacks inside Lua hot loops.

4. THREAD SAFETY: The LuaRuntime instance is NOT thread-safe for
   concurrent execute() calls. Use separate LuaRuntime instances per
   thread for true parallelism, or serialize calls to a single instance.
"""

import os
import time


class LUREngine:
    """Manages LuaJIT runtime via lupa. Loads accelerator .lua modules on init."""

    def __init__(self):
        self.lua = None
        self.available = False
        self.parse_count = 0
        self.event_count = 0
        self._lua_dir = os.path.dirname(os.path.abspath(__file__))
        self._diagnostic = ""
        self._init()

    def _init(self):
        try:
            import lupa
            from lupa import LuaRuntime
            self.lua = LuaRuntime(unpack_returned_tuples=True)

            test = self.lua.eval("1 + 1")
            if test != 2:
                self._diagnostic = "LuaJIT eval failed"
                return

            # Load each .lua module: execute code, capture returned table, assign to global
            modules = {
                "compiler": "compiler.lua",
                "process_events": "events.lua",
                "quantizer": "quantizer.lua",
                "midi_export": "midi_export.lua",
                "math_processor": "math_processor.lua",
            }

            for global_name, filename in modules.items():
                path = os.path.join(self._lua_dir, filename)
                if not os.path.exists(path):
                    self._diagnostic = f"missing {filename}"
                    return
                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()
                # Wrap so the returned table is captured
                wrapped = f"do local ret = (function()\n{code}\n end)(); {global_name} = ret; end"
                self.lua.execute(wrapped)

            self.available = True
            self._diagnostic = "ready"

        except ImportError:
            self._diagnostic = "lupa not installed (pip install lupa)"
        except Exception as e:
            self._diagnostic = str(e)

    def _table_to_dict(self, tbl):
        """Convert a Lua table to a Python dict."""
        if tbl is None:
            return None
        result = {}
        # Copy all keys using Lua iteration
        for k in tbl:
            result[k] = tbl[k]
        return result

    def _table_to_list(self, tbl):
        """Convert a Lua sequence table to a Python list of dicts."""
        if tbl is None:
            return []
        result = []
        for i in range(1, len(tbl) + 1):
            row = tbl[i]
            if row is not None:
                result.append(self._table_to_dict(row))
        return result

    def parse_line(self, line):
        """Parse a single line of E code. Returns event dict or None."""
        if not self.available:
            return None
        try:
            compiler = self.lua.globals().compiler
            result = compiler.parse(line)
            if result:
                self.parse_count += 1
                return self._table_to_dict(result)
            return None
        except Exception:
            return None

    def parse_lines_batch(self, lines):
        """Parse multiple lines. Returns list of (event or None)."""
        if not self.available or not lines:
            return [None] * len(lines)
        try:
            compiler = self.lua.globals().compiler
            # Convert Python list to Lua table
            lua_lines = self.lua.table_from(lines)
            results = compiler.parse_batch(lua_lines)
            if results:
                self.parse_count += len(lines)
                return [self._table_to_dict(r) if r else None for r in results]
            return [None] * len(lines)
        except Exception:
            return [None] * len(lines)

    def validate_and_sort(self, events):
        """Validate and sort events. Returns (cleaned, removed)."""
        if not self.available:
            return None, 0
        try:
            ev_mod = self.lua.globals().process_events
            result_tbl, removed = ev_mod.validate(events)
            if result_tbl:
                result = self._table_to_list(result_tbl)
                self.event_count += len(result)
                result.sort(key=lambda e: (e.get("timestamp", 0), e.get("midi", 0)))
                return result, removed
            return None, 0
        except Exception:
            return None, 0

    def quantize(self, events, scale_name):
        """Quantize events to scale."""
        if not self.available:
            return None
        try:
            q_mod = self.lua.globals().quantizer
            result = q_mod.quantize(events, scale_name)
            if result:
                return self._table_to_list(result)
            return None
        except Exception:
            return None

    def _py_to_lua(self, obj):
        """Recursively convert Python dicts/lists to Lua tables.
        LuaJIT (via lupa) keeps Python lists as-is (0-indexed), but
        Lua expects 1-indexed tables for ipairs. This conversion
        ensures all nested lists become proper Lua tables."""
        if obj is None:
            return None
        if isinstance(obj, dict):
            tbl = self.lua.table_from({})
            for k, v in obj.items():
                tbl[k] = self._py_to_lua(v)
            return tbl
        if isinstance(obj, (list, tuple)):
            tbl = self.lua.table_from({})
            for i, v in enumerate(obj):
                tbl[i + 1] = self._py_to_lua(v)
            return tbl
        return obj

    def eval_ast(self, ast_dict, variables):
        """Evaluate a math AST using LuaJIT.
        ast_dict: from math_engine.ast_to_dict()
        variables: dict of var_name -> value
        Returns number or None."""
        if not self.available:
            return None
        try:
            math_proc = self.lua.globals().math_processor
            if not math_proc:
                return None
            lua_ast = self._py_to_lua(ast_dict)
            lua_vars = self._py_to_lua(variables)
            result = math_proc.eval(lua_ast, lua_vars)
            if result is not None:
                return float(result)
            return None
        except Exception:
            return None

    def summary(self):
        return {
            "parse_count": self.parse_count,
            "event_count": self.event_count,
            "diagnostic": self._diagnostic,
        }
