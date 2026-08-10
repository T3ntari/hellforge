# Compiler Pipeline, Events, Exports

Entry: `ep_compiler/compile.py` — `compile_source(text, bpm=None, strict=
False, base_dir=None)` → `(events, bpm)`. `compile_file(path)` routes by
extension (`.enx`/`.ei`/`.eci`/`.e`+`.eic`). `strict=True` raises
`CompileError` with every typed diagnostic; `@strict on|off` overrides.

## compile_source flow (ordered)

1. `@strict on/off` in text toggles strict mode.
2. **Strip comments** (`comments.py`: `//`, `/* */`, `#`).
3. **`include "file.e"`** — `resolve_includes`, before version detection so
   included content participates fully. Depth ≤16, cycles rejected, path
   relative to source dir then cwd.
4. **`!fn` macros** — `process_v5_pre` collects definitions → `(text, fns)`;
   uses expand post-unroll.
5. **LURE fast path** — if `plugins.lure` (LuaJIT) available and NO v5-only
   statements: compile via Lua 5–15× speedup, return early.
6. **`pre_compile` hooks** — `ep_core.trigger_event("pre_compile", text)`;
   last non-None result replaces the text.
7. **Directives → ll_state** — `parse_config_strip` (`#compiler k: v`), then
   `parse_directives(text, state)`. `DEFAULT_LL_STATE`: sr/bit/quality,
   filter/envelope/phase/cents/swing, sub/bass_boost/stereo_width/neural,
   master_vol/gain_db, mem, seed, key/scale, gc_strategy. `@seed` sets RNG;
   `bpm` from `@bpm` else param.
8. **Version detect** — `detect_syntax_version` (details in language.md);
   v1–v4 warn once, still compile.
9. **Math scope preseed** — pure-constant `$var = 120` definitions.
10. **Preprocessors** (v3/v4/v5): `expand_punctuation`, `preprocess_v3`,
    `process_polyrhythms` (tuplets `[notes]/N`, Euclidean `E(N,M)`,
    polyrhythm `(a:b)`, ritard, tempo curves), `process_performance_pre`
    (tie shorthand `C4~ q q`).
11. **`compile_v1`** core parse: strip per-line comments → unroll loops
    (`detect_and_unroll_loops`; break/continue, 100k cap) →
    `preprocess_math` ($var defs, `{$expr}`, bare $var) → `process_v5_lines`
    (print/assert/prog/perc/`!fn`, math re-run) → per line in order: **LURE
    batch** → `parse_performance_line` (pedal/rest/`t3()/trip()/tup()`) →
    **machine** → **human** (cursor-advance) → plugin `_syntax_handlers`;
    then `sort_events` + `validate_events` (`print midi` emits stats).
12. **Post passes**: `apply_scale_quantization` (`@scale`; LURE quantize,
    else NumPy `scale_quantizer`) → `apply_ll_controllers` (`@gain:dB`
    scales velocities; `@gc:strategy` → `ep_core.run_gc`; `@mem:N` truncates
    past budget) → `apply_performance_post_passes` (velocity curve → ties
    merge → sustain stamp → octave shift → legato stretch).
13. **`post_compile` hooks** — feed-forward: each `cb(events, bp)` sees the
    previous hook's output; None leaves events unchanged (Humanize →
    Talisman layering). v2 path: `compile_v2` → same post passes.
14. Stores `ep_core._last_compiled_events`/`_compilation_count`.

## Event dict

`ep_compiler/events.py` — the single contract every parser/mode/config
feeds (shape + optional keys in language.md). Helpers: `create_event(ts,
midi, dur, vel, pan, bend)` (range-clamped), `midi_to_name/name_to_midi`,
`validate_events` (drops midi∉[0,127] or dur≤0, clamps vel → `(clean, n)`),
`sort_events` (timestamp, midi). Pedal/CC64 events are `midi==0` with
`sustain` set (or `pedal: True`).

## Directives → ll_state (apply_ll_controllers)

`parse_directives` maps every `@directive` onto `ll_state` (defaults in
`DEFAULT_LL_STATE`; syntax + semantics in language.md). `apply_ll_controllers`
acts on the compiled events: `@gain:dB` → `velocity × 10^(db/20)`;
`@gc:<strategy>` → `ep_core.run_gc(events, strategy)` (default/aggressive/off);
`@mem:N[k|m|g]` → warn + truncate past the event budget; `@master/@vol` →
CC7 at export; `@sr/@bit/@quality/@sub/@bass_boost/@stereo_width/@neural` →
synth render params; `@key/@scale` → quantizer + roman numerals; `@oct` →
+12·N on midi; `@pedal/@sustain` → CC64; `@seed` → RNG.

## Export formats (ep_compiler/formats.py)

| fn | output | How |
|---|---|---|
| `export_midi(events, bpm, path)` | `.mid` | mido; set_tempo, 4/4, CC7/91/93/10, polyphony warn >64, program 0, note_on/off (480 ticks/beat), CC64 sustain; sqrt-boost velocities when avg <40 |
| `export_ec` | `.ec` | binary `EC\x01\x00` + bpm f32 + count u32 + total u32 + per event `<IBHBhh` (ts, midi, dur, vel, pan·32767, bend·512) |
| `export_wav` | `.wav/.mp3` | mido→`piano_synth.render(mid, out, params)` (from @sr/@bit/…) → ffmpeg fallback |
| `export_eic` | `.eic` | bundles source text of `.e` / `.ei` (project/parts inline) / `.enx` (ordered projects inlined) |

## run.py CLI map

All run.py modes **re-enter through the K-rip hypervisor** (self-spawn
inside the sandbox; `KRIP_INNER=1`/`KRIP_BYPASS=1` skip it).

| Command | Usage | What it does |
|---|---|---|
| `compile` | `run.py compile <spec> -o <out>` | Compile to MIDI (default `<input>.mid`); `<spec>` = file/dir/`/`/glob; flags `--human`, `--machine`, `--strict`, `--mem`, `--recursive` |
| `check` | `run.py check <spec>` | Lint — the authoritative gate; `--recursive`, `--max <N>`; a pure v5 file reports at most I001 |
| `stats` | `run.py stats <file>` | Notes, duration, range, velocity, polyphony, density, channels |
| `tracks` | `run.py tracks <file>` | Per-channel table (+ per-track when `TRK[]` present) |
| `inspect` | `run.py inspect <file> [N]` | Show first N events (default 12) |
| `new` | `run.py new <name> [-o <dir>]` | Scaffold a v5 project: `index.ei` + `parts/main.e` + `README.md` |
| `transpose` | `run.py transpose <file> <n> [-o out]` | Shift notes by n semitones |
| `tempo` | `run.py tempo <file> <bpm> [-o out]` | Recompile at a new tempo |
| `merge` | `run.py merge <a> <b> [-o out]` | Concatenate two files |
| `integrity` | `run.py integrity [--github]` | Verify core digest vs committed (+ GitHub copy) |
| `hellgate` | `run.py hellgate` | HellGate → OpenCode wrapper |
| `ai` | `run.py ai ...` | Built-in copilot (see copilot.md) |

### Syntax conversion: `--to vN`

`run.py compile <old.e> --to v5` converts an old source to the canonical
version (portbaby converter; the v5 target is implemented as the
v4-superset conversion). Also `--to v1|v2|v3|v4`. Conversion is the
supported path for touching legacy files — never hand-port legacy syntax
into new v5 sources.

## Mode modules (parse layer)

| File | Handles |
|---|---|
| `mode_v1_machine.py` / `mode_v1_human.py` | machine lines / `play note·chord` (strict, typed problems) |
| `mode_v2_semantic.py` | v2 `[Section:]`, chord blocks, scale degrees |
| `mode_v3_extended.py` | v3 shorthand/macros/probability/roman-numeral preprocessor |
| `mode_v4_polyrhythm.py` | tuplets/Euclidean/polyrhythms/ritard preprocessor |
| `mode_v5_performance.py` / `mode_v5_statements.py` | pedal/rest/ties/curves/oct/legato · print/assert/include/!fn/prog/perc |
| `mode_eci.py`, `e_runtime.py`, `mode_enx.py` | `.eci` toggle, `.ei` project, `.enx` album compilers |
| `math_engine.py`, `variables.py`, `loops.py` | `{$expr}` → AST → evaluators (LURE>Python); `Scope`; loop unroller |
| `scale_quantizer.py`, `syntax_check.py` | snap-to-scale; lexicons + typed validators (parsers/lint/LSP share) |
| `lint.py`, `comments.py`, `punctuation.py` | static analysis; comment & separator stripping |

Diagnostics: `compile_v1` collects `last_problems` (machine/human) —
`{"code", "line", "char", "length", "message"}` (E051–E060, W019); strict
mode raises `CompileError` listing them; lint/LSP read the same stores.
