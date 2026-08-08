**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [eaudio-api](audio/eaudio-api.md) | [spatial-audio](audio/spatial-audio.md) | [dsp-effects](audio/dsp-effects.md) | [device-management](audio/device-management.md)

## Device Management

### Device Selection

EAudio auto-selects the default system audio device but allows explicit selection:

```
piano eaudio device set "Focusrite Scarlett 2i2"
piano eaudio device default
```

### Format Negotiation

When opening a stream, EAudio negotiates the optimal format with the device:

| Parameter | Options |
|---|---|
| Sample rate | 44100, 48000, 96000, 192000 |
| Bit depth | 16, 24, 32 (float) |
| Channels | 1 (mono), 2 (stereo), up to 8 |
| Buffer size | 64, 128, 256, 512, 1024 samples |

Devices that do not support the requested format will return the closest match. Use `eaudio device info` to see negotiated parameters.

### Hot-Swap Detection

EAudio monitors for device connection/disconnection events and can trigger callbacks to re-route audio streams automatically.

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**