"""Codebase search for the copilot — a true inverted token index (not just
symbols): identifiers, snake_case words, @directives and per-line text per
file, persisted to .fent_cache/llm_search_index.json with mtime-based
staleness so fresh caches are reused and stale ones rebuilt.

Feeds the SEARCH tool the model can invoke:

  search()          — ranked {path, line, text} hits for a text query
  search_snippet()  — line windows around hits (context feeding)
  similar()         — the `~` operator: char-2-gram Jaccard vs file heads
  run_query()       — dispatch `~x` / plain query, format for the model

File walking and skip rules reuse the symbol indexer (indexer.py)."""

import json
import math
import os
import re
import time
from pathlib import Path

from .indexer import SKIP_DIRS, SKIP_EXT

SEARCH_INDEX = "llm_search_index.json"

_IDENT_RE = re.compile(r"[A-Za-z_]\w*")
_DIRECTIVE_RE = re.compile(r"@\w+")
_WORD_RE = re.compile(r"[a-z][a-z0-9]*")

# Size guards: beyond these the index stays correct, just truncated.
MAX_LINES_PER_FILE = 3000  # deeper matches are not indexed
MAX_LINE_CHARS = 200      # per stored line
TEXT_CHARS = 120          # per displayed hit line

# Ranking weights: @directives (symbols) > identifier names > plain words.
WEIGHTS = {"directive": 8.0, "ident": 4.0, "word": 1.0}
PHRASE_BONUS = 10.0   # the query phrase appears inside a line (strong)
WORDS_BONUS = 3.0     # at least two query words inside one line

# Char-2-gram memo per loaded index dict (invalidated on each fresh build).
_BIGRAM_MEMO = {}


# ── tokenization ──

def document_tokens(text):
    """Tokenize file text into {'directive'|'ident'|'word': {token: count}}."""
    tokens = {"directive": {}, "ident": {}, "word": {}}
    for m in _DIRECTIVE_RE.finditer(text):
        t = m.group(0).lower()
        tokens["directive"][t] = tokens["directive"].get(t, 0) + 1
    for m in _IDENT_RE.finditer(text):
        t = m.group(0)
        tl = t.lower()
        tokens["ident"][tl] = tokens["ident"].get(tl, 0) + 1
        for w in _WORD_RE.findall(t):
            wl = w.lower()
            tokens["word"][wl] = tokens["word"].get(wl, 0) + 1
    return tokens


def query_units(query):
    """Tokenize a query into [(kind, unit)] matching document_tokens
    (directive before ident, so `@curve` is one unit, not `curve`)."""
    units = []
    for m in _DIRECTIVE_RE.finditer(query):
        units.append(("directive", m.group(0).lower()))
    for m in _IDENT_RE.finditer(query):
        t = m.group(0)
        tl = t.lower()
        if tl.startswith("@"):
            continue
        units.append(("ident", tl))
        for w in _WORD_RE.findall(t):
            units.append(("word", w.lower()))
    return units


def _phrase_key(text):
    """Alnum-only lowercased shape — punctuation and spacing don't break
    phrase matching (so `velocity curve` matches `curve velocity`)."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _bigrams(text):
    """Character 2-gram set over an alnum-only lowercase stream."""
    s = re.sub(r"[^a-z0-9]", "", text.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


# ── file walking (same skip rules as the symbol indexer) ──

def _walk_file_mtimes(project_dir):
    """Yield (relpath, mtime) for every indexable file under project_dir."""
    root = Path(project_dir).resolve()
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.suffix.lower() in SKIP_EXT or p.name.startswith("."):
            continue
        try:
            yield str(rel).replace(os.sep, "/"), p.stat().st_mtime
        except OSError:
            continue


# ── index build / load / staleness ──

def build_search_index(project_dir):
    """Walk project_dir and build the inverted index:
    {path: {tokens: {...counts...}, lines: [line_text, ...], mtime, size}}.
    Persisted to .fent_cache/llm_search_index.json; returns the dict."""
    root = Path(project_dir).resolve()
    files = {}
    for rel, mtime in _walk_file_mtimes(root):
        try:
            full = root / rel
            text = full.read_text(encoding="utf-8", errors="replace")
            size = full.stat().st_size
        except Exception:
            continue
        lines = text.splitlines()[:MAX_LINES_PER_FILE]
        lines = [ln.strip()[:MAX_LINE_CHARS] for ln in lines]
        if not lines:
            continue
        tokens = document_tokens(text)
        # Path tokens boost file-name hits ("curve.py" found by `curve`).
        for m in _IDENT_RE.finditer(rel):
            t = m.group(0)
            tl = t.lower()
            tokens["ident"][tl] = tokens["ident"].get(tl, 0) + 1
            for w in _WORD_RE.findall(t):
                wl = w.lower()
                tokens["word"][wl] = tokens["word"].get(wl, 0) + 1
        files[rel] = {"mtime": mtime, "size": size, "tokens": tokens, "lines": lines}
    index = {"version": 1, "root": str(root), "built": time.time(), "files": files}
    path = root / ".fent_cache" / SEARCH_INDEX
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = str(path) + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(index, f)
        os.replace(tmp, path)
    except Exception:
        pass
    return index


def load_search_index(project_dir):
    """Load the persisted search index, or None."""
    p = Path(project_dir) / ".fent_cache" / SEARCH_INDEX
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def is_stale(project_dir):
    """True when the cache is missing, a file was added/removed, or any
    indexed file's mtime changed since the index was built."""
    index = load_search_index(project_dir)
    if index is None:
        return True
    current = dict(_walk_file_mtimes(project_dir))
    if set(current) != set(index.get("files", {})):
        return True
    for rel, mtime in current.items():
        ent = index.get("files", {}).get(rel)
        if ent is None or abs(ent.get("mtime", -1) - mtime) > 1e-6:
            return True
    return False


def get_index(project_dir):
    """Fresh cache → reuse it; otherwise rebuild + persist."""
    index = load_search_index(project_dir)
    if index is not None and not is_stale(project_dir):
        return index
    return build_search_index(project_dir)


# ── searching ──

def _score_file(ent, units, phrase):
    """Token-overlap score (symbols > identifiers > words), log-squashed for
    file size, plus the line-match bonus. Returns (score, match_index) or
    None when the file shares no token with the query."""
    toks = ent.get("tokens", {})
    raw = sum(WEIGHTS[k] * toks.get(k, {}).get(u, 0) for k, u in units)
    if raw <= 0:
        return None
    lines = ent.get("lines", [])
    score = raw / (1.0 + math.log(max(1, len(lines))))
    words = [u for k, u in units if k == "word" and len(u) >= 2]
    phrase_line = None
    word_line = None
    line_words = 0
    for i, ln in enumerate(lines):
        lk = _phrase_key(ln)
        if phrase and phrase in lk:
            if phrase_line is None:
                phrase_line = i
        elif phrase_line is None and words:
            cnt = sum(1 for w in words if w in lk)
            if cnt:
                if word_line is None:
                    word_line = i
                if cnt >= 2:
                    line_words = max(line_words, cnt)
    if phrase_line is not None:
        score += PHRASE_BONUS
    elif line_words >= 2:
        score += WORDS_BONUS
    match = phrase_line if phrase_line is not None else word_line
    if match is None:
        return None
    return score, match


def search(project_dir, query, top_k=5):
    """Ranked search: token overlap (weighted) + line-match bonus. Returns
    [{path, line, text, score}] — line is the first matching line number
    (1-based), text is that line trimmed to 120 chars."""
    index = get_index(project_dir)
    units = query_units(query)
    if not units:
        return []
    phrase = _phrase_key(query)
    results = []
    for rel, ent in index.get("files", {}).items():
        sc = _score_file(ent, units, phrase)
        if sc is None:
            continue
        score, match = sc
        results.append({"path": rel,
                        "line": match + 1,
                        "text": ent["lines"][match][:TEXT_CHARS],
                        "score": round(score, 3)})
    results.sort(key=lambda r: (-r["score"], r["path"]))
    return results[:top_k]


def search_snippet(project_dir, query, top_k=3, radius=4):
    """Like search, but returns whole line windows for context feeding:
    [{path, start_line, lines: [...]}]. radius = lines around the match."""
    index = get_index(project_dir)
    out = []
    for hit in search(project_dir, query, top_k=top_k):
        ent = index.get("files", {}).get(hit["path"])
        if not ent:
            continue
        n = int(hit["line"])
        lines = ent["lines"]
        lo = max(0, n - 1 - radius)
        hi = min(len(lines), n + radius)
        out.append({"path": hit["path"], "start_line": lo + 1,
                    "lines": lines[lo:hi]})
    return out


# ── `~` similar-files ──

def _file_bigrams(index, rel):
    """Char-2-gram set of a file's first 200 lines (memoized for the life of
    the loaded index dict — computed once per build)."""
    memo = _BIGRAM_MEMO.get(id(index))
    if memo is None:
        memo = {}
        _BIGRAM_MEMO[id(index)] = memo
    bg = memo.get(rel)
    if bg is None:
        ent = index.get("files", {}).get(rel, {})
        head = "\n".join(ent.get("lines", [])[:200])
        bg = frozenset(_bigrams(head))
        memo[rel] = bg
    return bg


def similar(project_dir, text, top_k=3):
    """The `~` operator: character-2-gram Jaccard of text against every
    file's first 200 lines (cached per build). Returns [{path, score}]."""
    index = get_index(project_dir)
    qt = _bigrams(text)
    if not qt:
        return []
    scored = []
    for rel in index.get("files", {}):
        ft = _file_bigrams(index, rel)
        union = qt | ft
        if not union:
            continue
        j = len(qt & ft) / len(union)
        if j > 0:
            scored.append({"path": rel, "score": round(j, 4)})
    scored.sort(key=lambda r: (-r["score"], r["path"]))
    return scored[:top_k]


# ── query dispatch ──

def run_query(project_dir, query, top_k=5):
    """Dispatch a search request: leading `~` → similar (stripped); anything
    else → search. Returns a text block formatted for the model:
      SEARCH "velocity curve" — top 5:
        ep_compiler/mode_v5_performance.py:213  @curve vel <start> <end>
    """
    q = query.strip()
    if q.startswith("~"):
        payload = q[1:].strip()
        hits = similar(project_dir, payload, top_k=top_k)
        head = f'SIMILAR "{payload}" — top {len(hits)}:'
        rows = [f'  {h["path"]}  ({h["score"]})' for h in hits]
    else:
        hits = search(project_dir, q, top_k=top_k)
        head = f'SEARCH "{q}" — top {len(hits)}:'
        rows = [f'  {h["path"]}:{h["line"]}  {h["text"]}' for h in hits]
    if not rows:
        return head + "\n  (no matches)"
    return head + "\n" + "\n".join(rows)