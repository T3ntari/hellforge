"""AST to GLSL — convert E math AST dictionary to GLSL compute shader source.
Each expression becomes a compute shader invocation.
Batch expressions are grouped for single-dispatch execution."""

from ep_compiler.math_engine import ast_to_dict

# GLSL function name mapping
_FUNC_MAP = {
    "sin": "sin", "cos": "cos", "sqrt": "sqrt", "pow": "pow",
    "round": "round", "floor": "floor", "abs": "abs",
    "min": "min", "max": "max",
    "quadratic": "radical_quadratic",
    "solve_linear": "radical_solve_linear",
}

_GLSL_HEADER = """#version 430 core
layout(local_size_x = 256) in;

struct Expression {{
    float result;
}};

layout(std430, binding = 0) buffer Output {{
    Expression outputs[];
}};

{inputs}

{helpers}

void main() {{
    uint id = gl_GlobalInvocationIndex.x;
    if (id >= {count}) return;
    outputs[id].result = {expr};
}}
"""


def ast_to_glsl(ast_dict, var_names=None, count=1):
    """Convert an AST dict to a complete GLSL compute shader source.
    ast_dict: from math_engine.ast_to_dict()
    var_names: list of variable names used (for buffer declarations)
    count: number of invocations (batch size)
    Returns (glsl_source, input_decls) tuple.
    """
    var_names = var_names or []
    inputs_decl = _build_inputs(var_names)
    helpers = _build_helpers()
    expr_glsl = _node_to_glsl(ast_dict, var_names)

    source = _GLSL_HEADER.format(
        inputs=inputs_decl,
        helpers=helpers,
        expr=expr_glsl,
        count=count,
    )
    return source


def _node_to_glsl(node, var_names):
    """Recursively convert AST node to GLSL expression string."""
    t = node.get("t")
    if t == "NUM":
        v = node.get("v", 0)
        if isinstance(v, float):
            return f"{v:.10f}" if v != int(v) else f"{int(v)}.0"
        return str(v)

    if t == "VAR":
        name = node.get("n", "").lstrip("$")
        return f"inputs_{name}[id]" if name in var_names else f"{name}"

    if t == "UNARY":
        op = node.get("op", "-")
        operand = _node_to_glsl(node.get("o"), var_names)
        return f"(-{operand})"

    if t == "BINOP":
        op = node.get("op", "+")
        l = _node_to_glsl(node.get("l"), var_names)
        r = _node_to_glsl(node.get("r"), var_names)
        glsl_op = _GLSL_OPS.get(op, op)
        return f"({l} {glsl_op} {r})"

    if t == "CALL":
        name = node.get("n", "")
        args = node.get("a", [])
        glsl_args = ", ".join(_node_to_glsl(a, var_names) for a in args)
        glsl_name = _FUNC_MAP.get(name, name)
        return f"{glsl_name}({glsl_args})"

    if t == "NONE":
        return "0.0"

    return "0.0"


_GLSL_OPS = {
    "+": "+", "-": "-", "*": "*", "/": "/",
    "//": "/",  # integer division in GLSL
    "^": "pow",
    "%": "%",
}


def _build_inputs(var_names):
    """Build GLSL buffer declarations for variables."""
    if not var_names:
        return ""
    decls = []
    for name in var_names:
        decls.append(f"layout(std430, binding = 1) buffer Input_{name} {{ float inputs_{name}[]; }};")
    return "\n".join(decls)


def _build_helpers():
    """Build GLSL helper function implementations."""
    return """
float radical_quadratic(float a, float b, float c) {
    float d = b*b - 4.0*a*c;
    if (d < 0.0) return 0.0;
    return (-b + sqrt(d)) / (2.0*a);
}

float radical_solve_linear(float m, float x, float c) {
    return m * x + c;
}
"""


def ast_list_to_glsl(ast_dicts, var_names=None, count=None):
    """Convert multiple ASTs into a single GLSL shader.
    Each expression is evaluated for all invocations.
    Returns GLSL source string.
    """
    count = count or len(ast_dicts)
    var_names = var_names or []

    # Find all unique variable names across all expressions
    all_vars = set(var_names)
    for ad in ast_dicts:
        _collect_vars(ad, all_vars)
    all_vars = sorted(all_vars)

    # Generate expressions
    exprs = [_node_to_glsl(ad, all_vars) for ad in ast_dicts]

    inputs_decl = _build_inputs(all_vars)
    helpers = _build_helpers()

    # Batch: one invocation per expression
    source = f"""#version 430 core
layout(local_size_x = 256) in;

struct Expression {{
    float result;
}};

layout(std430, binding = 0) buffer Output {{
    Expression outputs[];
}};

{inputs_decl}

{helpers}

void main() {{
    uint id = gl_GlobalInvocationIndex.x;
    if (id >= {count}) return;
    switch(id) {{
"""
    for i, expr in enumerate(exprs):
        source += f"        case {i}: outputs[id].result = {expr}; break;\n"
    source += """        default: outputs[id].result = 0.0; break;
    }
}
"""
    return source


def _collect_vars(node, var_set):
    """Recursively collect variable names from AST."""
    if node is None:
        return
    t = node.get("t")
    if t == "VAR":
        var_set.add(node.get("n", "").lstrip("$"))
    elif t == "UNARY":
        _collect_vars(node.get("o"), var_set)
    elif t in ("BINOP", "ASSIGN"):
        _collect_vars(node.get("l"), var_set)
        _collect_vars(node.get("r"), var_set)
    elif t == "CALL":
        for a in node.get("a", []):
            _collect_vars(a, var_set)
