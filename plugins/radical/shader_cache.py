"""Shader Cache — LRU cache of compiled GLSL shader programs.
Persisted to disk via JSON (program IDs are not persisted across sessions,
but source hashes are kept for stats)."""

import os
import json
import hashlib
import time

CACHE_DIR = None
_cache = {}  # hash -> program_id (in-memory, per session)
_metadata = {}  # hash -> {source_preview, compile_time, count}


def _get_cache_dir():
    global CACHE_DIR
    if CACHE_DIR is None:
        from ep_core import IDENTITY_DIR
        CACHE_DIR = IDENTITY_DIR / ".radical_cache"
    return CACHE_DIR


def _meta_path():
    d = _get_cache_dir()
    return os.path.join(str(d), "shader_meta.json")


def _load_metadata():
    global _metadata
    if _metadata:
        return
    try:
        p = _meta_path()
        if os.path.exists(p):
            with open(p) as f:
                _metadata = json.load(f)
    except Exception:
        _metadata = {}


def _save_metadata():
    try:
        p = _meta_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump(_metadata, f, indent=2)
    except Exception:
        pass


def get_cached_shader(source_hash):
    """Get compiled program ID from cache. Returns program_id or None."""
    return _cache.get(source_hash)


def cache_shader(source_hash, program_id, source_preview=""):
    """Store compiled shader in cache."""
    _cache[source_hash] = program_id
    _load_metadata()
    if source_hash not in _metadata:
        _metadata[source_hash] = {
            "source_preview": source_preview[:80],
            "compile_time": time.time(),
            "count": 0,
        }
    _metadata[source_hash]["count"] = _metadata[source_hash].get("count", 0) + 1
    _save_metadata()


def get_cache_stats():
    """Get cache statistics."""
    _load_metadata()
    return {
        "count": len(_cache),
        "meta_count": len(_metadata),
        "size_kb": sum(len(json.dumps(v)) for v in _metadata.values()) // 1024,
    }


def list_shaders():
    """List cached shaders."""
    _load_metadata()
    entries = []
    for h, meta in sorted(_metadata.items(), key=lambda x: -x[1].get("count", 0)):
        entries.append({
            "hash": h,
            "source_preview": meta.get("source_preview", ""),
            "count": meta.get("count", 0),
            "compile_time": meta.get("compile_time", 0),
        })
    return entries


def clear_cache():
    """Clear shader cache."""
    global _cache, _metadata
    _cache = {}
    _metadata = {}
    try:
        p = _meta_path()
        if os.path.exists(p):
            os.remove(p)
    except Exception:
        pass
