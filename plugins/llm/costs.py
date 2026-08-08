"""Token + cost accounting for copilot sessions. estimate_tokens is a
chars/4 heuristic (no tokenizer dependency); SessionCost records each
provider/model exchange and renders a human-readable cost summary.
Ollama/custom endpoints are always free (local)."""

# ── pricing table (USD per 1M tokens: (input, output)) ──

PRICING = {
    "deepseek": (0.27, 1.10),   # deepseek-chat
    "openai": (2.50, 10.00),    # gpt-4o
    "claude": (3.00, 15.00),    # claude-sonnet-4-5
    "ollama": (0.0, 0.0),       # local — always free
    "custom": (0.0, 0.0),       # local/custom endpoint — free
}

LOCAL_PROVIDERS = {"ollama", "custom"}


def estimate_tokens(text):
    """chars/4 heuristic. Accepts a plain string OR a list of messages
    ({role, content}) — a messages list is summed across all contents."""
    def _len(content):
        if isinstance(content, list):  # Anthropic-style text blocks
            return sum(len(str(b.get("text", "")))
                       for b in content if isinstance(b, dict))
        return len(str(content or ""))
    if isinstance(text, (list, tuple)):
        total = 0
        for m in text:
            if isinstance(m, dict):
                total += _len(m.get("content"))
            else:
                total += _len(m)
        return total // 4
    return _len(text) // 4


def price_for(provider, model=None):
    """(input, output) USD per 1M tokens for a provider; unknown providers
    are treated as free and never break accounting."""
    return PRICING.get((provider or "").lower().strip(), (0.0, 0.0))


def _fmt_tokens(n):
    if n < 1000:
        return str(int(n))
    return f"{n / 1000:.1f}k"


class SessionCost:
    """Tracks tokens/cost across one session (or any exchange batch).
    record() per exchange; total() aggregates, render() prints the summary."""

    def __init__(self, provider="", model=""):
        self.provider = provider or "unknown"
        self.model = model or "unknown"
        self._records = []

    def record(self, messages, reply_text):
        """Record one exchange (input messages + reply). Returns the
        per-exchange dict {provider, model, tokens_in, tokens_out, cost}."""
        pin, pout = price_for(self.provider)
        tin = estimate_tokens(messages)
        tout = estimate_tokens(reply_text)
        rec = {
            "provider": self.provider,
            "model": self.model,
            "tokens_in": tin,
            "tokens_out": tout,
            "cost": tin * pin / 1e6 + tout * pout / 1e6,
        }
        self._records.append(rec)
        return rec

    @property
    def price(self):
        return price_for(self.provider, self.model)

    def total(self):
        """Aggregate dict: totals + per-(provider, model) breakdown."""
        agg = {}
        for r in self._records:
            key = (r["provider"], r["model"])
            a = agg.get(key)
            if a is None:
                a = {"provider": key[0], "model": key[1],
                     "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
                agg[key] = a
            a["tokens_in"] += r["tokens_in"]
            a["tokens_out"] += r["tokens_out"]
            a["cost"] += r["cost"]
        return {
            "tokens_in": sum(r["tokens_in"] for r in self._records),
            "tokens_out": sum(r["tokens_out"] for r in self._records),
            "cost": sum(r["cost"] for r in self._records),
            "per_model": [agg[k] for k in sorted(agg)],
        }

    def render(self):
        """Multi-line human summary (see module docs for the shape)."""
        t = self.total()
        lines = [f"Session cost — {_fmt_tokens(t['tokens_in'])} tokens in, "
                 f"{_fmt_tokens(t['tokens_out'])} out"]
        for m in t["per_model"]:
            line = f"{m['provider']} · {m['model']} — ${m['cost']:.4f}"
            if m["provider"] in LOCAL_PROVIDERS:
                line += " (local)"
            lines.append(line)
        lines.append(f"TOTAL: ${t['cost']:.4f}")
        return "\n".join(lines)