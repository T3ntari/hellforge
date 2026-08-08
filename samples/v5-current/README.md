# v5 samples

v5 is the canonical HELLFORGE syntax — used as the default for every source.
v5 = v4 + piano performance features:

| Feature | Example |
|---------|---------|
| Sustain pedal | `pedal on` / `pedal off`, `@pedal:64` |
| Rests | `rest q`, `rest 500ms`, `R e` |
| Articulations | `@art:staccato`, `@art:legato`, `@art:tenuto`, `@art:accent` |
| Tuplets | `t3(C4 E4 G4)`, `trip(...)`, `tup(3,2,C4,E4,G4)` |
| Octave shift | `@oct:+1`, `@oct:-1` |
| Velocity curves | `@curve vel 60 115` (+ `over 4q` windowed) |
| Ties | `C4~ q q`, `@tie` |

`performance_demo.e` exercises all seven.
