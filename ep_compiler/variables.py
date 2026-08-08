"""E Variable System — Scope stack, resolution, interpolation.
Core only: manages variable state. Plugin evaluators compute values.
Expressions are evaluated by registered math evaluators (LURE > PyPy > Python)."""

import re
from .math_engine import (
    build_ast,
    ast_to_dict,
    find_expressions,
    is_var_definition,
    parse_var_definition,
)


class Scope:
    """Per-file variable scope stack."""

    def __init__(self):
        self._scopes = [{}]  # stack of dicts

    def push(self):
        """Push a new scope (entering a loop body, section, etc)."""
        self._scopes.append({})

    def pop(self):
        """Pop the current scope, restoring previous variables."""
        if len(self._scopes) > 1:
            self._scopes.pop()

    def set(self, name, value):
        """Set a variable in the current scope."""
        self._scopes[-1][name] = value

    def get(self, name):
        """Get a variable, searching from current scope outward."""
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def has(self, name):
        return self.get(name) is not None

    def items(self):
        """All variables (flattened, inner scopes override outer)."""
        result = {}
        for scope in self._scopes:
            result.update(scope)
        return result

    def __contains__(self, name):
        return self.has(name)


# Global evaluator registry: plugins register here
_evaluators = []  # list of (priority, name, eval_fn)
_enabled_evaluators = {}  # name -> bool (False = disabled at runtime)


def register_evaluator(name, eval_fn, priority=100):
    """Register a math evaluator. lower priority = tried first.
    eval_fn(ast_dict, variables_dict) -> number or None."""
    _evaluators.append((priority, name, eval_fn))
    _evaluators.sort(key=lambda x: x[0])
    _enabled_evaluators.setdefault(name, True)


def set_evaluator_enabled(name, enabled):
    """Really enable/disable an evaluator at runtime (GPU toggle etc)."""
    _enabled_evaluators[name] = bool(enabled)


def is_evaluator_enabled(name):
    return _enabled_evaluators.get(name, True)


# Auto-register Python fallback evaluator (priority 100)
try:
    from plugins.lure.math_python import eval_python
    register_evaluator("Python", eval_python, priority=100)
except ImportError:
    pass


def evaluate_expression(expr_str, scope=None):
    """Evaluate an expression string using registered evaluators.
    Falls back through: LURE (LuaJIT) → PyPy → Python.
    Returns (result, error). Errors are typed — never a silent None:
      - parse/truncation errors from build_ast
      - division by zero / math domain errors during evaluation
      - unknown function / no evaluator available"""
    ast, err = build_ast(expr_str)
    if err:
        return None, err
    if ast is None:
        return None, "Empty expression"
    ast_dict = ast_to_dict(ast)
    vars_dict = scope.items() if scope else {}

    last_err = None
    for priority, name, eval_fn in _evaluators:
        if not _enabled_evaluators.get(name, True):
            continue
        try:
            result = eval_fn(ast_dict, vars_dict)
            if result is not None:
                return result, None
        except ZeroDivisionError:
            last_err = "Division by zero"
        except (ValueError, OverflowError, ArithmeticError) as e:
            last_err = f"Math error: {e}"
        except Exception as e:
            last_err = f"Evaluator {name} failed: {e}"
    return None, last_err or "No evaluator available"


def resolve_variables(line, scope):
    """Replace $var references in a line with their values.
    Resolves expressions inside {} first, then simple $var lookups."""
    # First, handle {expression} blocks
    for full_match, inner_expr, start, end in find_expressions(line):
        result, err = evaluate_expression(inner_expr, scope)
        if result is not None:
            line = line[:start] + str(result) + line[end:]

    # Then, handle simple $var references (not inside {})
    def replace_var(m):
        name = m.group(1)
        val = scope.get(name)
        if val is not None:
            return str(val)
        return m.group(0)

    line = re.sub(r'\$([a-zA-Z_]\w*)', replace_var, line)
    return line
