# Quickstart — HELLFORGE / E for Models (2-minute briefing)

**HELLFORGE (E)** is a DSL for piano music composition: plain text → `.mid`,
`.wav`, `.mp3`, `.mp4`, `.ec` (binary), `.eic` (one-file bundle). Version
**v0.1.14.41-beta**. Python 3.10+.

HELLFORGE is built like an OS:
- **kernel** = `ep_core.py` (plugin/mod registry, hooks, GC, signing, identity)
- **plugins = drivers** (14 shipped drivers under `plugins/`)
- **hypervisor = K-rip** (`plugins/krip/`): the boot manager + sandbox layer

Read this first, then `language.md` (syntax), `compiler.md` (pipeline),
`plugins.md` (drivers + hypervisor), `testing.md` (suites), `copilot.md`
(agent loop). Human docs: `SYNTAX.md`, `AGENTS.md`, `RULES.md`.

## You are running inside K-rip

Everything launches through the hypervisor. `krip` (no args) shows a
GRUB-style boot menu (3s countdown, ↑/↓ select, Enter boot, `c` console,
`u` update, Esc exit) → boots the kernel → drops into the **eshell
console**. Children run inside the K-rip sandbox: memory budget (RLIMIT_AS),
CPU affinity, GPU selection (`CUDA_VISIBLE_DEVICES`), graphics engine
(vulkan default / opengl), VulkanRT, tensor — configured in `krip.json`.

- `run.py <mode>` **re-enters through krip** automatically (spawns itself
  inside the sandbox). Children carry `KRIP_INNER=1` (no re-wrap);
  `KRIP_BYPASS=1` skips the wrap entirely.
- `krip run <cmd...>`, `krip eshell|shell`, `krip hellgate`, `krip player
  <file>`, `krip status`, `krip os` (kernel/drivers table).
- Sandbox anything: `krip sandbox run <name> -- <cmd...>` / `list` / `kill`.

## Integrity & SAFE MODE (X / Y)

Every init runs the security sequence: **X first (local, offline)** — the
160-byte triple aggregate (SHA-256 + SHA-512 + BLAKE2b-512 of the
`SECURITY_HASH.txt` manifest) is hidden as rotating random fragments under
`.e_identity/.integrity` (order file auto-deleted after use, re-randomized
every init) — then a network probe: online → **Y** (per-version key in
`ep_compiler/_version_key.py`, verified against the GitHub copy at the
version tag) + version check; **offline, X alone is the proof**.

On failure the system enters **SAFE MODE**: `status`, `reinstall` (re-install
preserving everything), `/safemode exit force` (risky), or `quit`.

Check it yourself: `run.py integrity [--github]`.

## Five things to know immediately

1. **v5 is canonical.** Everything compiles as v5 by default; v1–v4 still
   compile with warnings. New syntax goes ONLY in the v5 path
   (`ep_compiler/`), and only if it is in SYNTAX.md. Polyrythm/Euclidean/
   v3-shorthand are valid v5; machine lines, `while`, `for $i = 0 to N
   step S`, `?0.8`, roman chords, `ritard`, `N60-72`, `@curve bpm from`
   are legacy **hard bans** (see language.md).
2. **The event dict is the whole world.** Every parser emits
   `{"timestamp", "midi", "duration", "velocity", "pan", "bend"}` dicts
   (`ep_compiler/events.py`). Compile → events → export. Nothing else.
3. **v5 writing is human-mode + statements:** `play note(C4) @dur:q
   @vel:mf`, `prog(C:q G:q Am:h F:q)`, `perc(kick)`, `for $n in
   scale(C major, 4, 1) { ... }`, `!fn` macros, `@seed`+`pick/rand`,
   `pedal on/off`, `rest q`, `@art:staccato`, `@curve vel 60 115`, ties
   `C4~ q q`. v5 auto-detects; machine lines compile only for legacy.
4. **Always venv**: `.venv/bin/python ...`, never bare `python`. Tests:
   `.venv/bin/python tests/<file>_test.py`.
5. **Hard rules:** no whole-file rewrites (line-range edits only), no
   deletions without per-file confirmation, no paths outside the project
   root, no destructive shell commands, suite green before finish.

## Where things live

- `ep_compiler/` — compiler core (parser, modes, directives, math, loops, formats)
- `ep_core.py` — the kernel: plugin registry, hooks, GC, signing, identity
- `plugins/` — drivers (`krip/` hypervisor, `hellgate/` OpenCode wrapper,
  `llm/` copilot, `humanize/` feel, ...)
- `tests/` — `*_test.py` harness suites (no pytest); `samples/v5-current/` — canonical examples
- `.e_identity/` — kernel registry, X/Y hidden fragments, identity (gitignored — never touch)

## Entry points

```bash
.venv/bin/python run.py compile song.e -o song.mid   # compile (through krip)
.venv/bin/python run.py check <spec>                 # lint — authoritative
.venv/bin/python run.py stats|tracks|inspect <file>  # verify a result
.venv/bin/python run.py new <name>                   # scaffold a v5 project
.venv/bin/python run.py transpose|tempo|merge ...    # MIDI transforms
.venv/bin/python run.py integrity [--github]         # core integrity check
.venv/bin/python run.py hellgate                     # OpenCode wrapper
.venv/bin/python run.py ai fix "<issue>"             # built-in AI copilot
.venv/bin/python eshell.py                           # interactive shell (also: krip)
.venv/bin/python player.py song.e                    # playback
```

Verify work with `run.py check` (a pure v5 file reports at most the I001
info line) and `run.py compile <file> -o <out>.mid` (must compile cleanly).

## The 5 most important rules (RULES.md)

1. Never rewrite an existing file whole-file — line-range edits
   (`"lines": [a, b]` + `"replace"`) or insertions (`"lines": [x]`).
2. Never delete a file without explicit per-file confirmation; `a` (all)
   never auto-confirms deletes.
3. Never touch anything outside the project root; no reads/writes in
   protected dirs (`.e_identity/`, `.venv/`, `hellgate-state/`, `logs/`,
   `.git/`).
4. Only safe commands: `python tests/x.py`, `git status/diff/log` — no
   `rm`, `mv`, `sudo`, `pip install`, pipes, redirects.
5. After any `.py` change run relevant tests; full suite green before done.
   Never commit red. Update `TODO.md` as you work.
