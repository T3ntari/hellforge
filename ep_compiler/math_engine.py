"""E Math Engine — Tokenizer + AST Builder.
CORE ONLY: parses expressions and builds AST. 
No evaluation — that's done by plugins (LURE, fentclient) via api.register_math_evaluator().
If no evaluator is registered, {$expr} is left as-is in the source."""

import re

# ── Tokenizer ──

TOKEN_SPEC = [
    ("NUMBER", r"\d+\.?\d*"),
    ("IDENT", r"[a-zA-Z_$][a-zA-Z0-9_$]*"),
    ("PLUS", r"\+"), ("MINUS", r"-"), ("MUL", r"\*"), ("FLOORDIV", r"//"), ("DIV", r"/"),
    ("POW", r"\^"), ("MOD", r"%"),
    ("LPAREN", r"\("), ("RPAREN", r"\)"),
    ("COMMA", r","),
    ("ASSIGN", r"="),
    ("WS", r"\s+"),
]


def tokenize(expr):
    tokens = []
    pos = 0
    while pos < len(expr):
        for name, pat in TOKEN_SPEC:
            m = re.match(pat, expr[pos:])
            if m:
                val = m.group(0)
                if name != "WS":
                    tokens.append((name, val))
                pos += len(val)
                break
        else:
            pos += 1
    return tokens


# ── AST Builder (recursive descent, operator precedence) ──

class ASTNode:
    def __init__(self, type, **kwargs):
        self.type = type
        self.__dict__.update(kwargs)
    def __repr__(self):
        return f"AST({self.type}, {self.__dict__})"


def parse_expr(tokens, start=0):
    """Parse expression with proper precedence:
       lowest:  +=  →  |  →  ^  →  unary-  →  atom  highest"""
    node, pos = parse_assign(tokens, start)
    return node, pos


def parse_assign(tokens, pos):
    node, pos = parse_add(tokens, pos)
    if pos < len(tokens) and tokens[pos][0] == "ASSIGN":
        op = tokens[pos][1]
        right, pos = parse_add(tokens, pos + 1)
        node = ASTNode("ASSIGN", left=node, right=right)
    return node, pos


def parse_add(tokens, pos):
    node, pos = parse_mul(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] in ("PLUS", "MINUS"):
        op = tokens[pos][1]
        right, pos = parse_mul(tokens, pos + 1)
        node = ASTNode("BINOP", op=op, left=node, right=right)
    return node, pos


def parse_mul(tokens, pos):
    node, pos = parse_unary(tokens, pos)
    while pos < len(tokens) and tokens[pos][0] in ("MUL", "DIV", "MOD", "FLOORDIV"):
        op = tokens[pos][1]
        right, pos = parse_unary(tokens, pos + 1)
        node = ASTNode("BINOP", op=op, left=node, right=right)
    return node, pos


def parse_unary(tokens, pos):
    if pos < len(tokens) and tokens[pos][0] == "MINUS":
        op = tokens[pos][1]
        node, pos = parse_pow(tokens, pos + 1)
        return ASTNode("UNARY", op=op, operand=node), pos
    return parse_pow(tokens, pos)


def parse_pow(tokens, pos):
    """Power is right-associative: 2^3^2 == 2^(3^2)."""
    node, pos = parse_atom(tokens, pos)
    if pos < len(tokens) and tokens[pos][0] == "POW":
        op = tokens[pos][1]
        right, pos = parse_pow(tokens, pos + 1)  # recurse for right-assoc
        node = ASTNode("BINOP", op=op, left=node, right=right)
    return node, pos


def parse_atom(tokens, pos):
    if pos >= len(tokens):
        return ASTNode("NONE"), pos
    tt, tv = tokens[pos]
    if tt == "NUMBER":
        return ASTNode("NUM", value=float(tv) if "." in tv else int(tv)), pos + 1
    if tt == "IDENT":
        if pos + 1 < len(tokens) and tokens[pos + 1][0] == "LPAREN":
            # Function call
            name = tv
            args, pos = parse_args(tokens, pos + 2)
            return ASTNode("CALL", name=name, args=args), pos
        return ASTNode("VAR", name=tv), pos + 1
    if tt == "LPAREN":
        node, pos = parse_expr(tokens, pos + 1)
        if pos < len(tokens) and tokens[pos][0] == "RPAREN":
            pos += 1
        return node, pos
    return ASTNode("NONE"), pos + 1


def parse_args(tokens, pos):
    args = []
    while pos < len(tokens) and tokens[pos][0] != "RPAREN":
        if args:
            if tokens[pos][0] == "COMMA":
                pos += 1
        arg, pos = parse_expr(tokens, pos)
        args.append(arg)
    return args, pos + 1 if pos < len(tokens) else pos


_KNOWN_FUNCS = {"sin", "cos", "sqrt", "pow", "round", "floor", "abs",
                "min", "max", "quadratic", "solve_linear"}


def _validate_ast(node):
    """Reject NONE nodes and unknown function names — never silent."""
    if node is None:
        return None
    if node.type == "NONE":
        return "Incomplete expression (missing operand)"
    if node.type == "CALL" and node.name not in _KNOWN_FUNCS:
        return f"Unknown function: {node.name}"
    for key in ("left", "right", "operand"):
        child = getattr(node, key, None)
        if child is not None:
            err = _validate_ast(child)
            if err:
                return err
    for arg in getattr(node, "args", None) or []:
        err = _validate_ast(arg)
        if err:
            return err
    return None


def build_ast(expr):
    """Parse an expression string into an AST. Returns (ASTNode, error).
    Errors on leftover unconsumed tokens — never silently truncates."""
    try:
        tokens = tokenize(expr)
        if not tokens:
            return None, "Empty expression"
        ast, pos = parse_expr(tokens)
        if pos < len(tokens):
            leftover = tokens[pos]
            return None, f"Unexpected token '{leftover[1]}' at position {pos+1}"
        err = _validate_ast(ast)
        if err:
            return None, err
        return ast, None
    except Exception as e:
        return None, str(e)


# ── AST Serialization (JSON-safe, for sending to LURE) ──

def ast_to_dict(node):
    """Convert AST to JSON-safe dict for plugin evaluators."""
    if node is None:
        return None
    d = {"t": node.type}
    if node.type == "NUM":
        d["v"] = node.value
    elif node.type == "VAR":
        d["n"] = node.name
    elif node.type == "UNARY":
        d["op"] = node.op
        d["o"] = ast_to_dict(node.operand)
    elif node.type == "BINOP":
        d["op"] = node.op
        d["l"] = ast_to_dict(node.left)
        d["r"] = ast_to_dict(node.right)
    elif node.type == "CALL":
        d["n"] = node.name
        d["a"] = [ast_to_dict(a) for a in node.args]
    elif node.type == "ASSIGN":
        d["l"] = ast_to_dict(node.left)
        d["r"] = ast_to_dict(node.right)
    return d


# ── Expression Detection ──

EXPR_RE = re.compile(r"\{(.+?)\}")


def find_expressions(text):
    """Find all {expr} in a string. Returns list of (full_match, inner_expr, start, end)."""
    return [(m.group(0), m.group(1), m.start(), m.end()) for m in EXPR_RE.finditer(text)]


VAR_DEF_RE = re.compile(r"^\$([a-zA-Z_]\w*)\s*=\s*(.+)$")


def is_var_definition(line):
    """Check if a line is a variable definition like $bpm = 120."""
    return bool(VAR_DEF_RE.match(line.strip()))


def parse_var_definition(line):
    """Parse $bpm = 120 into (name, expr_str)."""
    m = VAR_DEF_RE.match(line.strip())
    if m:
        return m.group(1), m.group(2)
    return None, None
