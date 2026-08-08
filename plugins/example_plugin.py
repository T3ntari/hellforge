"""
Example plugin — adds a custom $repeat variable handler and new syntax.
Place in plugins/ directory. Auto-loaded at startup.
"""

def register(api):
    """Called when plugin is loaded. `api` provides registration functions."""
    api.register_variable_handler(custom_var_handler)
    api.register_syntax(custom_syntax_parser)
    api.log("  > Example plugin registered: $repeat, @shuffle syntax")


def custom_var_handler(name):
    """Handle $repeat_4, $repeat_8, etc. — repeat the last block N times."""
    import re
    m = re.match(r'repeat_(\d+)', name)
    if m:
        count = int(m.group(1))
        return f"// repeat {count} times (handled by plugin)"
    return None


def custom_syntax_parser(text):
    """Handle @shuffle directive — randomize note order in a block."""
    if "@shuffle" not in text:
        return None
    # Plugin would process and return events here
    return None
