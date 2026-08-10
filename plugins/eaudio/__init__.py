"""EAudio v1.0.0 — Low-level Audio API for E.
Not an audio player. Provides raw audio primitives that game engines
and audio renderers are built on top of.

Core primitives:
- Device: audio device enumeration, selection, format negotiation
- Buffer: PCM buffer management, streaming, ring buffers
- Spatial: 3D audio positioning, velocity, doppler, attenuation
- Effects: reverb, EQ, compressor, delay, convolution reverb

Third-party modders build audio engines ON TOP of this API.

Install: pip install pygame (basic), or python-sounddevice (advanced)"""

VERSION = "1.0.0"
author = "Tentari"
description = "Low-level Audio API — device management, buffers, 3D spatial, effects"

_api = None


def register(api):
    api.add_boot_step(f"EAudio v{VERSION}", "loading")
    global _api

    api.require("Radical")  # GPU context may be used for audio DSP compute shaders

    try:
        from ._device import AudioDeviceAPI
        from ._buffer import AudioBufferAPI
        from ._spatial import SpatialAudioAPI
        from ._effects import AudioEffectsAPI

        device_api = AudioDeviceAPI()
        if device_api.available:
            _api = {
                "device": device_api,
                "buffer": AudioBufferAPI(device_api),
                "spatial": SpatialAudioAPI(device_api),
                "effects": AudioEffectsAPI(device_api),
            }
            api.set_config("eaudio_available", True)
            api.add_command("eaudio", _cmd, "EAudio: eaudio status|devices|info")
            api.add_boot_step(f"EAudio: audio API active ({device_api.device_count} devices)", "done")
        else:
            api.set_config("eaudio_available", False)
            api.add_boot_step(f"EAudio: unavailable ({device_api.diagnostic})", "skip")
            api.add_command("eaudio", _cmd, "EAudio: eaudio status|info")
    except Exception as e:
        api.set_config("eaudio_available", False)
        api.add_boot_step(f"EAudio: init failed ({e})", "skip")
        api.add_command("eaudio", _cmd, "EAudio: eaudio status|info")


    api.add_help_section("EAudio (audio)", [
        "eaudio status          Audio engine + devices",
        "eaudio devices         List audio devices",
        "eaudio info            Capabilities",
        "",
        "Spatial audio: device, buffer synthesis, 3D positioning,",
        "doppler, reverb/delay/compressor/EQ effects.",
    ])

def get_api():
    return _api


def _cmd(args):
    if not args or args[0] == "status":
        if _api and _api["device"].available:
            d = _api["device"]
            print(f"  EAudio v{VERSION}")
            print(f"  Devices: {d.device_count}")
            print(f"  Default output: {d.default_output}")
            print(f"  Sample rate: {d.default_sample_rate} Hz")
            print(f"  Game engines can build audio on this API")
        else:
            print(f"  EAudio v{VERSION}")
            print(f"  Status: inactive")
            print(f"  Install: pip install pygame")

    elif args[0] == "devices":
        if _api and _api["device"].available:
            d = _api["device"]
            print(f"  Audio Devices ({d.device_count}):")
            for dev in d.devices:
                print(f"    [{dev['index']}] {dev['name']} ({dev['channels']}ch, {dev['sample_rate']}Hz)")
            print(f"  Default output: {d.default_output}")
            print(f"  Default sample rate: {d.default_sample_rate} Hz")

    elif args[0] == "info":
        print(f"  EAudio v{VERSION} — Low-level Audio API")
        print(f"  Provides raw audio primitives for building audio engines:")
        print(f"    - AudioDeviceAPI: device enum, selection, format")
        print(f"    - AudioBufferAPI: PCM buffers, streaming, ring buffers")
        print(f"    - SpatialAudioAPI: 3D positioning, doppler, attenuation")
        print(f"    - AudioEffectsAPI: reverb, EQ, compressor, delay")
        if _api and _api["device"].available:
            print(f"  API status: active — build your audio engine on top!")
    else:
        print(f"  Usage: eaudio status|devices|info")
