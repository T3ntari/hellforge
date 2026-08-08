"""Humanize v1.0.0 - de-robot MIDI with a tiny numpy MoE (~50k params).

The @humanize:nn directive adds human micro-timing and expressive
velocity to compiled songs:
    @humanize:15        strength 0-100 (default 15)
    @humanize           same as @humanize:15
    @humanize:0 / off   disable

Per-note context (pitch, velocity, bar position, local density, previous
offset/delta) is fed to an 8-expert Mixture-of-Experts model that predicts
timing jitter + velocity deltas. Trained once on a synthetic human-
performance regression task, cached to .fent_cache, instant CPU inference.

Hooks: pre_compile (scans @humanize directive), post_compile (applies
humanization to the rendered events)."""

import os
import re

VERSION = "1.0.0"
author = "REGAS"
description = "MoE humanization - de-robots MIDI with micro-timing + velocity expression"

DIRECTIVE_RE = re.compile(r"@humanize\s*(?::\s*(\d{1,3})|\s+(\d{1,3})|\s+off)?", re.I)

_strength = 0.0
_api = None


def register(api):
    global _api
    _api = api
    api.add_boot_step(f"Humanize v{VERSION}", "loading")

    def _pre_compile(text):
        """Scan source for @humanize:nn and stash the strength.
        Comments are stripped first — doc comments mentioning @humanize
        must never set the strength."""
        global _strength
        try:
            from ep_compiler.comments import strip_comments
            code = strip_comments(text)
        except Exception:
            code = text
        m = None
        for _m in DIRECTIVE_RE.finditer(code):
            m = _m  # last occurrence wins — doc text mentions come first
        if not m:
            _strength = 0.0
            return None
        if m.group(1) is not None:
            _strength = max(0.0, min(100.0, float(m.group(1))))
        elif m.group(2) is not None:
            _strength = max(0.0, min(100.0, float(m.group(2))))
        elif m.group(3) is not None:
            _strength = 0.0  # @humanize off
        else:
            _strength = 15.0  # bare @humanize
        return None

    def _post_compile(events, bp):
        """Apply humanization when @humanize was active."""
        global _strength
        if _strength <= 0 or not events:
            return None
        try:
            from .humanizer import apply_humanize
            return apply_humanize(events, bpm=bp, strength=_strength)
        except Exception as e:
            print(f"  > humanize: apply failed ({e})")
            return None

    api.on("pre_compile", _pre_compile)
    api.on("post_compile", _post_compile)

    def _cmd(args):
        return _command(args)

    api.add_command("humanize", _cmd, "Humanize: humanize status|apply <file> [strength]|retrain|info")
    api.set_config("humanize_available", True)
    api.add_boot_step(f"Humanize: MoE ready ({_model_summary()})", "done")


def _model_summary():
    try:
        from . import moe
        return f"{moe.N_EXPERTS} experts, ~{moe.param_count(moe.init_params()) // 1000}k params"
    except Exception:
        return "experts"


def get_api():
    return _api


def _command(args):
    from . import moe
    if not args or args[0] in ("status", "info"):
        p, dt = moe.load_or_train()
        path = moe.cache_path()
        cached = os.path.exists(path)
        print(f"  Humanize v{VERSION} — MoE de-robotizer")
        print(f"    experts      : {moe.N_EXPERTS}")
        print(f"    params       : {moe.param_count(p):,}")
        print(f"    weights      : {path} ({'cached' if cached else 'not cached yet'})")
        print(f"    last train   : {dt:.1f}s")
        print(f"    directive    : @humanize:nn (0-100, default {moe.DEFAULT_STRENGTH})")
        return 0
    if args[0] == "retrain":
        p, dt = moe.train(progress=lambda e, t: print(f"    epoch {e}/{t}", end="\r"))
        try:
            import numpy as np
            os.makedirs(os.path.dirname(moe.cache_path()), exist_ok=True)
            np.savez(moe.cache_path(), **p)
        except Exception as e:
            print(f"  ! cache write failed: {e}")
        print(f"\n  Retrained: {moe.param_count(p):,} params in {dt:.1f}s")
        return 0
    if args[0] == "apply" and len(args) >= 2:
        path = args[1].strip("\"'")
        strength = float(args[2]) if len(args) > 2 else moe.DEFAULT_STRENGTH
        try:
            from ep_compiler.compile import compile_source
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
            events, bp = compile_source(text)
            from .humanizer import apply_humanize
            human = apply_humanize(events, bpm=bp, strength=strength)
            out = os.path.splitext(path)[0] + "_humanized.e"
            # re-emit as v4 machine source so the result is usable directly
            try:
                from plugins.portbaby.v1_to_v4 import convert
                with open(out, "w", encoding="utf-8") as f:
                    f.write(convert(human, bp))
            except Exception:
                out = path
            print(f"  ✓ humanized {len(events)} notes @{strength:.0f} → {out}")
            return 0
        except Exception as e:
            print(f"  ✗ humanize apply: {e}")
            return 1
    print("  Usage: humanize status | retrain | apply <file> [strength]")
    return 1
