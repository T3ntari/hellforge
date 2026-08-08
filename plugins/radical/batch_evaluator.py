"""Batch Evaluator — group expressions by structure and evaluate in single GPU dispatch.
Provides a higher-level API than raw eval_ast calls."""

from .ast_to_glsl import _collect_vars


def batch_by_structure(expr_list):
    """Group expressions by their AST structure for batch dispatch.
    expr_list: list of (ast_dict, variables_dict, label)
    Returns list of batches: [(ast_dict, [variables_dict, ...], count), ...]
    """
    from ep_compiler.math_engine import ast_to_dict

    batches = {}  # canonical_form -> [entries]
    for ast_dict, variables, label in expr_list:
        # Use the AST dict as key (it's JSON-serializable)
        key = _canonical_form(ast_dict)
        if key not in batches:
            batches[key] = {"ast": ast_dict, "vars": [], "labels": []}
        batches[key]["vars"].append(variables or {})
        batches[key]["labels"].append(label)

    result = []
    for key, batch in batches.items():
        result.append((batch["ast"], batch["vars"], len(batch["vars"]), batch["labels"]))
    return result


def _canonical_form(ast_dict):
    """Generate a canonical string key for an AST dict.
    Two ASTs with the same structure but different variable values
    will have the same key and can be batched together."""
    if ast_dict is None:
        return "NONE"
    t = ast_dict.get("t")
    if t == "NUM":
        return "NUM"
    if t == "VAR":
        return f"VAR:{ast_dict.get('n', '')}"
    if t == "UNARY":
        return f"UNARY:{ast_dict.get('op', '')}({_canonical_form(ast_dict.get('o'))})"
    if t == "BINOP":
        return f"BINOP:{ast_dict.get('op', '')}({_canonical_form(ast_dict.get('l'))},{_canonical_form(ast_dict.get('r'))})"
    if t == "CALL":
        args = ",".join(_canonical_form(a) for a in ast_dict.get("a", []))
        return f"CALL:{ast_dict.get('n', '')}({args})"
    return "OTHER"
