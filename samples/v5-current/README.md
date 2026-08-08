# v5 samples

v5 is the canonical HELLFORGE syntax — used as the default for every source.
v5 = v4 + piano performance features + the v5 statement set:

| Feature | Example |
|---------|---------|
| Sustain pedal | `pedal on` / `pedal off`, `@pedal:64` |
| Rests | `rest q`, `rest 500ms`, `R e` |
| Articulations | `@art:staccato`, `@art:legato`, `@art:tenuto`, `@art:accent` |
| Tuplets | `t3(C4 E4 G4)`, `trip(...)`, `tup(3,2,C4,E4,G4)` |
| Octave shift | `@oct:+1`, `@oct:-1` |
| Velocity curves | `@curve vel 60 115` (+ `over 4q` windowed) |
| Ties | `C4~ q q`, `@tie` |
| `print` | `print "text"`, `print $var`, `print {expr}`, `print N60` |
| `assert` | `assert $i < 5, "message"` |
| `include` | `include "part.e"` |
| `!fn` macros | `!fn arp(r, d, v) = play note($r) @dur:$d @vel:$v` / `!arp(C4, e, mf)` |
| `prog` | `prog(C:q G:q Am:h F:q)` |
| `perc` | `perc(kick)`, `perc(snare)`, `perc(hihat)` |
| Loops | `for $n in [C4 E4 G4]`, `for $i in 1..8`, `for $n in scale(C major, 4, 1)`, `for $n in run(C4, C5)` + `break`/`continue` |
| `@seed` + `pick`/`rand` | `@seed 42`, `$v = pick(C4 E4 G4)`, `$x = rand(1, 8)` |

`performance_demo.e` exercises the seven piano-performance features;
`pattern_demo.e` exercises the full v5 statement set.
