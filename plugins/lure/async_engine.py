"""Async LURE — per-thread LuaJIT runtimes for GIL-free parallel compilation.

Each thread gets its own LuaRuntime instance (thread-safe, per lupa docs).
lupa releases Python's GIL during Lua execution, so N threads can
evaluate math ASTs or parse lines simultaneously across CPU cores."""

import asyncio
import concurrent.futures
import threading
import os


class AsyncLUREngine:
    """Async wrapper around LUREngine. Creates per-thread LuaRuntimes.
    Falls back to synchronous if LURE is unavailable."""

    def __init__(self, max_workers=None):
        import multiprocessing
        self._max_workers = max_workers or min(32, (multiprocessing.cpu_count() or 4) * 2)
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix="lure_async"
        )
        self._lock = threading.Lock()
        self._local = threading.local()
        self._available = False
        self._diagnostic = ""
        self._init_check()

    def _init_check(self):
        """Check if LURE is available by trying to create one instance."""
        try:
            from .lua_engine import LUREngine
            eng = LUREngine()
            self._available = eng.available
            self._diagnostic = eng._diagnostic if not eng.available else "ready"
        except Exception as e:
            self._available = False
            self._diagnostic = str(e)

    @property
    def available(self):
        return self._available

    def _get_engine(self):
        """Get or create a per-thread LUREngine."""
        if not hasattr(self._local, 'engine'):
            from .lua_engine import LUREngine
            self._local.engine = LUREngine()
        return self._local.engine

    async def eval_ast(self, ast_dict, variables):
        """Async math AST evaluation via LURE.
        Returns number or None."""
        if not self._available:
            return None
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._sync_eval_ast, ast_dict, variables
        )

    def _sync_eval_ast(self, ast_dict, variables):
        with self._lock:
            try:
                eng = self._get_engine()
                return eng.eval_ast(ast_dict, variables)
            except Exception:
                return None

    async def parse_lines_batch(self, lines):
        """Async batch line parsing via LURE.
        Returns list of event dicts or Nones."""
        if not self._available or not lines:
            return [None] * len(lines)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._sync_parse_batch, lines
        )

    def _sync_parse_batch(self, lines):
        with self._lock:
            try:
                eng = self._get_engine()
                return eng.parse_lines_batch(lines)
            except Exception:
                return [None] * len(lines)

    async def quantize(self, events, scale_name):
        """Async scale quantization via LURE."""
        if not self._available or not events:
            return None
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._sync_quantize, events, scale_name
        )

    def _sync_quantize(self, events, scale_name):
        with self._lock:
            try:
                eng = self._get_engine()
                return eng.quantize(events, scale_name)
            except Exception:
                return None

    async def validate_and_sort(self, events):
        """Async event validation via LURE."""
        if not self._available or not events:
            return None, 0
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._sync_validate, events
        )

    def _sync_validate(self, events):
        with self._lock:
            try:
                eng = self._get_engine()
                return eng.validate_and_sort(events)
            except Exception:
                return None, 0

    async def compile_source(self, text, bpm=None):
        """Async full compilation via LURE fast path (single batch parse)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, self._sync_compile, text, bpm
        )

    def _sync_compile(self, text, bpm=None):
        """Synchronous compile — tries LURE fast path, falls back to Python."""
        from ep_compiler.compile import compile_source
        return compile_source(text, bpm)

    async def shutdown(self):
        """Clean up thread pool."""
        self._executor.shutdown(wait=True)

    def summary(self):
        return {
            "available": self._available,
            "diagnostic": self._diagnostic,
            "max_workers": self._max_workers,
            "thread_pool": "active",
        }
