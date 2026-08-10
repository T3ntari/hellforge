**HELLFORGE OS v0.1.14.41-beta** — [index](index.md) | [getting-started](getting-started.md) | [contributing](contributing.md) | [changelog](changelog.md) | [faq](faq.md)

## Frequently Asked Questions

### What is HELLFORGE?

HELLFORGE is a domain-specific language for **piano music composition** — and
an OS-like system around it. You write music as plain text and E compiles it
to `.mid`, `.wav`, `.mp3`, `.ec`, `.eic`. Architecturally: `ep_core` is the
kernel, each plugin is a driver, and **K-rip** (plugin id `krip`, v1.0.0) is
the hypervisor that boots the system, sandboxes every process, and performs
safe updates. Current version: **v0.1.14.41-beta**.

### How do I start the system?

```bash
python3 run.py krip
```

This shows the GRUB-style boot menu (3s countdown, ↑/↓ to select, Enter to
boot, `c` console, `u` safe update, Esc to exit) and lands in the eshell
console. Every other launch path (`run.py play`, `run.py shell`, direct
`eshell.py`) re-enters through K-rip unless `KRIP_BYPASS=1` is set.

### What platforms are supported?

Windows, macOS, Linux (Python 3.10+). GPU acceleration is optional and
degrades gracefully — math evaluation falls back
TensorSHARP → Radical → LURE → Python.

### What is the v5 syntax?

v5 is the **canonical** language version and the default for all sources.
It is a superset of v4: polyrhythm `[C4 E4 G4](3:2)`, Euclidean
`E(5,4)`, and v3 shorthand (`C4 q`) are all valid v5. v1–v4 sources still
compile but emit deprecation warnings — convert with
`run.py compile <old.e> --to v5`. Run `run.py check <file>` for the
v5-aware linter (a pure v5 file reports at most `I001`). Legacy constructs
that are **not** v5: machine lines (`T0 N60 D500 V80`), `N60-72` ranges,
`CH0` poly shorthand, `ritard`, roman-numeral chords, `while`, `for $i = 0
to N step S`, `?0.8`, v4 `@curve bpm from`.

### How do I update HELLFORGE?

Press `u` in the K-rip boot menu (or answer yes to the safe-update prompt
after boot) when a newer version exists on GitHub. The safe update
backup/restores `.plugin_config.json`, `.env`, `.e_identity/`, `mods/`, and
custom plugins, and extends the manifest with `SECURITY_HASH.local` for
custom plugin directories. The previous kernel stays bootable for rollback
(via the kernel registry in `.e_identity/kernels.json`).

### What is SAFE MODE?

If the integrity checks fail (Technique X hidden digest, or Technique Y
against GitHub when online), the system boots into an isolated shell:
`status` shows what failed, `reinstall` re-installs the current version from
GitHub with a progress bar (preserving everything), `/safemode exit force`
leaves anyway with a risk warning, `quit` stays.

### Is there any network or backend?

**No.** There is no network backend, no hardcoded endpoints, and no
credentials anywhere in the repo. Everything is local-first; network
features are opt-in via environment variables (`HF_REGISTRY`,
`HF_VERIFY_URL`, `HF_VERIFY_TOKEN`, `HF_DEPLOY_*`, LLM provider keys). Local
plugin integrity uses SHA-256 codes in `pkglist.json`
(`tools/verify_integrity.py`); local identity lives in `.e_identity/`
(gitignored).

### How do I sign files?

Signing is an optional local feature: `sign --setup` creates an ED25519
identity under `.e_identity/`, then `sign <file>` adds an author signature.
Enforcement is controlled by `sys strict 0|1|2` (2 = block unsigned
plugins). There is no server registration.

### Can an AI help me compose?

Yes — the built-in LLM copilot (`run.py ai`, plugin `llm`): `ai ask`,
`ai chat`, `ai fix`, `ai plugin`. Providers: ollama, openai, anthropic,
deepseek, custom (Ollama is listed last, local by default). HellGate
(`run.py hellgate`) boots OpenCode focused on this project with the
knowledge pack, Music-Composer and Music-Refiner agents.

### How do I test my changes?

Each suite is self-contained: `python3 tests/<name>_test.py` — for example
`tests/security_hash_test.py` (X/Y integrity) or
`plugins/krip/tests/test_krip.py`. `tests/run_all.py` runs everything.

### Is HELLFORGE open source?

Yes. MIT license — see [LICENSE](../LICENSE).
