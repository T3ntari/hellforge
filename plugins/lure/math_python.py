"""Python Math AST Evaluator — fallback when LURE (LuaJIT) is unavailable.
Registered with lower priority so LURE takes precedence."""

import math


def eval_python(ast_dict, variables):
    """Evaluate a math AST using pure Python.
    ast_dict: JSON-safe dict from math_engine.ast_to_dict()
    variables: dict of $var_name -> value
    Returns number or None."""
    return _eval_node(ast_dict, variables)


_OPS = {
    "+": lambda a, b: a + b,
    "-": lambda a, b: a - b,
    "*": lambda a, b: a * b,
    "/": lambda a, b: a / b,
    "//": lambda a, b: a // b,
    "^": lambda a, b: a ** b,
    "%": lambda a, b: a % b,
}

_FUNCS = {
    "sin": math.sin, "cos": math.cos, "sqrt": math.sqrt,
    "pow": math.pow, "round": round, "floor": math.floor,
    "abs": abs, "min": min, "max": max,
    "quadratic": lambda a, b, c: ((-b + math.sqrt(b*b - 4*a*c)) / (2*a)) if (b*b - 4*a*c) >= 0 else 0,
    "solve_linear": lambda m, x, c: m * x + c,
}


def _eval_node(node, vars):
    if node is None:
        return None

    t = node.get("t")

    if t == "NUM":
        return node.get("v")

    if t == "VAR":
        name = node.get("n", "")
        if name.startswith("$"):
            name = name[1:]
        val = vars.get(name)
        if val is not None:
            try:
                return float(val)
            except (ValueError, TypeError):
                return val
        return None

    if t == "UNARY":
        v = _eval_node(node.get("o"), vars)
        if v is None:
            return None
        return -v if node.get("op") == "-" else v

    if t == "BINOP":
        l = _eval_node(node.get("l"), vars)
        r = _eval_node(node.get("r"), vars)
        if l is None or r is None:
            return None
        op = node.get("op")
        fn = _OPS.get(op)
        return fn(l, r) if fn else None

    if t == "CALL":
        name = node.get("n", "")
        args = [_eval_node(a, vars) for a in node.get("a", [])]
        args = [a for a in args if a is not None]
        fn = _FUNCS.get(name)
        if fn:
            return fn(*args)
        return None

    return None
