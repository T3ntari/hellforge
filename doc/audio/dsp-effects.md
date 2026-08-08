**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [eaudio-api](audio/eaudio-api.md) | [spatial-audio](audio/spatial-audio.md) | [dsp-effects](audio/dsp-effects.md) | [device-management](audio/device-management.md)

## DSP Effects

The DSP engine provides a chainable effects pipeline for real-time audio processing.

### Reverb

- Convolution reverb with IR loading
- Feedback delay network (FDN) reverb
- Configurable decay, diffusion, and pre-delay

### Delay

- Stereo delay with ping-pong mode
- Tempo-synced delay times
- Feedback and lowpass filtering on repeats

### Compressor

- Peak and RMS detection modes
- Threshold, ratio, attack, release controls
- Sidechain input support
- Knee shaping (hard/soft)

### EQ

- Parametric EQ with configurable bands
- Lowpass, highpass, bandpass filters
- Shelving filters (low/high)
- FIR and IIR filter implementations

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**