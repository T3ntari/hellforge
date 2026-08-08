# HELLFORGE v1.0.0.0 ALPHA — EAudio Commands

> Navigation: [doc/index.md](../index.md)

## eaudio status
**Syntax:** `eaudio status`
**Description:** Display the current status of the EAudio audio engine, including sample rate, buffer size, audio driver, and playback state.
**Example:** `eaudio status`
**Plugin:** eaudio

## eaudio devices
**Syntax:** `eaudio devices [--list] [--select <name>] [--default]`
**Description:** List available audio output/input devices, select a specific device, or reset to the system default.
**Example:** `eaudio devices --list`
**Plugin:** eaudio

## eaudio info
**Syntax:** `eaudio info [--driver] [--formats] [--latency]`
**Description:** Display detailed audio engine information including driver details, supported sample formats, and measured latency.
**Example:** `eaudio info --latency`
**Plugin:** eaudio

---

**HELLFORGE v1.0.0.0 ALPHA** — *forge your sound*
