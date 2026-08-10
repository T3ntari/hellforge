**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [trust-model](trust-model.md) | [strict-enforcement](strict-enforcement.md) | [identity-management](identity-management.md) | [rate-limiting](rate-limiting.md)

## Rate Limiting

HELLFORGE has **no built-in server endpoints** — there is nothing to rate
limit by default, and no `/e_identity`-style endpoints exist. The guidance
below is generic and applies only to **opt-in** network features you
configure yourself.

### Opt-in network features

| Feature | Env vars | When it talks to the network |
|---------|----------|------------------------------|
| Integrity verification | — | `run.py integrity --github` / Technique Y compares against the public GitHub repo (read-only) |
| Safe updates | — | `u` in the boot menu / safe-update prompt — fetches the version tag from GitHub |
| Plugin verification (remote) | `HF_VERIFY_URL`, `HF_VERIFY_TOKEN` | `tools/verify_integrity.py --remote` — pulls verification codes from *your* registry |
| LLM providers | `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENROUTER_API_KEY`, `GEMINI_API_KEY`, `HELLGATE_*` | calls the provider you configured (Ollama is local) |
| Deploy tooling | `HF_DEPLOY_*` | only if you use it |

Nothing is hardcoded: with unset variables the system is fully local.

### Generic advice for your own services (HF_VERIFY_URL)

If you run your own verification registry, apply standard protection:

- Per-client request budgets (e.g. per IP / token), short windows, with
  `429 Too Many Requests` + `Retry-After` on overflow
- Exponential backoff on the client side for transient failures
- Cap payload sizes and timeouts; never trust client-supplied paths
- Treat `HF_VERIFY_TOKEN` as a secret — it is read from the environment
  only, never committed

### Local limits

The system itself bounds its own resource usage via the K-rip hypervisor
(`krip mem`, `krip cpu`, GPU selection) and the sandbox RLIMITs (CPU time,
file size) for sandboxed processes — see
[K-rip commands](../commands/krip-commands.md).