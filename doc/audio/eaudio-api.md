**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [eaudio-api](eaudio-api.md) | [spatial-audio](spatial-audio.md) | [dsp-effects](dsp-effects.md) | [device-management](device-management.md)

## EAudio API

EAudio (v1.0.0) is the low-level **audio API** driver: device
enumeration, PCM buffer management, 3D spatial positioning and DSP
effects. It is an API for building audio engines on — not a player.

### Driver status

```
eaudio status        # device count, default output, sample rate
eaudio devices       # every device: index, channels, sample rate
eaudio info          # the four sub-APIs and their state
```

### Sub-APIs

- **AudioDeviceAPI** — device enumeration, selection, format negotiation
- **AudioBufferAPI** — PCM buffer management, streaming, ring buffers
- **SpatialAudioAPI** — 3D positioning, velocity, doppler, attenuation
- **AudioEffectsAPI** — reverb, EQ, compressor, delay, convolution reverb

### Dependencies & fallback

- Requires Radical (GPU context may be used for audio DSP compute
  shaders); `pip install pygame` for the basic backend or
  `python-sounddevice` for the advanced one
- When no audio backend is available the plugin reports
  `eaudio: unavailable` at boot and still registers the command

---

**HELLFORGE OS v0.1.14.41-beta** — EAudio API