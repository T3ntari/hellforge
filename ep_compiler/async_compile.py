"""Async Compilation Pipeline — non-blocking compile with fallback chain.

Chain: LURE async > Python async > synchronous fallback.
Allows concurrent compilation of multiple files and keeps the REPL responsive."""

import asyncio
import concurrent.futures
import multiprocessing
import time


# ── Engine Singleton ──

_async_lure = None
_async_fc = None
_default_executor = None


def _get_executor():
    global _default_executor
    if _default_executor is None:
        cpus = multiprocessing.cpu_count() or 4
        _default_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=min(32, cpus * 2),
            thread_name_prefix="e_async"
        )
    return _default_executor


def set_thread_pool_size(n):
    """Resize the default async thread pool for real.
    Existing executor is shut down and replaced with the new size."""
    global _default_executor
    n = max(1, int(n))
    old = _default_executor
    _default_executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=n, thread_name_prefix="e_async"
    )
    if old is not None:
        try:
            old.shutdown(wait=False)
        except Exception:
            pass
    return n


def _get_lure_async():
    global _async_lure
    if _async_lure is None:
        try:
            from plugins.lure.async_engine import AsyncLUREngine
            _async_lure = AsyncLUREngine()
        except Exception:
            _async_lure = None
    return _async_lure


def _get_fc_async():
    global _async_fc
    if _async_fc is None:
        try:
            from plugins.fentclient.async_engine import AsyncCompilePool
            _async_fc = AsyncCompilePool()
        except Exception:
            _async_fc = None
    return _async_fc


def get_fc_async():
    return _get_fc_async()


# ── Async Compile Functions ──


async def async_compile_source(text, bpm=None, executor=None):
    """Compile source text asynchronously.
    Tries LURE async first, then Python async, then falls back to synchronous.
    Returns (events, bpm)."""
    loop = asyncio.get_event_loop()
    ex = executor or _get_executor()

    # Fast path: if LURE async is available, use it
    lure = _get_lure_async()
    if lure and lure.available:
        try:
            result = await lure.compile_source(text, bpm)
            if result and result[0]:
                return result
        except Exception:
            pass

    # Fallback: use Python async engine
    fc = _get_fc_async()
    if fc and fc.available:
        try:
            return await fc.compile_source(text, bpm)
        except Exception:
            pass

    # Last resort: synchronous in executor
    from ep_compiler.compile import compile_source
    return await loop.run_in_executor(ex, compile_source, text, bpm)


async def async_compile_batch(sources, bpm=None):
    """Compile multiple sources in parallel.
    Returns list of (events, bpm) tuples."""
    loop = asyncio.get_event_loop()
    lure = _get_lure_async()
    fc = _get_fc_async()

    # LURE batch path
    if lure and lure.available:
        try:
            results = []
            for src in sources:
                result = await lure.compile_source(src, bpm)
                results.append(result)
            return results
        except Exception:
            pass

    # FC async path
    if fc and fc.available:
        try:
            return await fc.compile_batch(sources, bpm)
        except Exception:
            pass

    # Synchronous fallback
    from ep_compiler.compile import compile_source
    tasks = [loop.run_in_executor(None, compile_source, src, bpm) for src in sources]
    return await asyncio.gather(*tasks)


async def async_eval_math(expr_str, variables=None):
    """Evaluate a math expression asynchronously.
    Returns (result, error) tuple matching evaluate_expression()."""
    from ep_compiler.math_engine import (
        build_ast,
        ast_to_dict,
    )
    from ep_compiler.variables import evaluate_expression

    ast, err = build_ast(expr_str)
    if err:
        return None, err
    if ast is None:
        return None, "Empty expression"

    ast_dict = ast_to_dict(ast)
    vars_dict = variables or {}

    # Try LURE async first
    lure = _get_lure_async()
    if lure and lure.available:
        try:
            result = await lure.eval_ast(ast_dict, vars_dict)
            if result is not None:
                return result, None
        except Exception:
            pass

    # Try FC async
    fc = _get_fc_async()
    if fc and fc.available:
        try:
            result = await fc.eval_ast(ast_dict, vars_dict)
            if result is not None:
                return result, None
        except Exception:
            pass

    # Synchronous fallback
    return evaluate_expression(expr_str, None)


async def async_eval_math_batch(expr_strs, variables_list=None):
    """Evaluate multiple math expressions in parallel.
    Returns list of (result, error) tuples."""
    from ep_compiler.math_engine import (
        build_ast,
        ast_to_dict,
    )
    from ep_compiler.variables import evaluate_expression

    # Build ASTs first (fast, no I/O)
    asts = []
    for i, expr in enumerate(expr_strs):
        ast, err = build_ast(expr)
        if err:
            asts.append(None)
        elif ast is None:
            asts.append(None)
        else:
            ast_dict = ast_to_dict(ast)
            vars_dict = variables_list[i] if variables_list and i < len(variables_list) else {}
            asts.append((ast_dict, vars_dict))

    lure = _get_lure_async()
    fc = _get_fc_async()

    # Try LURE async in parallel
    if lure and lure.available:
        try:
            tasks = []
            for a in asts:
                if a is None:
                    tasks.append(asyncio.sleep(0, result=None))
                else:
                    ad, vd = a
                    tasks.append(lure.eval_ast(ad, vd))
            results = await asyncio.gather(*tasks)
            return [(r, None) if r is not None else (None, "eval failed") for r in results]
        except Exception:
            pass

    # Try Python async in parallel
    if fc and fc.available:
        try:
            tasks = []
            for a in asts:
                if a is None:
                    tasks.append(asyncio.sleep(0, result=None))
                else:
                    ad, vd = a
                    tasks.append(fc.eval_ast(ad, vd))
            results = await asyncio.gather(*tasks)
            return [(r, None) if r is not None else (None, "eval failed") for r in results]
        except Exception:
            pass

    # Fallback: synchronous in executor
    loop = asyncio.get_event_loop()
    tasks = []
    for i, expr in enumerate(expr_strs):
        vd = variables_list[i] if variables_list and i < len(variables_list) else None
        tasks.append(loop.run_in_executor(None, evaluate_expression, expr, vd))
    return await asyncio.gather(*tasks)


async def async_compile_file(path, bpm=None):
    """Compile a file asynchronously. Returns (events, bpm)."""
    loop = asyncio.get_event_loop()
    from ep_compiler.compile import compile_file
    return await loop.run_in_executor(None, compile_file, path, bpm)


# ── Pool for long-running compilation ──

class AsyncCompilePool:
    """Manage a pool of async compile workers.
    Each worker can compile files independently."""

    def __init__(self, max_workers=None):
        cpus = multiprocessing.cpu_count() or 4
        self._max = max_workers or cpus
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max,
            thread_name_prefix="e_pool"
        )
        self._jobs = {}

    async def compile_file(self, path, bpm=None):
        """Compile a file asynchronously in the pool."""
        loop = asyncio.get_event_loop()
        from ep_compiler.compile import compile_file
        return await loop.run_in_executor(self._executor, compile_file, path, bpm)

    async def compile_text(self, text, bpm=None):
        """Compile source text asynchronously in the pool."""
        loop = asyncio.get_event_loop()
        return await async_compile_source(text, bpm, executor=self._executor)

    def shutdown(self):
        self._executor.shutdown(wait=True)


# ── Convenience ──

def get_async_engines():
    """Return status of all async engines."""
    lure = _get_lure_async()
    fc = _get_fc_async()
    return {
        "lure_async": lure.summary() if lure else {"available": False, "diagnostic": "not loaded"},
        "python_async": fc.summary() if fc else {"available": False},
    }
