**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [eaudio-api](eaudio-api.md) | [spatial-audio](spatial-audio.md) | [dsp-effects](dsp-effects.md) | [device-management](device-management.md)

## DSP Effects

The **AudioEffectsAPI** (eaudio) provides an effects pipeline for audio
engines built on top of EAudio.

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

### Related

The Humanize driver adds *performance feel* (micro-timing + velocity
expression) at the compile level (`@humanize:nn`) — see
[Humanize](../plugins/humanize.md).

---

**HELLFORGE OS v0.1.14.41-beta** — DSP effects