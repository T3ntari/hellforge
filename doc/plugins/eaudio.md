# EAudio — Low-Level Audio API

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [eaudio](eaudio.md) | [humanize](humanize.md) | [talisman](talisman.md) | [commands](../commands/eaudio-commands.md)

---

## Overview

**EAudio v1.0.0** (author Tentari) is a low-level **audio API** — not an
audio player. It provides raw audio primitives that game engines and audio
renderers are built on top of. Requires Radical (GPU context may be used
for audio DSP compute shaders); `pip install pygame` (basic) or
`python-sounddevice` (advanced).

## Core primitives

- **Device** — audio device enumeration, selection, format negotiation
- **Buffer** — PCM buffer management, streaming, ring buffers
- **Spatial** — 3D audio positioning, velocity, doppler, attenuation
- **Effects** — reverb, EQ, compressor, delay, convolution reverb

Third-party modders build audio engines ON TOP of this API.

## Commands

`eaudio status|devices|info` — see
[EAudio commands](../commands/eaudio-commands.md). The audio docs cover
[devices](../audio/device-management.md), [spatial audio](../audio/spatial-audio.md),
[DSP effects](../audio/dsp-effects.md) and the [API](../audio/eaudio-api.md).
