# HELLFORGE — EAudio Commands

> Navigation: [doc/index.md](../index.md) | [core-commands](core-commands.md) | [eaudio-commands](eaudio-commands.md)

The **eaudio** plugin (v1.0.0) is a low-level audio **API** — not a player.
It exposes raw primitives (device enumeration, PCM buffers, 3D spatial,
effects) that audio engines are built on top of. The eshell command mirrors
its status:

## eaudio status
**Syntax:** `eaudio status`
**Description:** Show the EAudio API state: device count, default output device, sample rate, or "inactive" with the install hint (`pip install pygame`, or `python-sounddevice` for the advanced backend).
**Example:** `eaudio status`

## eaudio devices
**Syntax:** `eaudio devices`
**Description:** List every audio device with index, channel count and sample rate, plus the default output.
**Example:** `eaudio devices`

## eaudio info
**Syntax:** `eaudio info`
**Description:** Describe the four sub-APIs — AudioDeviceAPI, AudioBufferAPI (PCM buffers, streaming, ring buffers), SpatialAudioAPI (3D positioning, doppler, attenuation), AudioEffectsAPI (reverb, EQ, compressor, delay) — and the active status.
**Example:** `eaudio info`

---

**Plugin:** eaudio · see [EAudio plugin page](../plugins/eaudio.md) and [Audio docs](../audio/eaudio-api.md)
