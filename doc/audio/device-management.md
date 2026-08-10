**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [eaudio-api](eaudio-api.md) | [spatial-audio](spatial-audio.md) | [dsp-effects](dsp-effects.md) | [device-management](device-management.md)

## Device Management

EAudio auto-selects the default system audio device.

### Device enumeration

```
eaudio devices
```

Lists every available device with index, channel count and sample rate,
plus the default output and default sample rate. `eaudio status` shows the
active default output.

### Backends

The basic backend uses `pygame`; the advanced backend uses
`python-sounddevice` (WASAPI / CoreAudio / ALSA / JACK via the platform
stack). When no backend is present the driver reports
`eaudio: unavailable` at boot with a diagnostic.

### Format negotiation

The device API exposes each device's channel count and supported sample
rate; selection negotiates the closest match.

---

**HELLFORGE OS v0.1.14.41-beta** — device management