# Language Reference — v5 (canonical)

Source of truth: `SYNTAX.md`. Rules: never invent syntax not in SYNTAX.md;
all new syntax goes in the v5 path (`ep_compiler/`). Files: `.e` (source),
`.ei` (project index), `.eic` (one-file bundle), `.ec` (binary), `.ee`
(encrypted), `.enx` (album). Comments: `//` line, `/* */` block, `#` legacy
(outside headers).

## v5 is canonical; legacy is hard-banned for new files

Every source compiles as v5 by default. v1–v4 still compile with deprecation
warnings — never write them. The v5 statement set below is **verified
against `tests/v5_statements_test.py` (29/29 passing)**; that file is the
ground truth for what v5 means.

## The v5 statement set (exact spellings)

```text
print "text"                      // literal string
print {2 + 3}                     // {expr}, $var, note name (N60 → C4)
assert {2 + 2} == 4, "ok"         // compile FAILS when false (AssertionError)
include "parts/hook.e"            // inline, relative to source dir; depth ≤16,
                                  //   cycles rejected, missing file raises
!fn arp(r, d, v) = play note($r) @dur:$d @vel:$v   // macro definition
!arp(C4, e, mf)                   // invoke: literal, $var, {expr}, note-name args
prog(C:q G:q Am:h F:q)            // chord progression → stacked chord notes
perc(kick)                        // GM drum on channel 9 (kick=36 snare=38
                                  //   hihat=42 ...); unknown drum rejected
@seed 42                          // deterministic RNG
$x = pick(60 64 67)               // deterministic choice (space-separated)
$y = rand(1, 4)                   // random int, inclusive
```

## Loops (all with `break` / `continue`; single- or multi-line `{ }`)

```text
for $n in [C4 E4 G4] { ... }              // list
for $i in 1..4 { ... }                    // range, inclusive
for $n in scale(C major, 4, 1) { ... }    // scale(name, octave, octaves)
for $n in run(C4, E4) { ... }             // chromatic run, inclusive
repeat 5 { ... }                          // fixed count
```

Scale names: `major minor harmonicminor melodicminor pentatonic blues dorian
phrygian lydian mixolydian locrian chromatic wholehalf halfwhole`. Loop
unroll cap 100k; loop vars resolve in `print`, `assert`, `!fn` args, and
math expressions.

## Piano-performance layer (v5 = v4 + these)

```text
pedal on / pedal off             // sustain CC64 127/0; @pedal:<0-127> global
rest q / rest 500ms / R 500ms    // silence advancing the cursor
@art:staccato|legato|tenuto|accent
t3(C4 E4 G4)                     // triplet (3 over 2 beats); trip()/tup(5,1,...)
[C4 D4 E4]/3                     // tuplet bracket form
@oct:+1 / @oct:-1                // octave shift
@curve vel 60 115 over 4q        // velocity curve over a window (or whole song)
C4~ q q                          // tie shorthand → merged durations (@tie)
```

## Human-mode play statements (the canonical way to write notes)

```text
play note(C4) @dur:q @vel:mf          // note, defaults: dur=1 beat, vel=80
play chord(C, major) @dur:h @vel:ff   // chord; qualities: major minor dim aug
                                      //   dom7 maj7 min7 dim7 sus2 sus4 m m7 7
play note(E4) @dur:e. @vel:80         // dotted (q. = 1.5 beats)
play note(C4) @dur:q @pan:-0.5 @bend:10 @ch:2 @track:lead @time:2s
play note(C4) @dur:q @sustain:127 @art:staccato @oct:+1 @tie
play chord(C, major) @dur:q @strum:0.03
```

Durations: `w h q e s t` = 4,2,1,½,¼,⅛ beats (plus words and dotted).
Velocity words: `ppp pp p mp mf f ff fff`. Cursor advances per statement.

## Valid v5 superset constructs (NOT deprecated — use freely)

These are v5-valid and do NOT demote the file:

```text
[C4 E4 G4](3:2)                  // polyrhythm: 3 steps over 2 beats
E(5,4)                           // Euclidean rhythm: 5 pulses over 4 steps
C4 q                             // v3 shorthand: note + duration
```

## Directives (`@`-prefixed, any line)

```text
@bpm 120            // tempo (also @tempo; Italian aliases: @allegro @adagio ...)
@key C major        // key signature (harmonic grounding / quantization)
@scale A_minor      // snap notes to nearest scale degree; @scale off disables
@vol:0.7 @master:0.7 @gain:-3db   // master volume / linear-amp gain
@sr:44100 @bit:16 @quality:standard  // audio render params
@sub:40hz @bass_boost:3db @stereo_width:120 @neural on  // sound shaping
@mem:64k            // event budget (warn+truncate) — k/m/g suffixes
@seed 42            // deterministic RNG → pick()/rand() reproducible
@gc:aggressive      // garbage-collect events (default|aggressive|off)
@oct:+1 @pedal:64 @sustain:64  // octave shift / global sustain 0..127
@strict on|off      // fail-fast compile (also --strict CLI flag)
```

## Math, variables, randomness

```text
$bpm = 120                    // variable definition (numeric or text)
$x = {$bpm * 2}               // {expr} substitution: + - * / // % ^ ( )
play note(C4) @dur:{$d * 0.5}ms   // expressions inline in any line
```

Known functions: `sin cos sqrt pow round floor abs min max quadratic
solve_linear pick rand`. `@seed N` makes pick/rand reproducible.

## Legacy syntax — HARD BAN in new files

These compile (for old material) but must **NEVER appear in files you
write**. Convert old sources with `run.py compile <file> --to v5`.

```text
T0 N60 D500 V80                    // machine lines (absolute timestamps)
N60  /  N60-72                     // v1 note shorthand / random note range
CH0 3:2 C4|E4 e                    // shorthand polyrhythm
ritard(2 bars)->100                // ritardando
!name body                         // v3 bare macros
?0.8 T0 N60 D500 V80               // probability gate
x4 repeat suffix
chord(I) / chord(V7)               // roman numerals
while $x < 10 { ... }              // while loops
for $i = 0 to N step S { ... }     // step loops
@curve bpm from 60 to 120          // v4 tempo curves
```

## Version detection

`detect_syntax_version` checks v5 markers first (`pedal on/off`, `rest`,
`t3(`, `@oct:`, `@art:`, `@tie`, `~` ties, `print/assert/include`, `prog(`,
`perc(`, `!fn`, `pick(/rand(`, `scale(/run(`, list/range loops,
break/continue), then v4/v3/v2/v1 markers, else defaults to v5. Deprecation
banner once per version. Convert: `run.py compile <old.e> --to v5`.
`run.py check` is authoritative: a pure v5 file reports at most the I001
info line; any deprecation warning means the file is not v5.

## Event dict (all parsers produce these)

```python
{"timestamp": int_ms, "midi": 0..127, "duration": int_ms,
 "velocity": 0..127, "pan": -1.0..1.0, "bend": -64..64}
# optional: channel track sustain pedal art tie octave
#           master_vol gain_db filter_* env_* phase cents swing strum
```
