# HELLFORGE Samples & Examples Index

Reference index of `samples/`, `songs/` and `examples/` — what each
demonstrates. Type column: v5 / v4 / v3 / v1 / v2 / ei / eic / enx / ec
(syntax version or project format). All v1–v4 sources compile but are
deprecated (warnings); v5 is canonical.

## samples/

| Path | Type | What it demonstrates |
|---|---|---|
| `samples/v5-current/README.md` | v5 | Feature cheat-sheet for the v5 statement set + piano-performance layer |
| `samples/v5-current/pattern_demo.e` | v5 | The full v5 statement set in one piece: `!fn` macros, `for-in-scale` / `for-in-range` loops, `print`, `assert`, `prog`, `perc`, `@seed` + `pick` |
| `samples/v5-current/performance_demo.e` | v5 | Seven piano-performance features: `pedal on/off`, articulations (`@art:staccato/legato/tenuto/accent`), tuplets (`t3(...)`), `rest`, octave shift (`@oct:+1`), velocity curve (`@curve vel 60 115`), ties (`C4~`); plus audio directives (`@sr`, `@bit`, `@quality`, `@vol`) |
| `samples/v4-current/basics/hello_world_v4.e` | v4 | Minimal note (`C4 q`), `@bpm`, note-duration shorthand |
| `samples/v4-current/basics/euclidean.e` | v4 | Euclidean rhythms `5:8`, `3:4`, `7:12` (beats:steps) |
| `samples/v4-current/basics/rhythm_layers.e` | v4 | Polyrhythm layering — `3:2` cross-rhythm over steady quarters (hemiola) |
| `samples/v4-current/generative/probability.e` | v4 | Aleatoric composition: `@prob 0.5` probability gates per note |
| `samples/v4-current/generative/tempo_curve.e` | v4 | Tempo curves: `@curve bpm from 60 to 120 over 4` (accelerando/ritardando) |
| `samples/v4-current/generative/polyrhythm_complex.e` | v4 | Three simultaneous polyrhythms (`3:2` + `4:3` ...) on separate channels (`CH0/CH1/...`) |
| `samples/v4-current/humanize/humanize_demo.e` | v4 | `@humanize:40` — MoE human micro-timing/velocity feel on a repeated melody |
| `samples/v4-current/loops/for_step.e` | v4 | `for $i = 0 to 12 step 3` stepped loop |
| `samples/v4-current/loops/nested_for.e` | v4 | Nested for loops building a 2D pitch grid (`N{60 + $i*4 + $j*2}`) |
| `samples/v4-current/loops/var_update_loop.e` | v4 | `while $base < 72 { ... }` mutable-variable loop |
| `samples/v4-current/math/modulo_arpeggio.e` | v4 | `%` modulo in a loop for pattern cycles |
| `samples/v4-current/math/quadratic_notes.e` | v4 | `quadratic()` math driving note parameters over a loop |
| `samples/v4-current/math/velocity_sin.e` | v4 | `sin()` modulating velocity — wave-like dynamic envelopes |
| `samples/v3-supported/basics/channels.e` | v3 | MIDI channel binding `CH0/CH1/CH2` (piano/strings/bass) |
| `samples/v3-supported/basics/first_note.e` | v3 | Simplest note + duration |
| `samples/v3-supported/basics/note_durations.e` | v3 | Duration codes `w h q e s t` and dotted forms |
| `samples/v3-supported/basics/velocity_dynamics.e` | v3 | Velocity words `ppp pp p mp mf f ff fff` (16–127) |
| `samples/v3-supported/chords/arpeggio_v3.e` | v3 | `@mode:arpeggio` — broken-chord arpeggio of `play chord(C, major)` |
| `samples/v3-supported/chords/chord_progression.e` | v3 | Chord progressions via `play chord()` |
| `samples/v3-supported/loops/for_scale.e` | v3 | `for $i = 0 to N` scale-building loop |
| `samples/v3-supported/loops/repeat_pattern.e` | v3 | `repeat N { }` fixed-count repetition |
| `samples/v3-supported/loops/while_counter.e` | v3 | `while` counter loop |
| `samples/v3-supported/math/functions.e` | v3 | Built-in math functions `sin cos sqrt pow min max abs floor` in `{expr}` |
| `samples/v3-supported/math/scale_calc.e` | v3 | `$base` var + `{expr}` math to construct a C-major scale |
| `samples/v3-supported/math/var_expr.e` | v3 | Variable definitions + expressions |
| `samples/v1-deprecated/machine/bare_minimum.e` | v1 | Minimal machine line `T0 N60 D500 V100` |
| `samples/v1-deprecated/machine/dynamics.e` | v1 | Velocity range via the `V` token (0–127) |
| `samples/v1-deprecated/machine/melody.e` | v1 | C-major scale melody in absolute machine timestamps |
| `samples/v1-deprecated/human/play_notes.e` | v1 | `play note(...)` human mode + duration/velocity qualifiers |
| `samples/v1-deprecated/human/play_chords.e` | v1 | `play chord(C, major) @dur:w` — I–IV–V–I progression |
| `samples/v2-deprecated/semantic_basics.e` | v2 | `[Section:]`, `Key:` headers, semantic vocabulary |
| `samples/v2-deprecated/semantic_song.e` | v2 | Sections (Intro/Verse/Chorus), `arpeggio()`, `chromatic_run()` |
| `samples/ei/simple_project.ei` | ei | Multi-file project: `**inherit parts/intro.e**` + parts/verse.e, `@title`/`@bpm` metadata |
| `samples/ei/parts/intro.e` | ei | Part file: self-contained C-major arpeggio phrase (inherited, not standalone) |
| `samples/ei/parts/verse.e` | ei | Second inherited part (verse melody) |
| `samples/eic/toggle_basics.eic` | eic | `#MACHINE` / `#HUMAN` mode toggling in one file |
| `samples/eic/toggle_full.eic` | eic | Full-feature machine+human toggle |
| `samples/eic/toggle_math.eic` | eic | Mode toggling combined with math expressions |
| `samples/enx/album.enx` | enx | Album root: `@title/@artist/@year` metadata + `**track tracks/song1.e**` |
| `samples/enx/tracks/song1.e` | enx | Album track: intro → `repeat` riff → variation → outro |

## songs/

| Path | Type | What it demonstrates |
|---|---|---|
| `songs/aurora_nocturne.e` | v5 | "Aurora Nocturne" — a complete, polished v5 piano piece (48 bars, C major, `@bpm 78`, `@seed 7`): `pedal on/off`, `!fn` ornament macros, `for-in-list` arpeggio loops, `@curve vel` swells, ties (`@tie`), dotted durations, dynamics pp→fff across intro → theme → restate → interlude → climax → coda. The reference for full-song structure in canonical v5. |

## examples/

| Path | Type | What it demonstrates |
|---|---|---|
| `examples/Rush_E.e` | reference | The signature HELLFORGE piece — 19853 events, 270 BPM, ~174s, note range 21–108 (aggressive tempo, dense polyphony) |
| `examples/Rush_E.ec` | ec | Compiled binary form of Rush_E (241KB, `EC\x01\x00` header, events `<IBHBhh`) |
| `examples/Rush_E.human` | reference | Human-mode rendering of Rush_E (117KB) |
| `examples/Rush_E.mid/.wav/.mp3/.mp4` | out | The exported artifacts (MIDI / audio / video) |
| `examples/v3-compositions/chord_song_v3.e` | v3 | "Harmony's Voyage" — pop progression I–vi–IV–V with `play chord()` inversions/voicings |
| `examples/v3-compositions/melody_v3.e` | v3 | "Morning Walk" — complete melody in v3 shorthand `C4 1.0` + `@vel` |
| `examples/v4-compositions/cinematic_v4.e` | v4 | "The Approaching Storm" — tempo curves (`@tempo_curve 60 72 16`), dynamic arcs, polyrhythms, probability, sections, 150+ events |
| `examples/v4-compositions/lullaby_v4.e` | v4 | "Starfall Slumber" — 64+ bars at `@bpm 80`: 5:4 polyrhythm arpeggios, `for` loops, velocity modulation (`@vel 30 + $i*3`) |
| `examples/v4-compositions/techno_v4.e` | v4 | "Acid Pulse" — 140 BPM: Euclidean hi-hat patterns, four-on-the-floor kick, `wait 1/4` sequencing |
| `examples/projects/suite.ei` | ei | 3-movement classical suite via `.ei` inheritance (`title/composer/copyright/description` metadata) |
| `examples/projects/parts/movement1.e` | ei | Sonata-allegro movement: `section` blocks, `play C4 E4 G4 C5` chords, `@vel 80 + sin(...)*10`, `wait 1/2` |
| `examples/projects/parts/movement2.e` | ei | Second movement (slow, lyrical) |
| `examples/projects/parts/movement3.e` | ei | Third movement (fast finale) |
| `examples/albums/opus1.enx` | enx | 5-track album "First Light" with album/composer/year/genre metadata |
| `examples/albums/tracks/01_prelude.e` | enx | Track 1 "Prelude in C": broken-chord arpeggios, `@vel 35 + ($i*1.5)` crescendo |
| `examples/audio/audio_dsp_demo.e` | v4 | "Spatial Reverie" — DSP directives `@reverb_room/@reverb_damp/@reverb_wet`, `@vol`, `@pan` |
| `examples/gpu/gpu_math_demo.e` | v4 | "Radiance Engine" — heavy `sin()/cos()/quadratic()/sqrt()` math in loops (Radical GPU acceleration demo), 200+ events |
| `examples/eic/duality.eic` | eic | Machine/human duality composition |
| `examples/eic/hybrid.eic` | eic | "Cyborg Lullaby" — `#MACHINE` ambient pad + `#HUMAN` sections in one file |
| `examples/opengl_engine.py` | py | Reference game engine built on the OPENapi + Vulkanizer + EAudio plugins |

Notes:
- For canonical v5 style, mirror `samples/v5-current/pattern_demo.e`
  (statements) and `performance_demo.e` (performance layer); for a
  complete polished piece, study `songs/aurora_nocturne.e`.
- `run.py new <name>` scaffolds a fresh v5 project: `index.ei` +
  `parts/main.e` (pedal/rest/articulations) + `README.md`.
- v1–v4 sources in `samples/` and `examples/` are legacy; they compile with
  deprecation warnings — convert with `run.py compile <file> --to v5`.
