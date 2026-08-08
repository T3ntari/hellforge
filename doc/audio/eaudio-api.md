**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [eaudio-api](audio/eaudio-api.md) | [spatial-audio](audio/spatial-audio.md) | [dsp-effects](audio/dsp-effects.md) | [device-management](audio/device-management.md)

## EAudio API

EAudio is the audio abstraction layer for Piano DSL, providing device enumeration, buffer management, and stream control.

### Device Enumeration

```
piano eaudio devices
```

Lists all available audio devices with channel count and supported sample rates.

### Buffer Management

- Ring buffers for low-latency streaming
- Pool allocation for effect chain processing
- DMA buffer sharing with GPU compute pipelines
- Automatic buffer size negotiation based on device capabilities

### Stream Control

- `eaudio.stream.open(device, config)` -- Open an audio stream
- `eaudio.stream.start()` -- Begin processing
- `eaudio.stream.stop()` -- Stop processing
- `eaudio.stream.close()` -- Release resources

EAudio supports WASAPI (Windows), CoreAudio (macOS), ALSA (Linux), and JACK.

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**