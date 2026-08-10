**HELLFORGE OS v0.1.14.41-beta**

[Nav: doc/index.md](../index.md) | [eaudio-api](eaudio-api.md) | [spatial-audio](spatial-audio.md) | [dsp-effects](dsp-effects.md) | [device-management](device-management.md)

## Spatial Audio

The **SpatialAudioAPI** (eaudio) provides 3D sound positioning primitives
for E applications.

### Primitives

- 3D audio object placement using listener-relative coordinates
- Velocity for Doppler calculation
- Distance attenuation curves (rolloff models)
- Directional sources (cone/pattern directivity)

### Doppler & attenuation

Doppler shift is calculated from relative velocity between listener and
source. Attenuation follows a configurable rolloff model (linear,
inverse, exponential).

### Culling integration

The Talisman driver can cull/occlude inaudible sources before they reach
the spatial mixer (`talisman on|off`, `talisman local` for local-only
mode) — see [Talisman](../plugins/talisman.md).

---

**HELLFORGE OS v0.1.14.41-beta** — spatial audio