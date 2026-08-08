"""Subagent orchestration for the copilot. The model's plan can carry a
"subagents" key: [{"task": ..., "context": ...}] — each subagent runs in a
separate chat (system = copilot base prompt + optional extra) via an
injected model_fn (the caller wires the real request function, so tests
and the BETA path never touch the network). Results are compactly
summarized for feeding back into the main loop."""


def run_subagent(model_fn, task, context, system_extra=""):
    """One subagent chat. System prompt = copilot base (lazily imported
    from plugins.llm.agent, avoiding an import cycle) + system_extra.
    model_fn(messages) returns the reply text, or a (text, err) tuple like
    providers.chat_request. Returns the reply text."""
    from . import agent as agent_mod  # lazy import — no cycle at module load

    system = agent_mod.SYSTEM_PROMPT
    if system_extra:
        system = system + "\n\n" + system_extra
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"TASK:\n{task}\n\nCONTEXT:\n{context or ''}"},
    ]
    result = model_fn(messages)
    text, err = result if isinstance(result, tuple) else (result, None)
    if err:
        raise RuntimeError(f"subagent request failed: {err}")
    return (text or "").strip()


def plan_subagents(plan):
    """Extract the plan's "subagents" key → [{"task", "context"}].
    Entries without a non-empty task are dropped; missing context → ''."""
    out = []
    for s in ((plan or {}).get("subagents") or []):
        if not isinstance(s, dict) or not s.get("task"):
            continue
        out.append({
            "task": str(s["task"]).strip(),
            "context": str(s.get("context") or ""),
        })
    return out


def run_plan_subagents(plan, model_fn, max_workers=4):
    """Run every subagent named in the plan. Sequential for BETA (max_workers
    is reserved for the parallel phase). A failing subagent is captured as an
    error result — it never aborts the batch. Returns [{task, result}]."""
    results = []
    for t in plan_subagents(plan):
        try:
            reply = run_subagent(model_fn, t["task"], t["context"])
        except Exception as e:
            reply = f"error: {e}"
        results.append({"task": t["task"], "result": reply})
    return results


def summarize(results):
    """Compact per-subagent one-liners for the main loop's next prompt:
    includes every task name and a truncated result."""
    results = results or []
    lines = [f"Subagent results ({len(results)}):"]
    for r in results:
        text = (r.get("result") or "").strip().replace("\n", " / ")[:160]
        lines.append(f"- {r.get('task', '?')}: {text}")
    return "\n".join(lines)