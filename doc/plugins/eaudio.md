# **HELLFORGE v1.0.0.0 ALPHA — eaudio: 3D Spatial Audio API**

**Navigation:** [doc/index.md](../index.md) | [overview](overview.md) | [radical](radical.md) | [tensorsharp](tensorsharp.md) | [openapi](openapi.md) | [vulkanizer](vulkanizer.md) | [eaudio](eaudio.md) | [lure](lure.md) | [portbaby](portbaby.md) | [talisman](talisman.md) | [developing-plugins](developing-plugins.md)

---

## Overview

**eaudio** delivers 3D spatial audio through four sub-APIs, backed by a real-time audio engine with <5 ms latency. Supports HRTF-based binaural rendering, Ambisonics, and object-based audio.

## Sub-APIs

### Device (`eaudio.device`)

Audio device enumeration and selection (WASAPI, ALSA, CoreAudio, JACK). Sample rate negotiation, buffer size configuration, and multi-channel output (stereo, 5.1, 7.1, Atmos).

### Buffer (`eaudio.buffer`)

Audio buffer management: PCM, compressed (Opus, Vorbis), procedural generation. Streaming buffers for long audio files and ring buffers for real-time synthesis.

### Spatial (`eaudio.spatial`)

3D audio object placement using listener-relative coordinates. HRTF convolution per source, distance attenuation curves, Doppler shift, and room reverb via IR convolution.

### Effects (`eaudio.effects`)

Per-source effect chain: EQ (parametric, graphic), compressor, limiter, reverb (convolution + algorithmic), delay, chorus, flanger, pitch shifter. Effects stack serializable to DSL.

---

**API Reference:** `#include <eaudio/api.h>`

**HELLFORGE v1.0.0.0 ALPHA — eaudio: 3D Spatial Audio API**
