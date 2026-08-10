# Humanize — MoE De-Robotizer

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [humanize](humanize.md) | [eaudio](eaudio.md) | [talisman](talisman.md)

---

## Overview

**Humanize v1.0.0** (author REGAS) de-robots MIDI with a tiny numpy
Mixture-of-Experts model (~50k params). The `@humanize:nn` directive adds
human micro-timing and expressive velocity to compiled songs.

## Directive

```
@humanize:15        strength 0-100 (default 15)
@humanize           same as @humanize:15
@humanize:0 / off   disable
```

Per-note context (pitch, velocity, bar position, local density, previous
offset/delta) is fed to an 8-expert MoE that predicts timing jitter +
velocity deltas. The model is trained once on a synthetic
human-performance regression task, cached, and runs as instant CPU
inference. It hooks `pre_compile` (scans the directive) and
`post_compile` (applies humanization to the rendered events).

## Commands

```
humanize status           experts, params, weights cache, last train time
humanize retrain          retrain the model
humanize apply <file> [strength]   apply humanization to a file
```

---

See also: [Talisman](talisman.md) (audio culling) · [EAudio](eaudio.md) (audio API)
