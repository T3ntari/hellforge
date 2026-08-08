**HELLFORGE v1.0.0.0 ALPHA**

[Nav: doc/index.md](index.md) | [eaudio-api](audio/eaudio-api.md) | [spatial-audio](audio/spatial-audio.md) | [dsp-effects](audio/dsp-effects.md) | [device-management](audio/device-management.md)

## Spatial Audio

The spatial audio system provides 3D sound positioning for Piano DSL applications.

### Listener

The listener represents the virtual microphone in 3D space:

```
listener.position = [x, y, z]
listener.orientation = [forward_x, forward_y, forward_z, up_x, up_y, up_z]
listener.velocity = [vx, vy, vz]
```

### Sources

Audio sources are positioned relative to the listener:

- `source.position` -- 3D position
- `source.velocity` -- Velocity for Doppler calculation
- `source.directivity` -- Cone/pattern for directional sources
- `source.rolloff` -- Distance attenuation curve

### Doppler and Attenuation

Doppler shift is calculated from relative velocity between listener and source. Attenuation follows a configurable rolloff model (linear, inverse, exponential).

---

**HELLFORGE v1.0.0.0 ALPHA -- Piano DSL Documentation**