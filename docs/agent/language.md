# Language Reference — v5 (canonical)

Source of truth: `SYNTAX.md`. Rules: never invent syntax not in SYNTAX.md;
all new syntax goes in the v5 path. Files: `.e` (source), `.ei` (project
index), `.eci` (mode-toggle), `.enx` (album), `.eic` (inline bundle), `.ec`
(binary). Comments: `//` line, `/* */` block, `#` legacy (outside headers).

## Machine mode — absolute timestamps

`T0 N60 D500 V80` — `T<ms>` `N<midi|name>` `D<ms>` `V<0-127|0.0-1.0|word>`.

```text
T0 N60 D500 V80            // note 60 (C4), 500ms, velocity 80
T500 N C4 D q V mf         // word forms: note name, duration q, velocity mf
CH1 T0 N60 D100 V0.8       // channel 1 (CH[n] or CHn); TRK[melody] = track meta
T0 N60 D500 V80 P[bend:-12] S[pan:0.5] S[art:staccato]  // bend/pan/art
T0 N60 D500 V80 F[c:200hz] F[r:0.8] F[t:lowpass] E[a:5ms] E[r:100ms] E[s:0.7]
```

Durations: `w h q e s t` = 4,2,1,½,¼,⅛ beats (`D q`); missing D → 500ms.
V words: `ppp pp p mp mf f ff fff` (+ soft/normal/loud/max). Machine lines
use absolute `T`; human statements advance a cursor.

## Human mode — relative cursor

`play note(C4) @dur:q @vel:mf`, `play chord(C, major) @dur:h @vel:ff`.
Statements advance a cursor; machine lines jump to absolute `T`.
```text
play note(C4) @dur:q @vel:mf          // note, defaults: dur=1 beat, vel=80
play chord(C, major) @dur:h @vel:ff   // chord, quality from table below
play note(E4) @dur:e. @vel:80         // dotted (q. = 1.5 beats); 500ms / 0.6 OK
play note(C4) @dur:q @pan:-0.5 @bend:10 @ch:2 @track:lead @time:2s
play note(C4) @dur:q @sustain:127 @art:staccato @oct:+1 @tie  // CC64/art/oct/tie
play chord(C, major) @dur:q @strum:0.03  // strummed chord
```

Quality table: `major minor dim aug dom7 maj7 min7 dim7 sus2 sus4 m m7 7 maj min`.
Durations: `w h q e s t` + words (whole/half/quarter/eighth/sixteenth/thirtysecond) + dotted;
default chord root octave 4 (`C` → C4). Cursor advances per statement.

## Directives (`@`-prefixed, any line)

```text
@bpm 120            // tempo (also @tempo; Italian aliases: @allegro @adagio ...)
@key C major        // key signature (scale for quantization/roman numerals)
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

## v5 statements

```text
print "text"  /  print {2 + 3}    // literal, expr, $var, N60 (→ C4), midi (→ stats)
assert {2 + 2} == 4, "ok"   // compile fails when false (raises AssertionError)
include "parts/hook.e"      // inline file pre-version-detection (depth ≤16)
!fn arp(r, d, v) = play note($r) @dur:$d @vel:$v   // parameterized macro
!arp(C4, e, mf)             // use ($1..$n and named params substituted)
prog(C:q G:q Am:h F:q)      // chord progression → human chord lines
perc(kick)                  // GM drum on ch9: kick snare clap hihat openhat
                            //   tom_low/mid/high crash ride tambourine cowbell shaker
```

## Loops (all with `break` / `continue`; single- or multi-line `{ }`)

```text
for $n in [C4 E4 G4] { play note($n) @dur:q }       // list
for $i in 1..8 { print {$i} }                       // range, inclusive
for $n in scale(C major, 4, 1) { ... }              // scale(name, octave, octaves)
for $n in run(C4, C5) { ... }                       // chromatic, inclusive
for $i = 0 to 4 step 2 { ... }   repeat 3 { ... }   // classic / fixed count
while $x < 10 { $x = $x + 1 }                       // mutable-condition loop
```

Scale names: major minor harmonicminor melodicminor pentatonic blues dorian
phrygian lydian mixolydian locrian chromatic wholehalf halfwhole. Loop vars
resolve in `print`, `assert`, `!fn` args, math. Unroll cap 100k.

## Math, variables, randomness

```text
$bpm = 120                    // variable definition (numeric or text)
$x = {$bpm * 2}               // {expr} substitution: + - * / // % ^ ( )
play note(C4) @dur:{$d * 0.5}ms   // expressions inline in any line
$v = pick(C4 E4 G4)           // deterministic choice (space-separated)
$x = rand(1, 8)               // random int, inclusive (seeded by @seed)
```

Known functions: `sin cos sqrt pow round floor abs min max quadratic
solve_linear pick rand`. `@seed N` makes pick/rand reproducible.

## Piano performance (v5 = v4 + these)

```text
pedal on / pedal off         // sustain CC64 127/0 events
rest q / rest 500ms / R 500ms // silence advancing the cursor
t3(C4 E4 G4) @vel:f          // triplet (3 over 2 beats); trip()/tup(5,1,...) too
[C4 D4 E4]/3                 // tuplet bracket form (nested allowed)
@curve vel 60 115 over 4q    // velocity curve over window (or whole song)
C4~ q q                      // tie shorthand → merged durations (@tie)
```

## v4/v3 carry-overs (still valid in v5, deprecated elsewhere)

```text
[C4 D4 E4 F4 G4] (5:4)       // polyrhythm: 5 steps over 4 beats
CH0 3:2 C4|E4 e              // shorthand polyrhythm (a:b, pipe = chord)
E(5,4)  or  [C4 E4 G4] E(5,4)  // Euclidean rhythm: 5 pulses over 4 steps
ritard(2 bars)->100          // ritardando → @bpm
C4 q                         // v3 shorthand note; !name = body / !name macros
?0.8 T0 N60 D500 V80         // probability gate (random); x4 = repeat suffix
chord(I) chord(V7)           // roman numerals, key-aware via @key
N60-72                       // random note range
```

## Version detection

`detect_syntax_version` checks v5 markers first (`pedal on/off`, `rest`,
`t3(`, `@oct:`, `@art:`, `@tie`, `~` ties, `print/assert/include`, `prog(`,
`perc(`, `!fn`, `pick(/rand(`, `scale(/run(`, list/range loops,
break/continue), then v4/v3/v2/v1 markers, else defaults to v5. Deprecation
banner once per version. Convert: `run.py compile <old.e> --to v5`.

## Event dict (all parsers produce these)

```python
{"timestamp": int_ms, "midi": 0..127, "duration": int_ms,
 "velocity": 0..127, "pan": -1.0..1.0, "bend": -64..64}
# optional: channel track sustain pedal art tie octave
#           master_vol gain_db filter_* env_* phase cents swing strum
```
