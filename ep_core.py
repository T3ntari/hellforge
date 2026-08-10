"""
E Language Core — Plugin/Mod loader, variable system, encryption, portable paths.
"""

import importlib.util
import importlib.machinery
import inspect
import json
import os
import re
import sys
import hashlib
import base64
import hmac
import time
from pathlib import Path

# Terminal colors
R_ = "\033[0m"; B_ = "\033[1m"; D_ = "\033[2m"
RED_ = "\033[91m"; GREEN_ = "\033[92m"; YELLOW_ = "\033[93m"
CYAN_ = "\033[96m"; GREY_ = "\033[90m"


def c(text, color=""):
    return f"{color}{text}{R_}" if color and sys.stdout.isatty() else text

PROJECT_DIR = Path(__file__).parent.resolve()
PLUGINS_DIR = PROJECT_DIR / "plugins"
MODS_DIR = PROJECT_DIR / "mods"
ENCRYPTION_DIR = PROJECT_DIR / "encryption"

# ── Plugin / Mod Registry ────────────────────

_plugins = {}
_mods = {}
_encryptors = {}
_variable_handlers = []
_syntax_handlers = []
_plugin_directives = {}
_boot_steps = []  # (label, status) for boot progress bar
_disabled_plugins = set()
_disabled_mods = set()
_plugin_configs = {}
_gc_enabled = True
_last_compiled_events = []
_auth_providers = {}  # name -> config dict
_auth_tokens = {}  # provider -> token dict
_compilation_count = 0
_plugin_dependencies = {}  # plugin_name -> [pip_package, ...]
_CONFIG_FILE = PROJECT_DIR / ".plugin_config.json"


def _load_plugin_configs():
    global _plugin_configs, _auth_tokens
    try:
        if _CONFIG_FILE.exists():
            import json
            with open(_CONFIG_FILE) as f:
                data = json.load(f)
                _plugin_configs.update(data)
                _auth_tokens.update(data.get("_auth_tokens", {}))
    except Exception:
        pass


def _save_plugin_configs():
    try:
        import json
        with open(_CONFIG_FILE, "w") as f:
            json.dump(_plugin_configs, f, indent=2)
    except Exception:
        pass


# Load configs at module import time
_load_plugin_configs()


def _load_disabled_state():
    """Load disabled plugins/mods from config."""
    disabled = _plugin_configs.get("_disabled", {})
    _disabled_plugins.update(disabled.get("plugins", []))
    _disabled_mods.update(disabled.get("mods", []))


def _save_disabled_state():
    """Save disabled plugins/mods to config."""
    disabled = _plugin_configs.get("_disabled", {})
    disabled["plugins"] = sorted(_disabled_plugins)
    disabled["mods"] = sorted(_disabled_mods)
    _plugin_configs["_disabled"] = disabled
    _save_plugin_configs()


_load_disabled_state()


def _error(msg):
    print(f"  {RED_}✗{R_} {msg}")

def _warn(msg):
    print(f"  {YELLOW_}⚠{R_} {msg}")

def _ok(msg):
    print(f"  {GREEN_}✓{R_} {msg}")

def _fatal(msg, plugin_name=None, pkg_type="plugin"):
    """Print a fatal error and auto-disable the plugin/mod."""
    print(f"  {RED_}☠ FATAL{R_} {msg}")
    if plugin_name:
        if pkg_type == "mod":
            _disabled_mods.add(plugin_name)
        else:
            _disabled_plugins.add(plugin_name)
        _save_disabled_state()
        print(f"  {YELLOW_}  Auto-disabled: {plugin_name}{R_}")


def _load_module(path, module_name, security_scan=False):
    """Load a single module from a .py file path, with optional AST scan."""
    try:
        if security_scan:
            content = path.read_bytes()
            issues = ast_scan(content)
            if issues:
                _warn(f"Mod rejected (security): {path.name}")
                for line, issue in issues[:3]:
                    print(f"    line {line}: {_warn(issue)}")
                return None
        spec = importlib.util.spec_from_file_location(module_name, path)
        if not spec or not spec.loader:
            return None
        mod = importlib.util.module_from_spec(spec)
        if '.' in module_name:
            mod.__package__ = module_name.rsplit('.', 1)[0]
        else:
            mod.__package__ = module_name
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        if security_scan:
            if hasattr(mod, "init"):
                import types
                restricted = types.ModuleType(module_name)
                restricted.__dict__.update(mod.__dict__)
                restricted.__builtins__ = RESTRICTED_BUILTINS
                restricted.init(_plugin_api)
        else:
            if hasattr(mod, "register"):
                mod.register(_plugin_api)
        return mod
    except Exception as e:
        is_fatal = "cannot import name" in str(e) or "ModuleNotFoundError" in str(e) or "SyntaxError" in str(e)
        if is_fatal:
            _fatal(f"{path.name}: {e}", path.stem, "mod" if security_scan else "plugin")
        else:
            _error(f"{path.name}: {e}")
        return None


def _scan_dir(target_dir, entry_fn, security_scan=False):
    """Load from both .py files and subdirectories with __init__.py.
    Skips conflicts where a file and directory share the same name."""
    if not target_dir.exists():
        return
    sys.path.insert(0, str(target_dir))
    
    # Collect names to detect file/dir conflicts
    file_names = set()
    dir_names = set()
    for f in target_dir.glob("*.py"):
        if f.name.startswith("_") or f.name == "__init__.py":
            continue
        file_names.add(f.stem)
    for d in target_dir.iterdir():
        if d.is_dir() and not d.name.startswith("_"):
            dir_names.add(d.name)
    
    # Conflicts: skip the file if a dir with same name exists
    conflicts = file_names & dir_names
    if conflicts:
        for c in conflicts:
            _warn(f"Conflict: '{c}.py' and '{c}/' — using directory")

    # Single-file .py (skip if same-named dir exists)
    for f in sorted(target_dir.glob("*.py")):
        if f.name.startswith("_") or f.name == "__init__.py":
            continue
        if f.stem in dir_names:
            continue  # directory takes priority
        yield f.stem, _load_module(f, f.stem, security_scan)
    # Directory-based: dir/__init__.py
    for d in sorted(target_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_"):
            continue
        init_file = d / "__init__.py"
        if init_file.exists():
            yield d.name, _load_module(init_file, d.name, security_scan)


def install_dependency(package):
    """Install a pip package. Returns True if successful or already installed."""
    import subprocess as _sp
    try:
        __import__(package.replace("-", "_"))
        return True
    except ImportError:
        pass
    _warn(f"Installing dependency: {package}")
    try:
        r = _sp.run(
            [sys.executable, "-m", "pip", "install", "--quiet", package],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120
        )
        if r.returncode == 0:
            _ok(f"Dependency installed: {package}")
            return True
        _error(f"Failed to install {package}: {r.stderr.strip()[:200]}")
        return False
    except Exception as e:
        _error(f"Failed to install {package}: {e}")
        return False


def check_plugin_dependencies(name, deps_list):
    """Check and install all dependencies for a plugin. Returns True if all OK."""
    if not deps_list:
        return True
    _boot_steps.append((f"{name}: checking deps ({len(deps_list)} packages)", "loading"))
    all_ok = True
    for dep in deps_list:
        if not install_dependency(dep):
            all_ok = False
    if all_ok:
        _boot_steps.append((f"{name}: deps OK", "done"))
    return all_ok


def load_plugins():
    """Load all plugins from plugins/ (single .py + dir/__init__.py), skipping disabled."""
    # Read dependencies from pkglist.json
    pkglist_deps = {}
    try:
        pkglist_path = PROJECT_DIR / "pkglist.json"
        if pkglist_path.exists():
            with open(pkglist_path, "r") as _f:
                _data = json.load(_f)
            for _ptype in ("plugins", "mods"):
                for _name, _info in _data.get(_ptype, {}).items():
                    _deps = _info.get("dependencies", [])
                    if _deps:
                        pkglist_deps[_name] = _deps
    except Exception:
        pass

    for name, mod in _scan_dir(PLUGINS_DIR, "register", security_scan=False):
        if name in _disabled_plugins:
            _boot_steps.append((f"Plugin: {name} (disabled)", "skip"))
            continue
        if not mod:
            continue

        # Strict signing check: verify plugin signature if strict mode >= 1
        if _STRICT_SIGNING >= 1:
            mod_file = getattr(mod, "__file__", None)
            if mod_file:
                v, level, author, detail = verify_signature(mod_file)
                if not v:
                    if _STRICT_SIGNING >= 2:
                        _fatal(f"Signature check FAILED for {name}: {detail}", name, "plugin")
                        _boot_steps.append((f"Plugin: {name} (blocked — unsigned)", "skip"))
                        continue
                    else:
                        _warn(f"Plugin {name}: {detail}")
            elif _STRICT_SIGNING >= 2:
                _fatal(f"Cannot verify {name}: no source file", name, "plugin")
                _boot_steps.append((f"Plugin: {name} (blocked — no file)", "skip"))
                continue

        # Check and install dependencies from pkglist
        deps = pkglist_deps.get(name, [])
        inline_deps = _plugin_dependencies.get(name, [])
        all_deps = list(set(deps + inline_deps))
        if all_deps:
            if not check_plugin_dependencies(name, all_deps):
                _fatal(f"Dependency installation failed for {name}", name, "plugin")
                _boot_steps.append((f"Plugin: {name} (dep install failed)", "skip"))
                continue
        _plugins[name] = mod
        _boot_steps.append((f"Plugin: {name}", "loaded"))


def load_mods():
    """Load all mods from mods/ (single .py + dir/__init__.py) with AST scan, skipping disabled."""
    for name, mod in _scan_dir(MODS_DIR, "init", security_scan=True):
        if name in _disabled_mods:
            _boot_steps.append((f"Mod: {name} (disabled)", "skip"))
            continue
        if not mod:
            continue
        deps = _plugin_dependencies.get(name, [])
        if deps:
            if not check_plugin_dependencies(name, deps):
                _fatal(f"Dependency installation failed for {name}", name, "mod")
                _boot_steps.append((f"Mod: {name} (dep install failed)", "skip"))
                continue
        _mods[name] = mod
        _boot_steps.append((f"Mod: {name}", "loaded"))


def ast_scan(source_bytes):
    """Scan Python source using AST analysis. Returns list of (line, issue) tuples.
    Catches obfuscated calls that string-based scanning misses."""
    import ast as _ast
    issues = []

    BLOCKED_FUNCS = {
        'system', 'popen', 'call', 'run', 'Popen', 'check_call',
        'check_output', 'getoutput', 'getstatusoutput',
    }
    BLOCKED_NAMES = {
        'eval', 'exec', 'compile', '__import__', 'open',
        'input', 'breakpoint',
    }
    BLOCKED_DUNDERS = {
        '__import__', '__subclasses__', '__globals__', '__code__',
        '__builtins__', '__dict__',
    }
    SAFE_DUNDERS = {'__init__', '__str__', '__repr__', '__call__'}

    try:
        tree = _ast.parse(source_bytes.decode("utf-8", errors="replace"))
    except SyntaxError as e:
        return [(0, f"syntax error: {e}")]

    for node in _ast.walk(tree):
        # Block direct dangerous function calls: os.system(...)
        if isinstance(node, _ast.Call):
            if isinstance(node.func, _ast.Attribute):
                if node.func.attr in BLOCKED_FUNCS:
                    issues.append((getattr(node, 'lineno', 0), f"call to .{node.func.attr}"))
            if isinstance(node.func, _ast.Name):
                if node.func.id in BLOCKED_NAMES:
                    issues.append((getattr(node, 'lineno', 0), f"call to {node.func.id}"))

        # Block getattr() — used for obfuscated access
        if isinstance(node, _ast.Call) and isinstance(node.func, _ast.Name):
            if node.func.id == 'getattr':
                issues.append((getattr(node, 'lineno', 0), "getattr() — dynamic attribute access blocked"))
            if node.func.id == 'setattr':
                issues.append((getattr(node, 'lineno', 0), "setattr() blocked"))

        # Block dangerous dunder function definitions
        if isinstance(node, _ast.FunctionDef):
            if node.name.startswith('__') and node.name.endswith('__'):
                if node.name not in SAFE_DUNDERS:
                    issues.append((getattr(node, 'lineno', 0), f"suspicious dunder: {node.name}"))

        # Block attribute access to __builtins__ etc
        if isinstance(node, _ast.Attribute):
            if node.attr in BLOCKED_DUNDERS:
                issues.append((getattr(node, 'lineno', 0), f"access to .{node.attr}"))

    return issues


# Restricted builtins for mod execution (no import, no file I/O, no subprocess)
RESTRICTED_BUILTINS = {
    'None': None, 'True': True, 'False': False,
    'int': int, 'float': float, 'str': str, 'bool': bool,
    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
    'len': len, 'range': range, 'zip': zip, 'map': map, 'filter': filter,
    'min': min, 'max': max, 'sum': sum, 'abs': abs, 'round': round,
    'print': print, 'isinstance': isinstance, 'hasattr': hasattr,
    'type': type, 'object': object, 'property': property,
    'enumerate': enumerate, 'reversed': reversed, 'sorted': sorted,
    'iter': iter, 'next': next, 'any': any, 'all': all,
    'Exception': Exception, 'ValueError': ValueError, 'TypeError': TypeError,
    'KeyError': KeyError, 'IndexError': IndexError, 'AttributeError': AttributeError,
    'StopIteration': StopIteration,
}


# ── Plugin API v2 ────────────────────────────

# Extended registries
_eshell_commands = {}


def _caller_plugin():
    """Best-effort name of the plugin registering a command (via the
    call stack). Returns None when not called from plugins/."""
    import inspect
    try:
        for fr in inspect.stack()[2:]:
            fname = fr.filename or ""
            fname = fname.replace("\\", "/")
            if "/plugins/" in fname:
                rest = fname.split("/plugins/", 1)[1]
                return rest.split("/")[0].split(".")[0]
    except Exception:
        pass
    return None
_eshell_keybindings = {}
_eshell_prompt_renderers = []
_eshell_output_filters = []
_gc_strategies = {}
_event_hooks = {"pre_compile": [], "post_compile": [], "pre_play": [],
                "post_play": [], "pre_render": [], "post_render": [],
                "on_load": [], "on_unload": [], "on_exit": []}
_plugin_help_texts = []  # list of (section_title, lines: list) for eshell help
_theme = {"prompt_color": "\033[92m", "accent_color": "\033[96m",
          "dim_color": "\033[90m", "error_color": "\033[91m",
          "success_color": "\033[92m", "warning_color": "\033[93m",
          "banner_art": "", "prompt_char": ">"}


class _PluginAPI:
    """API object passed to plugins. Full eshell integration."""
    def register_syntax(self, handler):
        _syntax_handlers.append(handler)
    def register_variable_handler(self, handler):
        _variable_handlers.append(handler)
    def register_encryptor(self, name, enc, dec):
        _encryptors[name] = (enc, dec)

    # ── v2 API: eshell integration ──
    def add_command(self, name, handler, help_text=""):
        _eshell_commands[name] = (handler, help_text, _caller_plugin())

    def require(self, *packages):
        """Declare a pip dependency. Installed automatically on boot.
        Usage: api.require('numpy', 'scipy')"""
        caller_name = "unknown"
        try:
            import traceback
            frame = traceback.extract_stack()[-3]
            caller_path = frame.filename
            caller_name = Path(caller_path).stem
        except Exception:
            pass
        _plugin_dependencies.setdefault(caller_name, [])
        for pkg in packages:
            if pkg not in _plugin_dependencies[caller_name]:
                _plugin_dependencies[caller_name].append(pkg)

    def add_keybinding(self, key, action, description=""):
        _eshell_keybindings[key] = (action, description)

    def set_prompt_renderer(self, renderer):
        _eshell_prompt_renderers.append(renderer)

    def add_output_filter(self, filter_fn):
        _eshell_output_filters.append(filter_fn)

    def on(self, event, callback):
        if event in _event_hooks:
            _event_hooks[event].append(callback)

    def register_gc(self, name, strategy_fn):
        _gc_strategies[name] = strategy_fn

    def add_help_section(self, title, lines):
        """Add a section to the eshell help command."""
        _plugin_help_texts.append((title, lines))

    def get_config(self, key, default=None):
        """Get a config value from the plugin's config store."""
        return _plugin_configs.get(key, default)

    def set_config(self, key, value):
        """Set a config value in the plugin's config store."""
        _plugin_configs[key] = value
        _save_plugin_configs()

    def get_all_configs(self):
        """Return all plugin configs as a dict."""
        return dict(_plugin_configs)

    def register_auth_provider(self, name, config):
        """Register an auth provider (spotify, openai, etc.).
        config: { 'login_url', 'token_url', 'handler', 'refresh', 'scopes' }"""
        _auth_providers[name] = config

    def get_auth_token(self, provider):
        """Get stored auth token for a provider."""
        return _auth_tokens.get(provider)

    def set_auth_token(self, provider, token):
        """Store an auth token for a provider (persisted in config)."""
        _auth_tokens[provider] = token
        _plugin_configs["_auth_tokens"] = _auth_tokens
        _save_plugin_configs()

    def clear_auth_token(self, provider):
        """Remove stored auth token."""
        _auth_tokens.pop(provider, None)
        _plugin_configs["_auth_tokens"] = _auth_tokens
        _save_plugin_configs()

    def get_auth_providers(self):
        """List registered auth provider names."""
        return dict(_auth_providers)

    def register_directive(self, pattern, handler):
        """Register a @directive parser. Pattern is regex, handler gets (match, state)."""
        _plugin_directives[pattern] = handler

    def register_math_evaluator(self, name, eval_fn, priority=100):
        """Register a math expression evaluator (from plugins/lure, radical, etc).
        eval_fn(ast_dict, variables_dict) -> number.
        Lower priority = tried first."""
        try:
            from ep_compiler.variables import register_evaluator
            register_evaluator(name, eval_fn, priority)
        except Exception:
            pass

    def set_theme(self, **kwargs):
        for k, v in kwargs.items():
            if k in _theme:
                _theme[k] = v

    def add_boot_step(self, label, status="pending"):
        """Add a step to the boot progress bar."""
        _boot_steps.append((label, status))

    def log(self, msg):
        print(msg)

    @property
    def project_dir(self):
        return str(PROJECT_DIR)
    @property
    def commands(self):
        return dict(_eshell_commands)
    @property
    def theme(self):
        return dict(_theme)


_plugin_api = _PluginAPI()


def _register_syntax(handler):
    _syntax_handlers.append(handler)
def _register_variable_handler(handler):
    _variable_handlers.append(handler)
def _register_encryptor(name, enc, dec):
    _encryptors[name] = (enc, dec)


# ── Event Hooks ──────────────────────────────

def trigger_event(event, *args, **kwargs):
    """Trigger all callbacks for an event. Returns list of non-None return values."""
    results = []
    for cb in _event_hooks.get(event, []):
        try:
            r = cb(*args, **kwargs)
            if r is not None:
                results.append(r)
        except Exception as e:
            print(f"  > Event '{event}' error: {e}")
    return results


def apply_output_filters(text):
    """Run text through all output filters."""
    for f in _eshell_output_filters:
        try:
            text = f(text)
        except Exception:
            pass
    return text


# ── Encryption (.ee) ─────────────────────────

def _base_encrypt(data: bytes, key: str = "e-lang-default") -> bytes:
    """Simple XOR + base64 encryption."""
    k = key.encode()
    xored = bytes(data[i] ^ k[i % len(k)] for i in range(len(data)))
    return base64.b64encode(xored)


def _base_decrypt(data: bytes, key: str = "e-lang-default") -> bytes:
    """Reverse of base_encrypt."""
    try:
        xored = base64.b64decode(data)
    except Exception:
        return data
    k = key.encode()
    return bytes(xored[i] ^ k[i % len(k)] for i in range(len(xored)))


_encryptors["base"] = (_base_encrypt, _base_decrypt)


def encrypt_e(source_path, output_path, method="base", key=None):
    """Encrypt a .e file to .ee format."""
    with open(source_path, "rb") as f:
        data = f.read()

    enc = _encryptors.get(method)
    if not enc:
        raise ValueError(f"Unknown encryption: {method}. Available: {list(_encryptors.keys())}")

    encrypted = enc[0](data, key or "e-lang-default")

    header = json.dumps({"method": method, "key_hint": hashlib.md5((key or "e-lang-default").encode()).hexdigest()[:8]}).encode() + b"\n"
    with open(output_path, "wb") as f:
        f.write(header + encrypted)

    print(f"  > Encrypted -> {output_path} ({method})")
    return True


def decrypt_ee(path, key=None):
    """Decrypt a .ee file and return raw bytes."""
    with open(path, "rb") as f:
        header_line = f.readline()
        encrypted = f.read()

    header = json.loads(header_line.decode())
    method = header.get("method", "base")

    enc = _encryptors.get(method)
    if not enc:
        raise ValueError(f"Unknown encryption: {method}")

    return enc[1](encrypted, key or "e-lang-default")


# ── EZip Package Handler ─────────────────────

EZIP_MAGIC = b"EzPk"
MODS_DIR = PROJECT_DIR / "mods"
PLUGINS_DIR = PROJECT_DIR / "plugins"


def install_ezip(path, target_type="mod"):
    """Install a .ezip package: validate manifest, extract, register."""
    import zipfile
    import json
    import shutil
    import tempfile

    path = Path(str(path).strip("\"'"))
    if not path.exists():
        return print(f"  {c('✗ file not found:', RED)} {path}")

    target_dir = MODS_DIR if target_type == "mod" else PLUGINS_DIR
    try:
        with zipfile.ZipFile(path, "r") as zf:
            # Validate magic
            magic = zf.read("EzPk")
            if magic != EZIP_MAGIC:
                print(f"  {c('✗ invalid EZip (missing EzPk)', RED)}")
                return

            # Read manifest
            if "manifest.json" not in zf.namelist():
                return print(f"  {c('✗ no manifest.json in EZip', RED)}")
            manifest = json.loads(zf.read("manifest.json"))
            name = manifest.get("name", path.stem)
            version = manifest.get("version", "?")
            ptype = manifest.get("type", target_type)
            entry = manifest.get("entry", "main.py")

            # Security scan
            for fname in zf.namelist():
                if fname.endswith(".py"):
                    content = zf.read(fname)
                    for pat in SECURITY_BLOCKLIST:
                        if pat in content:
                            print(f"  {c(f'✗ security block: {pat.decode()} in {fname}', RED)}")
                            return

            # Extract
            extract_dir = target_dir / name
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            zf.extractall(extract_dir)

            # Register entry point
            entry_path = extract_dir / entry
            if entry_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location(f"{target_type}.{name}", entry_path)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    if hasattr(mod, "register"):
                        mod.register(_plugin_api)
                        print(f"  {c('✓', GREEN)} {target_type} '{name}' v{version} loaded")

            print(f"  {c('✓', GREEN)} installed {target_type}  {c(name, CYAN)} v{version}  ({extract_dir})")

    except zipfile.BadZipFile:
        print(f"  {c('✗ invalid zip file', RED)}")
    except json.JSONDecodeError:
        print(f"  {c('✗ invalid manifest.json', RED)}")
    except Exception as e:
        print(f"  {c(f'✗ install error: {e}', RED)}")


def list_ezip_contents(path):
    """List contents of an EZip file without extracting."""
    import zipfile
    path = Path(str(path).strip("\"'"))
    if not path.exists():
        return print(f"  {c('✗ file not found:', RED)} {path}")
    try:
        with zipfile.ZipFile(path, "r") as zf:
            if "manifest.json" in zf.namelist():
                manifest = json.loads(zf.read("manifest.json"))
                print(f"  {c('Package:', CYAN)} {manifest.get('name','?')} v{manifest.get('version','?')}")
                print(f"  {c('Type:', D)} {manifest.get('type','mod')}  {c('Author:', D)} {manifest.get('author','?')}")
                print(f"  {c('Description:', D)} {manifest.get('description','')}")
            print(f"  {c('Contents:', B)}")
            for f in sorted(zf.namelist()):
                info = zf.getinfo(f)
                sz = info.file_size // 1024
                print(f"    {c(f'{sz}KB', D)} {f}")
    except zipfile.BadZipFile:
        print(f"  {c('✗ invalid zip', RED)}")


# ── GC Engine ────────────────────────────────

def default_gc(events):
    """Default garbage collection: clean up events for quality/sanity."""
    if not events:
        return events
    cleaned = []
    seen = set()
    for e in events:
        # Remove out-of-range MIDI
        midi = e.get("midi", -1)
        if midi < 0 or midi > 127:
            continue
        # Clamp velocity
        e["velocity"] = max(0, min(127, e.get("velocity", 80)))
        # Remove zero-duration
        if e.get("duration", 0) <= 0:
            continue
        # Dedup identical events at same timestamp
        key = (e["timestamp"], e["midi"], e["duration"], e["velocity"])
        if key not in seen:
            seen.add(key)
            cleaned.append(e)
    print(f"  > GC: {len(events)} -> {len(cleaned)} events ({len(events)-len(cleaned)} removed)")
    return cleaned


def aggressive_gc(events):
    """Aggressive GC: merge overlapping same-pitch notes only if they're likely
    unintentional duplicates. Preserves intentional overlaps (different velocity,
    different channel, staccato separation, or large gap-to-overlap ratio)."""
    events = default_gc(events)
    if not events:
        return events
    events.sort(key=lambda e: (e["timestamp"], e["midi"]))
    merged = []
    for e in events:
        if not merged:
            merged.append(e)
            continue
        prev = merged[-1]
        # Only merge same pitch AND same channel
        if prev["midi"] != e["midi"] or prev.get("channel") != e.get("channel"):
            merged.append(e)
            continue

        prev_end = prev["timestamp"] + prev["duration"]
        gap = e["timestamp"] - prev["timestamp"]
        overlap = prev_end - e["timestamp"]

        # Don't merge if:
        # 1. Notes don't actually overlap (gap > 0 with space between)
        if gap >= 0 and e["timestamp"] >= prev_end:
            merged.append(e)
            continue

        # 2. Velocity differs significantly (intentional accent/rearticulation)
        vel_diff = abs(prev["velocity"] - e["velocity"])
        if vel_diff >= 12:
            merged.append(e)
            continue

        # 3. Overlap is small relative to duration (staccato rearticulation)
        if overlap < min(prev["duration"], e["duration"]) * 0.3:
            merged.append(e)
            continue

        # 4. Gap between note-on times is large (separate musical gesture)
        if gap > prev["duration"] * 0.5:
            merged.append(e)
            continue

        # Safe to merge: extend the first note's duration to cover both
        prev["duration"] = max(prev["duration"], e["duration"] + gap)

    removed = len(events) - len(merged)
    if removed > 0:
        print(f"  > GC (aggressive): {len(events)} -> {len(merged)} events ({removed} merged)")
    return merged


_gc_strategies["default"] = default_gc
_gc_strategies["aggressive"] = aggressive_gc


def run_gc(events, strategy="default"):
    """Run garbage collection on events using named strategy."""
    if strategy in _gc_strategies:
        return _gc_strategies[strategy](events)
    if strategy == "off":
        return events
    return default_gc(events)


# ── Ed25519 via cryptography library (with fallback) ──

try:
    from cryptography.hazmat.primitives.asymmetric import ed25519 as _ed
    from cryptography.exceptions import InvalidSignature as _InvSig

    def ed25519_generate_key(seed=None):
        if seed is None:
            key = _ed.Ed25519PrivateKey.generate()
        else:
            key = _ed.Ed25519PrivateKey.from_private_bytes(seed[:32])
        pub = key.public_key()
        return key.private_bytes_raw().hex(), pub.public_bytes_raw().hex()

    def ed25519_sign(message, seed_hex):
        key = _ed.Ed25519PrivateKey.from_private_bytes(bytes.fromhex(seed_hex)[:32])
        return key.sign(message).hex()

    def ed25519_verify(message, sig_hex, pub_hex):
        try:
            pub = _ed.Ed25519PublicKey.from_public_bytes(bytes.fromhex(pub_hex))
            pub.verify(bytes.fromhex(sig_hex), message)
            return True
        except _InvSig:
            return False

    _ED_CRYPTO = True
except ImportError:
    # Fallback: pure-Python Ed25519 (stdlib-only, RFC 8032). Produces the
    # same keys and signatures as the `cryptography` implementation above,
    # so identity files are interchangeable.
    _ED_CRYPTO = True
    _Q_ = 2 ** 255 - 19
    _L_ = 2 ** 252 + 27742317777372353535851937790883648493
    _D_ = (-121665 * pow(121666, _Q_ - 2, _Q_)) % _Q_
    _I_ = pow(2, (_Q_ - 1) // 4, _Q_)

    def _xrecover(y):
        xx = (y * y - 1) * pow(_D_ * y * y + 1, _Q_ - 2, _Q_) % _Q_
        x = pow(xx, (_Q_ + 3) // 8, _Q_)
        if (x * x - xx) % _Q_ != 0:
            x = (x * _I_) % _Q_
        if x % 2 != 0:
            x = _Q_ - x
        return x

    _BY_ = (4 * pow(5, _Q_ - 2, _Q_)) % _Q_
    _BX_ = _xrecover(_BY_)
    _B_ = (_BX_, _BY_, 1, (_BX_ * _BY_) % _Q_)

    def _point_add(P, Q):
        x1, y1, z1, t1 = P
        x2, y2, z2, t2 = Q
        A = (y1 - x1) * (y2 - x2) % _Q_
        B = (y1 + x1) * (y2 + x2) % _Q_
        C = 2 * t1 * t2 * _D_ % _Q_
        D = 2 * z1 * z2 % _Q_
        E = B - A
        F = D - C
        G = D + C
        H = B + A
        return (E * F % _Q_, G * H % _Q_, F * G % _Q_, E * H % _Q_)

    def _point_mul(P, e):
        if e == 0:
            return (0, 1, 1, 0)
        Q = _point_mul(P, e >> 1)
        Q = _point_add(Q, Q)
        if e & 1:
            Q = _point_add(Q, P)
        return Q

    def _point_encode(P):
        x, y, z, _t = P
        zi = pow(z, _Q_ - 2, _Q_)
        x = (x * zi) % _Q_
        y = (y * zi) % _Q_
        n = y | ((x & 1) << 255)
        return n.to_bytes(32, "little")

    def _point_decode(s):
        n = int.from_bytes(s, "little")
        y = n & ((1 << 255) - 1)
        x = _xrecover(y)
        if x & 1 != ((n >> 255) & 1):
            x = _Q_ - x
        return (x % _Q_, y % _Q_, 1, (x * y) % _Q_)

    def ed25519_generate_key(seed=None):
        if seed is None:
            seed = os.urandom(32)
        seed = seed[:32]
        h = hashlib.sha512(seed).digest()
        a = int.from_bytes(h[:32], "little")
        a &= (1 << 254) - 8
        a |= 1 << 254
        pub = _point_encode(_point_mul(_B_, a))
        return seed.hex(), pub.hex()

    def ed25519_sign(message, seed_hex):
        seed = bytes.fromhex(seed_hex)[:32]
        h = hashlib.sha512(seed).digest()
        a = int.from_bytes(h[:32], "little")
        a &= (1 << 254) - 8
        a |= 1 << 254
        r = int.from_bytes(hashlib.sha512(h[32:] + message).digest(), "little") % _L_
        R = _point_encode(_point_mul(_B_, r))
        A = _point_encode(_point_mul(_B_, a))
        k = int.from_bytes(hashlib.sha512(R + A + message).digest(), "little") % _L_
        s = (r + k * a) % _L_
        return (R + s.to_bytes(32, "little")).hex()

    def ed25519_verify(message, sig_hex, pub_hex):
        try:
            signature = bytes.fromhex(sig_hex)
            public = bytes.fromhex(pub_hex)
            if len(signature) != 64 or len(public) != 32:
                return False
            R = _point_decode(signature[:32])
            A = _point_decode(public)
            s = int.from_bytes(signature[32:], "little")
            if s >= _L_:
                return False
            k = int.from_bytes(hashlib.sha512(signature[:32] + public + message).digest(), "little") % _L_
            return _point_encode(_point_mul(_B_, s)) == _point_encode(_point_add(R, _point_mul(A, k)))
        except Exception:
            return False


# ── Identity Management ──────────────────────

IDENTITY_DIR = PROJECT_DIR / ".identity"
_IDENTITY = {}  # cached identity


def _identity_path():
    return IDENTITY_DIR / "identity.json"


def _secret_key_path():
    return IDENTITY_DIR / "secret.key"


def _gitignore_path():
    return IDENTITY_DIR / ".gitignore"


def identity_exists():
    """Check if user has set up their signing identity."""
    return _identity_path().exists() and _secret_key_path().exists()





def load_identity():
    """Load cached identity. Returns dict with name, social, public_key or None."""
    global _IDENTITY
    if _IDENTITY:
        return _IDENTITY
    if not identity_exists():
        return None
    try:
        with open(_identity_path(), "r") as f:
            _IDENTITY = json.load(f)
        return _IDENTITY
    except Exception:
        return None


def creatidentity(name, social=None):
    """Generate a new ed25519 keypair and save identity. Returns identity dict."""
    IDENTITY_DIR.mkdir(exist_ok=True)
    seed_hex, pub_hex = ed25519_generate_key()
    identity = {
        "name": name,
        "public_key": pub_hex,
        "social": social or {},
        "created": time.time(),
        "algorithm": "ED25519",
    }
    with open(_identity_path(), "w") as f:
        json.dump(identity, f, indent=2)
    with open(_secret_key_path(), "w") as f:
        f.write(seed_hex)
    with open(_gitignore_path(), "w") as f:
        f.write("secret.key\n")
    global _IDENTITY
    _IDENTITY = identity
    # refresh the hidden identity digest so the new identity verifies
    try:
        from ep_compiler.security_hash import reembed
        reembed()
    except Exception:
        pass
    return identity


def get_public_key(name_lookup=None):
    """Get the public key for a known identity. Case-insensitive.

    Resolves only local identities: the user's own keypair (None/"local") and
    any keys saved via savidentity_public_key into trusted/."""
    if name_lookup is None or str(name_lookup).lower() in ("local", "self"):
        id = load_identity()
        if id:
            return id.get("public_key")
    if name_lookup:
        lookup = str(name_lookup).lower()
        trust_dir = IDENTITY_DIR / "trusted"
        if trust_dir.exists():
            for f in sorted(trust_dir.glob("*.pub")):
                if f.stem.lower() == lookup:
                    try:
                        return f.read_text().strip()
                    except Exception:
                        return None
    return None


def savidentity_public_key(name, pub_hex):
    """Save a trusted public key (for trusting other signers)."""
    trust_dir = IDENTITY_DIR / "trusted"
    trust_dir.mkdir(exist_ok=True)
    with open(trust_dir / f"{name}.pub", "w") as f:
        f.write(pub_hex)
    _ok(f"Trusted key saved for {name}")


def list_trusted_keys():
    """Return dict of {name: pub_hex} for all trusted identities."""
    result = {}
    # Include user's own key
    id = load_identity()
    if id:
        result[id.get("name", "local")] = id.get("public_key", "")
    # Include trusted keys
    trust_dir = IDENTITY_DIR / "trusted"
    if trust_dir.exists():
        for f in sorted(trust_dir.glob("*.pub")):
            try:
                name = f.stem
                pub = f.read_text().strip()
                result[name] = pub
            except Exception:
                pass
    return result


# ── Session Management (persistent login) ──

_LOGIN_PATH = PROJECT_DIR / ".identity" / ".login"


def save_session(username, host="local"):
    """Save a login session. Local-only — never contacts a network service."""
    session = {"username": username, "host": host, "ip": "local", "time": time.time()}
    os.makedirs(os.path.dirname(str(_LOGIN_PATH)), exist_ok=True)
    with open(_LOGIN_PATH, "w") as f:
        json.dump(session, f)
    return session


def load_session():
    """Load saved session. Returns dict or None."""
    if not _LOGIN_PATH.exists():
        return None
    try:
        with open(_LOGIN_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return None


def clear_session():
    """Remove saved session (logout)."""
    if _LOGIN_PATH.exists():
        _LOGIN_PATH.unlink()
    return True


def check_session_ip():
    """Check saved session. Local-only — no IP phone-home.
    Returns (session, ip_changed, old_ip)."""
    session = load_session()
    if not session:
        return (None, False, "")
    return (session, False, session.get("ip", ""))


# ── Token Management (for authenticated operations) ──

_SESSION_TOKEN = None


def get_session_token():
    """Get current session token (validated at login time)."""
    return _SESSION_TOKEN


def set_session_token(token):
    global _SESSION_TOKEN
    _SESSION_TOKEN = token


# ── Trust Levels (used by verify_signature and plugins) ──

TRUST_REGAS = 2    # CORE-EXPANSION: REGAS — TENTARI confirmed via server check
TRUST_TENTARI = 2  # TENTARI-signed (third-party plugin devs, same trust level)
TRUST_UNKNOWN = 1  # Unknown signer
TRUST_UNSIGNED = 0 # No signature or invalid

# ── Strict Signing Enforcement ──
# 0 = off (load anything), 1 = warn (log unsigned/altered), 2 = block (reject unsigned/altered)
_STRICT_SIGNING = 0


def get_strict_signing():
    return _STRICT_SIGNING


def set_strict_signing(level):
    global _STRICT_SIGNING
    if level in (0, 1, 2):
        _STRICT_SIGNING = level
        return True
    return False

# ── Signing (ED25519) ─────────────────────────

def sign_file(path, author=None, social=None, embed=False):
    """Sign a file using the user's ed25519 key. Identity MUST be set up first."""
    if not identity_exists():
        _error("Cannot sign: no identity configured")
        _error("Run 'sign --setup' first to create your signing keypair")
        return None
    id = load_identity()
    with open(_secret_key_path(), "r") as f:
        secret_hex = f.read().strip()
    with open(path, "rb") as f:
        data = f.read()
    signature = ed25519_sign(data, secret_hex)
    algo = "ED25519"
    signer_name = id.get("name", author or "Unknown")
    signer_social = id.get("social", social or {})

    meta = {
        "_e_sig": {
            "algorithm": algo,
            "signature": signature,
            "timestamp": time.time(),
            "file": os.path.basename(path),
            "author": signer_name,
            "social": signer_social,
        }
    }

    if embed:
        meta["_e_sig"]["_embedded"] = True
        sig_block = json.dumps(meta).encode() + b"\n"
        first_line = data.split(b"\n", 1)[0]
        try:
            existing = json.loads(first_line.decode())
            if "_e_sig" in existing:
                rest = data.split(b"\n", 1)[1]
                data = rest
        except (json.JSONDecodeError, IndexError):
            pass
        with open(path, "wb") as f:
            f.write(sig_block + data)
        _ok(f"Signed (embedded) -> {os.path.basename(path)}")
    else:
        sig_path = path + ".sig"
        with open(sig_path, "w") as f:
            json.dump(meta["_e_sig"], f, indent=2)
        _ok(f"Signed -> {sig_path}")

    _print_copyright(meta["_e_sig"])
    return meta["_e_sig"]


def _hex_to_ansi(hex_color):
    if not hex_color or not hex_color.startswith("#"):
        return CYAN_
    try:
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        return f"\033[38;2;{r};{g};{b}m"
    except (ValueError, IndexError):
        return CYAN_


def _print_copyright(meta):
    sig = meta.get("signature", "?")[:12]
    author = meta.get("author", "Unknown")
    social = meta.get("social", {})
    print(f"  {CYAN_}©{R_} {YELLOW_}{author}{R_} [{GREY_}{sig}...{R_}]")
    for platform, handle in social.items():
        if "|" in str(handle):
            h, hex_c = str(handle).split("|", 1)
            ansi = _hex_to_ansi(hex_c.strip())
            print(f"    {platform}: {ansi}{h}{R_}")
        else:
            print(f"    {platform}: {CYAN_}{handle}{R_}")


# Add color constants fallback
try:
    from .config import (
        c,
        B,
        D,
        CYAN,
        YELLOW,
    )
except ImportError:
    R_ = "\033[0m"; B_ = "\033[1m"; D_ = "\033[2m"
    CYAN_ = "\033[96m"; YELLOW_ = "\033[93m"; GREY_ = "\033[90m"
    def c(t, color=""):
        return f"{color}{t}{R_}" if color else t


def verify_signature(path):
    """Verify a file's signature against known trusted keys.
    Returns (is_valid, trust_level, author, detail)."""
    sig_path = path + ".sig"
    meta = None
    if os.path.exists(sig_path):
        try:
            with open(sig_path, "r") as f:
                meta = json.load(f)
        except Exception:
            pass
    if not meta:
        try:
            with open(path, "rb") as f:
                first = f.readline()
            m = json.loads(first.decode())
            meta = m.get("_e_sig") or m
        except Exception:
            pass
    if not meta:
        return (False, TRUST_UNSIGNED, "unsigned", "No signature")

    signature = meta.get("signature", "")
    author = meta.get("author", "Unknown")
    algo = meta.get("algorithm", "SHA256-HASH")

    if algo == "ED25519":
        trusted = list_trusted_keys()
        pub = trusted.get(author)
        if not pub:
            return (False, TRUST_UNKNOWN, author, "Unknown signer")
        try:
            with open(path, "rb") as f:
                data = f.read()
            if meta.get("_embedded"):
                data = data.split(b"\n", 1)[1] if b"\n" in data else data
            if ed25519_verify(data, signature, pub):
                if author.upper() == "REGAS":
                    level = TRUST_REGAS
                elif author == "Tentari":
                    level = TRUST_TENTARI
                else:
                    level = TRUST_UNKNOWN
                return (True, level, author, f"Valid ED25519 signature")
            return (False, TRUST_UNSIGNED, author, "Signature mismatch")
        except Exception as e:
            return (False, TRUST_UNSIGNED, author, f"Verify error: {e}")

    # Legacy HMAC verification (fallback)
    if algo == "HMAC-SHA256":
        key = "e-lang-signature-key"
        try:
            with open(path, "rb") as f:
                data = f.read()
            computed = hmac.new(key.encode(), data, hashlib.sha256).hexdigest()
            if computed == signature:
                return (True, TRUST_UNKNOWN, author, "Legacy HMAC signature")
            return (False, TRUST_UNSIGNED, author, "HMAC mismatch")
        except Exception as e:
            return (False, TRUST_UNSIGNED, author, f"HMAC error: {e}")

    return (False, TRUST_UNSIGNED, author, f"Unknown algorithm: {algo}")


def embed_signature(data: bytes) -> bytes:
    """Embed signature into file bytes (for .ec, .ee formats)."""
    id = load_identity()
    if id:
        try:
            with open(_secret_key_path(), "r") as f:
                secret_hex = f.read().strip()
            sig = ed25519_sign(data, secret_hex)
            algo = "ED25519"
        except Exception:
            sig = hashlib.sha256(data).hexdigest()
            algo = "SHA256-HASH"
    else:
        sig = hashlib.sha256(data).hexdigest()
        algo = "SHA256-HASH"
    sig_block = json.dumps({
        "_sig": sig, "_algo": algo, "_ts": time.time(),
    }).encode() + b"\n"
    return sig_block + data


def verify_embedded(data: bytes) -> tuple:
    """Verify embedded signature. Handles both _sig and _e_sig formats."""
    try:
        first_line, rest = data.split(b"\n", 1)
        meta = json.loads(first_line.decode())

        # Handle _e_sig format (from sign_file embed)
        if "_e_sig" in meta:
            sig_data = meta["_e_sig"]
            expected = sig_data.get("signature", "")
            algo = sig_data.get("algorithm", "SHA256-HASH")
            author = sig_data.get("author", "")
            if algo == "ED25519":
                # Look up author's public key
                pub_key = list_trusted_keys().get(author, "")
                if not pub_key:
                    return False, f"Unknown signer: {author}"
                if ed25519_verify(rest, expected, pub_key):
                    return True, f"Valid ED25519 ({author})"
                return False, "Signature mismatch"
            else:
                computed = hashlib.sha256(rest).hexdigest()
                if computed == expected:
                    return True, "Valid hash"
                return False, "Hash mismatch"

        # Handle _sig format (from embed_signature)
        if "_sig" not in meta:
            return False, "No embedded signature"
        expected = meta["_sig"]
        algo = meta.get("_algo", "SHA256-HASH")
        if algo == "ED25519":
            id = load_identity()
            if not id:
                return False, "No identity configured"
            pub = id.get("public_key", "")
            if ed25519_verify(rest, expected, pub):
                return True, "Valid ED25519"
            return False, "Signature mismatch"
        else:
            computed = hashlib.sha256(rest).hexdigest()
            if computed == expected:
                return True, "Valid hash"
            return False, "Hash mismatch"
    except (ValueError, json.JSONDecodeError):
        return False, "No signature data"


# ── Multi-file .ee bundling ──────────────────

def bundle_to_ee(source_path, output_path, method="base", key=None, sign=False):
    """Bundle .ei project (index + all parts) into a single .ee file."""
    import ep as _ep  # lazy import to avoid circular

    source_path = os.path.abspath(source_path)
    base_dir = os.path.dirname(source_path)

    if source_path.endswith(".ei"):
        # Read index
        with open(source_path, "r", encoding="utf-8") as f:
            index = f.read()

        parts = {}
        for m in re.finditer(r'include\s+"([^"]+)"', index, re.I):
            rel = m.group(1)
            full = os.path.normpath(os.path.join(base_dir, rel))
            if os.path.exists(full):
                with open(full, "r", encoding="utf-8") as pf:
                    parts[rel] = pf.read()

        # Bundle everything
        bundle = json.dumps({
            "type": "ee-bundle",
            "version": "2.0",
            "index": index,
            "parts": parts,
        }, indent=2).encode()

        if sign:
            bundle = embed_signature(bundle, key)

        # Encrypt the bundle
        enc = _encryptors.get(method)
        if not enc:
            raise ValueError(f"Unknown encryption: {method}")
        encrypted = enc[0](bundle, key or "e-lang-default")

        header = json.dumps({
            "method": method,
            "type": "ee-bundle",
            "signed": sign,
        }).encode() + b"\n"

        with open(output_path, "wb") as f:
            f.write(header + encrypted)

        n_parts = len(parts)
        print(f"  > Bundled to .ee: {output_path} ({n_parts} parts, {method}{', signed' if sign else ''})")
        return True
    else:
        # Single file .ee
        return encrypt_e(source_path, output_path, method, key)


def unbundle_ee(path, key=None):
    """Decrypt a .ee bundle and return (index_text, {part_name: text})."""
    try:
        raw = decrypt_ee(path, key)
    except Exception:
        with open(path, "rb") as f:
            raw = f.read()
        # Try to find header
        try:
            first_line, raw = raw.split(b"\n", 1)
            header = json.loads(first_line.decode())
            if header.get("type") != "ee-bundle":
                raw = open(path, "rb").read()
            else:
                raw = decrypt_ee(path, key)
        except Exception:
            raw = decrypt_ee(path, key)

    # Check for embedded signature
    verified, sig_msg = verify_embedded(raw, key)
    if verified:
        print(f"  > {sig_msg}")

    # Parse bundle
    try:
        bundle = json.loads(raw)
    except json.JSONDecodeError:
        # Might be signed — strip signature and try again
        try:
            first_line, rest = raw.split(b"\n", 1)
            bundle = json.loads(rest.decode())
        except Exception:
            raise ValueError("Not a valid .ee bundle")

    if bundle.get("type") != "ee-bundle":
        raise ValueError("Not a bundle .ee file (use single-file encryption instead)")

    return bundle.get("index", ""), bundle.get("parts", {})


# ── Variable System ──────────────────────────

class VariableScope:
    """Manages variable definitions and resolution."""

    def __init__(self):
        self.vars = {}  # name -> raw text content
        self.imports = {}  # prefix -> file path

    def define(self, name, content):
        self.vars[name] = content

    def get(self, name):
        if name in self.vars:
            return self.vars[name]
        for handler in _variable_handlers:
            result = handler(name)
            if result:
                return result
        return None

    def resolve(self, text):
        """Replace $variable references in text with their values."""
        def repl(m):
            name = m.group(1) or m.group(2)
            val = self.get(name)
            if val is not None:
                return val
            return m.group(0)  # leave unresolved

        # $name or ${name} or $name.attribute
        text = re.sub(r'\$\{([^}]+)\}|\$([a-zA-Z_]\w*)', repl, text)
        return text

    def parse_definition(self, line):
        """Parse '$name = { ... }' definitions."""
        m = re.match(r'^\$([a-zA-Z_]\w*)\s*=\s*\{(.*)\}\s*$', line, re.DOTALL)
        if m:
            self.define(m.group(1), m.group(2).strip())
            return True
        return False


# ── Portable Paths ───────────────────────────

def resolve_e_path(path):
    """Resolve a .e/.ei/.ee path relative to PROJECT_DIR if not absolute."""
    p = Path(path)
    if p.is_absolute():
        return str(p)
    # Try relative to CWD first, then PROJECT_DIR
    if p.exists():
        return str(p)
    alt = PROJECT_DIR / str(p)
    if alt.exists():
        return str(alt)
    return str(p)


# ── Embedded Plugin Restore (Tentari-signed only) ──

EMBEDDED_DIR = PROJECT_DIR / "embedded_plugins"


def _load_embedded_json(name):
    """Load a plugin's JSON backup from embedded_plugins/<name>.json."""
    json_path = EMBEDDED_DIR / f"{name}.json"
    if not json_path.exists():
        return None
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _list_embedded_jsons():
    """Yield (name, data) for all embedded plugin JSONs."""
    if not EMBEDDED_DIR.exists():
        return
    for f in sorted(EMBEDDED_DIR.glob("*.json")):
        name = f.stem
        data = _load_embedded_json(name)
        if data:
            yield name, data


def is_plugin_missing(name):
    """Check if a bundled plugin's directory is missing or empty."""
    pdir = PLUGINS_DIR / name
    if not pdir.exists() or not pdir.is_dir():
        return True
    py_files = list(pdir.glob("*.py"))
    if not py_files:
        return True
    return False


def _real_progress(pct, label, detail=""):
    """Print a real progress bar tracking actual byte/file progress."""
    import sys
    bar_width = 24
    filled = int(pct * bar_width // 100)
    bar = "█" * filled + "░" * (bar_width - filled)
    display = label
    if detail:
        display += f"  {detail}"
    print(f"\r  \033[93m⟳\033[0m [{bar}] {pct:3d}%  \033[96m{display}\033[0m  ", end="")
    sys.stdout.flush()


def restore_plugin(name, target_dir=None):
    """Restore a Tentari-signed plugin from embedded_plugins/<name>.json.
    Returns list of written files, or None on failure."""
    if target_dir is None:
        target_dir = PLUGINS_DIR
    target_dir = Path(target_dir) if not isinstance(target_dir, Path) else target_dir
    payload = _load_embedded_json(name)
    if not payload:
        _error(f"No embedded backup for: {name}")
        return None
    written = []
    try:
        entries = payload.get("files", [])
        total = payload.get("total_size", 0)
        decoded_bytes = 0
        for idx, entry in enumerate(entries):
            rel = entry["path"]
            data = base64.b64decode(entry["data"])
            actual = hashlib.sha256(data).hexdigest()
            expected = entry.get("sha256", "")
            if expected and actual != expected:
                _error(f"Integrity fail: {name}/{rel}")
                return None
            dst = target_dir / name / rel
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(data)
            written.append(str(dst))
            decoded_bytes += len(data)
            pct = int(decoded_bytes * 100 / total) if total else 100
            _real_progress(pct, "extracting", f"{idx+1}/{len(entries)} files")
        _real_progress(100, "finalizing")
        print(f"\r  \033[92m✓\033[0m restored {name}: {len(written)} files ({total/1024:.0f} KB)  ")
        return written
    except Exception as e:
        print(f"\n  \033[91m✗\033[0m Restore failed for {name}: {e}")
        return None


def restore_all(target_dir=None):
    """Restore all Tentari-signed plugins that are missing."""
    if target_dir is None:
        target_dir = PLUGINS_DIR
    target_dir = Path(target_dir) if not isinstance(target_dir, Path) else target_dir
    restored = 0
    for name, payload in _list_embedded_jsons():
        count = payload.get("file_count", 0)
        if is_plugin_missing(name):
            r = restore_plugin(name, target_dir)
            if r:
                restored += 1
        else:
            real = sum(1 for f in (target_dir / name).rglob("*")
                       if f.is_file() and "__pycache__" not in f.parts)
            _ok(f"Plugin {name} present ({real} files)")
    if restored == 0:
        _ok("All bundled plugins present")
    return restored


def embed_info(name=None):
    """Show info about Tentari-signed embedded plugins."""
    if name:
        payload = _load_embedded_json(name)
        if payload:
            _ok(f"{payload['name']} v{payload.get('version', '?')}: {payload['file_count']} files, {payload['total_size']/1024:.0f} KB")
            for entry in payload.get("files", []):
                print(f"    {entry['path']} ({entry['size']} bytes)")
        else:
            _error(f"No embedded backup for: {name}")
    else:
        for n, p in _list_embedded_jsons():
            status = _ok if not is_plugin_missing(n) else _warn
            status(f"{n} v{p.get('version', '?')}: {p['file_count']} files, {p['total_size']/1024:.0f} KB {'(missing — plugin install to restore)' if is_plugin_missing(n) else '(present)'}")


# ── Init ─────────────────────────────────────

def init():
    """Initialize core system: load plugins, mods, encryptors."""
    # Load custom encryptors from encryption/
    _enc_names = []
    if ENCRYPTION_DIR.exists():
        sys.path.insert(0, str(ENCRYPTION_DIR))
        for f in sorted(ENCRYPTION_DIR.glob("*.py")):
            if f.name.startswith("_"):
                continue
            try:
                mod = _load_module(f, f"encryption.{f.stem}", security_scan=False)
                if mod and hasattr(mod, "register_encryptor"):
                    mod.register_encryptor(_register_encryptor)
                    _enc_names.append(f.stem)
            except Exception as e:
                print(f"  > Encryption error {f.name}: {e}")
    if _enc_names:
        print(f"  \033[90m[encryption] {len(_enc_names)} module(s): "
              f"{', '.join(_enc_names)}\033[0m")

    load_plugins()
    load_mods()
    _boot_steps.append(("Finalizing", "done"))


def show_boot_progress():
    """Display a progress bar showing boot initialization steps.
    Each step represents loading a plugin or mod. Returns when done."""
    import sys
    import time
    if not _boot_steps:
        return
    total = len(_boot_steps)
    cols = min(50, shutil.get_terminal_size((80, 20)).columns - 20)
    bar_width = max(10, cols)
    print("")  # spacing
    for idx, (label, status) in enumerate(_boot_steps):
        pct = (idx + 1) * 100 // total
        filled = pct * bar_width // 100
        bar = "█" * filled + "░" * (bar_width - filled)
        # Truncate label if too long
        display_label = label[:40] + "..." if len(label) > 40 else label
        print(f"\r  \033[36mBoot\033[0m [{bar}] {pct:3d}%  \033[90m{display_label}\033[0m", end="")
        sys.stdout.flush()
        time.sleep(0.05)  # small delay so the bar is visible
    print(f"\r  \033[36mBoot\033[0m [{'█' * bar_width}] 100%  \033[32mReady\033[0m{' ' * 20}")
    print("")


# Need shutil for terminal size in boot progress
import shutil
