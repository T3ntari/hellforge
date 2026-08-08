# **HELLFORGE v1.0.0.0 ALPHA — talisman: Audio Culling & Privacy**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**talisman** optimizes the audio pipeline through intelligent culling and occlusion, enforces privacy modes, and provides an event inspector for debugging.

## Audio Culling

talisman culls inaudible audio sources before they reach eaudio's spatial mixer:

- **Distance culling** — sources beyond a configurable max distance are skipped
- **Cone-of-hearing** — sources outside the listener's directional cone are attenuated
- **Priority culling** — lowest-priority sources are dropped when voice count exceeds the limit

## Occlusion

Ray-cast occlusion queries against the scene geometry (via openapi or vulkanizer). Occluded sources receive frequency-dependent attenuation (low-pass filter with cutoff proportional to occlusion thickness).

## Privacy Mode

When `@privacy` is active, talisman:

- Disables all audio capture (mic, loopback, system)
- Mutes output to recording devices
- Replaces HRTF with a flat panning curve
- Wipes audio buffer inspection logs

## Event Inspector

talisman exposes a real-time event inspector for audio pipeline debugging:

- Per-source gain, pan, occlusion value
- Effect chain bypass states
- Culling decisions with reason codes
- Latency breakdown (input → processing → output)

---

**API Reference:** `#include <talisman/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — talisman: Audio Culling & Privacy**
