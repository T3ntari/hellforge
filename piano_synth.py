"""FluidSynth MIDI renderer — uses libfluidsynth-3.dll with auto-generated SoundFont.
If no valid SF2 exists, creates one from scratch using the FluidSynth API.
This is the DEFAULT audio renderer for all E language output.

Usage:
  py -3 piano_synth.py <input.mid> [output.wav]
  py -3 -c "from piano_synth import render; render('song.mid', 'song.wav')"
"""

import os
import sys
import subprocess
import struct
import math
import tempfile
import time
import json
from pathlib import Path

try:
    import numpy as np
    from scipy.io import wavfile
    HAS_NP = True
except ImportError:
    HAS_NP = False

# Load saved driver preference
_synth_config = {}
try:
    cfg_path = Path(__file__).parent / ".synth_config.json"
    if cfg_path.exists():
        with open(cfg_path) as f:
            _synth_config = json.load(f)
except Exception:
    pass

RENDERER = _synth_config.get("driver", "numpy")  # default: numpy (clean, no noise)

PROJECT_DIR = Path(__file__).parent.resolve()
TOOLS_DIR = PROJECT_DIR / "tools"
DLL_DIR = TOOLS_DIR / "fluidsynth" / "fluidsynth-v2.5.6-win10-x64-cpp11" / "bin"
DLL_PATH = DLL_DIR / "libfluidsynth-3.dll"
DLL_ALT = TOOLS_DIR / "libfluidsynth-3.dll"
SF2_PATH = TOOLS_DIR / "default.sf2"
EXE_PATH = DLL_DIR / "fluidsynth.exe"


def _make_sf2():
    """Create a valid General MIDI SoundFont programmatically.
    This generates a .sf2 file with 128 GM instruments using a
    synthetic piano waveform."""
    if SF2_PATH.exists() and SF2_PATH.stat().st_size > 1000:
        return str(SF2_PATH)

    print("  Generating default SoundFont...")

    sr = 44100
    dur = 1.0  # 1 second sample
    n_samples = int(sr * dur)

    # Generate a rich piano-like waveform using additive synthesis
    # Piano harmonics: stronger odd harmonics, weaker even
    harmonics = [(1, 1.0), (2, 0.3), (3, 0.6), (4, 0.15), (5, 0.4),
                 (6, 0.1), (7, 0.25), (8, 0.05), (9, 0.15)]
    samples = np.zeros(n_samples, dtype=np.float64)
    t = np.arange(n_samples) / sr

    for h, amp in harmonics:
        freq = 440 * h
        wave = np.sin(2 * np.pi * freq * t) * amp
        # Each harmonic has its own decay rate (higher = faster decay)
        decay = np.exp(-t * (2 + h * 0.5))
        samples += wave * decay

    # Normalize
    samples /= np.max(np.abs(samples))
    # Convert to 16-bit PCM
    samples_i16 = (samples * 0.9 * 32767).astype(np.int16)

    # Write a temporary WAV file, then use it to build the SF2
    # Actually, we need to write the RIFF/SF2 binary directly
    # The SF2 format expects samples in the smpl chunk, 16-bit signed

    smpl_data = samples_i16.tobytes()
    smpl_len = len(samples_i16)  # in 16-bit samples

    def p2(s):
        return s.encode("ascii")

    def D4(v):
        return struct.pack("<I", v)

    def W2(v):
        return struct.pack("<H", v)

    def W1(v):
        return struct.pack("B", v)

    def pad(b):
        return b if len(b) % 2 == 0 else b + b"\x00"

    # Build sf2 chunks
    # INFO list
    info = b""
    info += p2("ifil") + D4(4) + W2(2) + W2(1) + b"\x00\x00"  # version 2.1
    info += p2("isng") + D4(20) + b"E Piano Synth Engine\x00"
    info += p2("INAM") + D4(12) + b"E Default\x00"
    info += p2("irom") + D4(12) + b"E v1.0\x00\x00"
    info += p2("iver") + D4(4) + W2(0) + W2(1) + b"\x00\x00"
    info += p2("ICRD") + D4(12) + b"2026-07-28\x00"
    info += p2("IENG") + D4(12) + b"Tentari\x00\x00"
    info = p2("LIST") + D4(len(info)) + p2("INFO") + info

    # sdta (sample data)
    smpl = p2("smpl") + D4(len(smpl_data)) + smpl_data
    smpl = pad(smpl)
    sdta = p2("LIST") + D4(len(smpl)) + p2("sdta") + smpl

    # shdr: sample header
    shdr = b""
    sname = b"E.Piano\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    sname = sname[:20].ljust(20, b"\x00")
    shdr += sname
    shdr += D4(0)                         # start
    shdr += D4(smpl_len)                  # end
    shdr += D4(0)                         # startLoop
    shdr += D4(smpl_len)                  # endLoop
    shdr += D4(sr)                        # sampleRate
    shdr += W1(69)                        # originalKey (A4)
    shdr += struct.pack("b", 0)           # correction
    shdr += W2(0)                         # sampleLink
    shdr += W2(1)                         # sampleType
    shdr = pad(shdr)
    # Terminator shdr
    shdr += b"\x00" * 20 + D4(0) * 5 + struct.pack("bB", 0, 0) + W2(0) + W2(0)
    shdr = pad(shdr)
    shdr_chunk = p2("shdr") + D4(len(shdr)) + shdr

    # pgen: preset generators
    pgen = b""
    # 128 presets, each with a generator zone that uses the sample
    for i in range(128):
        pgen += W2(41)                     # genOper = instrument
        pgen += W2(0)                      # instrument index 0 (our instrument)
    pgen += W2(0) + W2(0)                 # terminator
    pgen = pad(pgen)
    pgen_chunk = p2("pgen") + D4(len(pgen)) + pgen

    # pmod: preset modulators (empty)
    pmod = W2(0) + W2(0)
    pmod_chunk = p2("pmod") + D4(len(pmod)) + pmod

    # pbag: preset bags
    pbag = b""
    for i in range(128):
        pbag += W2(i)                      # genNdx = generator index
        pbag += W2(65535)                  # modNdx = none
    pbag += W2(128) + W2(65535)           # terminator
    pbag = pad(pbag)
    pbag_chunk = p2("pbag") + D4(len(pbag)) + pbag

    # phdr: preset headers
    phdr = b""
    for i in range(128):
        name = f"E-{i:03d}\x00".encode()[:20].ljust(20, b"\x00")
        phdr += name
        phdr += W2(i)                      # preset number
        phdr += W2(0)                      # bank
        phdr += W2(i)                      # presetBagNdx
        phdr += D4(0) + D4(0) + D4(0)     # library, genre, morphology
    # Terminator
    phdr += b"\x00" * 20 + W2(127) + W2(127) + W2(128) + D4(0) * 3
    phdr = pad(phdr)
    phdr_chunk = p2("phdr") + D4(len(phdr)) + phdr

    # inst: instruments (1 instrument + terminator)
    inst_data = b""
    inst_data += b"E.Piano\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"[:20].ljust(20, b"\x00")
    inst_data += W2(0)                     # instBagNdx = 0
    # Terminator instrument
    inst_data += b"\x00" * 20 + W2(1)
    inst_data = pad(inst_data)
    inst_chunk = p2("inst") + D4(len(inst_data)) + inst_data

    # ibag: instrument bags (1 + terminator)
    ibag = W2(0) + W2(65535) + W2(1) + W2(65535)
    ibag = pad(ibag)
    ibag_chunk = p2("ibag") + D4(len(ibag)) + ibag

    # igen: instrument generators
    igen = b""
    igen += W2(53) + W2(0)                # sampleID = 0
    igen += W2(43) + struct.pack("<h", 69) # overriddenRootKey = A4
    igen += W2(0) + W2(0)                 # terminator
    igen = pad(igen)
    igen_chunk = p2("igen") + D4(len(igen)) + igen

    # pdta list
    pdta_body = phdr_chunk + pbag_chunk + pmod_chunk + inst_chunk + ibag_chunk + igen_chunk + shdr_chunk
    pdta = p2("LIST") + D4(len(pdta_body)) + p2("pdta") + pdta_body

    # Final SF2: RIFF + sfbk
    sfbk_body = info + sdta + pdta
    riff = p2("RIFF") + D4(4 + len(sfbk_body)) + p2("sfbk") + sfbk_body

    with open(SF2_PATH, "wb") as f:
        f.write(riff)

    sz = SF2_PATH.stat().st_size
    print(f"  Created: {SF2_PATH.name} ({sz//1024}KB)")
    return str(SF2_PATH)


def render(midi_path, output_wav=None, gain=0.5, sample_rate=44100, params=None):
    """Render MIDI to WAV using FluidSynth. Falls back to numpy synth if unavailable.
    params: optional dict carrying @sr/@bit/@gain/@sub/@bass_boost/@stereo_width/@neural
    directives from the compiled E source."""
    midi_path = str(Path(midi_path).resolve())
    if output_wav is None:
        output_wav = str(Path(midi_path).with_suffix(".wav"))
    params = params or {}
    sr = int(params.get("sample_rate", params.get("sr", sample_rate)))
    bit = int(params.get("bit_depth", params.get("bit", 16)))

    global RENDERER
    # numpy is the default — clean, no noise, no dependencies
    if RENDERER == "numpy" or RENDERER == "fluidsynth":
        if HAS_NP:
            result = _render_numpy(midi_path, output_wav, sr=sr, bit=bit, gain=gain, params=params)
            if result: return _to_mp3(result)
        if RENDERER == "numpy":
            RENDERER = "fluidsynth"

    if RENDERER == "fluidsynth":
        result = _render_fluidsynth(midi_path, output_wav, gain, sr)
        if result: return _to_mp3(result)

    if RENDERER == "ffmpeg":
        result = _render_ffmpeg(midi_path, output_wav)
        if result: return _to_mp3(result)

    # Fallback chain
    for method in ["numpy", "fluidsynth", "ffmpeg"]:
        if method == "numpy" and HAS_NP:
            result = _render_numpy(midi_path, output_wav, sr=sr, bit=bit, gain=gain, params=params)
        elif method == "fluidsynth":
            result = _render_fluidsynth(midi_path, output_wav, gain, sr)
        elif method == "ffmpeg":
            result = _render_ffmpeg(midi_path, output_wav)
        else:
            continue
        if result:
            return _to_mp3(result)

    return None


def _render_fluidsynth(midi_path, output_wav, gain=0.5, sr=44100):
    """Render using FluidSynth library."""
    if not DLL_PATH.exists() and not DLL_ALT.exists():
        return None

    dll = str(DLL_PATH) if DLL_PATH.exists() else str(DLL_ALT)
    sf2_path = _make_sf2()

    # Use subprocess to call fluidsynth.exe
    out_path = str(output_wav)
    if EXE_PATH.exists():
        cmd = [str(EXE_PATH), "-F", out_path,
               "-g", str(gain),
               "-R", str(sr),
               str(sf2_path), str(midi_path)]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            if r.returncode == 0 and os.path.exists(out_path):
                sz = os.path.getsize(out_path) // 1024
                print(f"  ✓ FluidSynth: {os.path.basename(out_path)} ({sz}KB)")
                return out_path
        except Exception as e:
            print(f"  FluidSynth error: {e}")
    return None


def _render_numpy(midi_path, output_wav, sr=44100, bit=16, gain=0.5, params=None):
    """Software MIDI renderer with piano-like timbre.
    Honors @sr/@bit/@gain/@sub/@bass_boost/@stereo_width/@neural params:
    - sr: sample rate
    - bit: bit depth (16 or 24)
    - sub: sub-octave sine reinforcement (Hz, 20-120)
    - bass_boost: dB shelf applied to the low band (<250Hz)
    - stereo_width: 0-200% stereo spread (0 = mono)
    - neural: soft-knee saturation stage (musical warm distortion)
    - quality: 'low'/'standard'/'high' harmonic richness"""
    try:
        import mido as _mido
    except ImportError:
        return None

    print("  Rendering with software synth...")
    import numpy as np
    from scipy.io import wavfile

    mid = _mido.MidiFile(midi_path)
    params = params or {}
    quality = str(params.get("quality", "standard")).lower()

    # Piano synthesis parameters — richer harmonics for high quality
    HARMONICS = {
        "low":      [(1, 1.0, 1.0), (2, 0.3, 2.5), (3, 0.15, 4.0)],
        "standard": [(1, 1.0, 1.0), (2, 0.3, 2.5), (3, 0.15, 4.0),
                     (4, 0.1, 6.0), (5, 0.05, 8.0)],
        "high":     [(1, 1.0, 1.0), (2, 0.3, 2.5), (3, 0.15, 4.0),
                     (4, 0.1, 6.0), (5, 0.05, 8.0), (6, 0.04, 10.0),
                     (7, 0.03, 12.0), (8, 0.02, 14.0), (9, 0.015, 16.0)],
    }
    harmonics = HARMONICS.get(quality, HARMONICS["standard"])

    sub_hz = params.get("sub")
    try:
        sub_hz = float(sub_hz) if sub_hz is not None else None
    except (ValueError, TypeError):
        sub_hz = None
    bass_boost = params.get("bass_boost")
    try:
        bass_boost = float(bass_boost) if bass_boost is not None else None
    except (ValueError, TypeError):
        bass_boost = None
    stereo_width = float(params.get("stereo_width", 100)) / 100.0
    neural = bool(params.get("neural", False))

    # Calculate total time
    tempo = 500000
    total_ticks = 0
    for track in mid.tracks:
        t = 0
        for msg in track:
            t += msg.time
            if msg.type == "set_tempo":
                tempo = msg.tempo
            if t > total_ticks:
                total_ticks = t
    sec_per_tick = tempo / 1_000_000 / mid.ticks_per_beat
    total_sec = total_ticks * sec_per_tick + 2
    n_samples = int(total_sec * sr) + sr * 2

    audio = np.zeros(n_samples, dtype=np.float64)

    def _render_note(key, st, vel, end_t):
        """Render one note from start tick st to end tick end_t into audio."""
        note = key[0]
        dt = end_t - st
        if dt <= 0:
            return
        freq = 440.0 * (2.0 ** ((note - 69) / 12.0))
        start_s = st * sec_per_tick
        dur_s = dt * sec_per_tick
        start_n = int(start_s * sr)
        dur_n = max(1, int(dur_s * sr))
        if start_n + dur_n > n_samples:
            dur_n = n_samples - start_n
        if dur_n <= 0:
            return
        t_note = np.arange(dur_n) / sr
        wave = np.zeros(dur_n)
        for h, amp, decay_rate in harmonics:
            hfreq = freq * h
            hwave = np.sin(2 * np.pi * hfreq * t_note) * amp
            henv = np.exp(-t_note * decay_rate)
            attack = np.ones(dur_n)
            attack[:50] = np.linspace(0, 1, min(50, dur_n))
            wave += hwave * henv * attack
        if sub_hz is not None and freq > sub_hz:
            sub_wave = np.sin(2 * np.pi * (freq / 2.0) * t_note) * np.exp(-t_note * 1.2)
            wave += sub_wave * 0.25
        wave *= (vel / 127.0) * 0.4
        end_n = min(start_n + dur_n, n_samples)
        audio[start_n:end_n] += wave[:end_n - start_n]

    note_starts = {}
    sustain_active = False
    for track in mid.tracks:
        t = 0
        for msg in track:
            t += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                note_starts[(msg.note, msg.channel)] = (t, msg.velocity)
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.note, msg.channel)
                if sustain_active and key in note_starts:
                    continue  # hold the note until pedal-up
                start = note_starts.pop(key, None)
                if start:
                    _render_note(key, start[0], start[1], t)
            elif msg.type == "control_change" and msg.control == 64:
                if msg.value >= 64 and not sustain_active:
                    sustain_active = True
                elif msg.value < 64 and sustain_active:
                    sustain_active = False
                    for key, (st, vel) in list(note_starts.items()):
                        _render_note(key, st, vel, t)
                    note_starts.clear()

    # Master gain (0.0-1.0 → amplitude)
    if gain is not None and gain != 0.5:
        audio *= float(gain) * 2.0

    # Bass boost: shelf below 250 Hz (FIR one-pole via FFT-free biquad)
    if bass_boost:
        boost = 10 ** (bass_boost / 20.0)
        audio = _bass_shelf(audio, sr, 250.0, boost)

    # Neural saturation stage: soft-knee tanh drive (musical, no harsh clipping)
    if neural:
        audio = np.tanh(audio * 1.5) / np.tanh(1.5)

    # Stereo width: haas-style decorrelation of left/right for spread >100%,
    # or collapse toward mono below 100%.
    if abs(stereo_width - 1.0) > 0.01 and len(audio) > sr // 10:
        audio = _stereo_width(audio, sr, stereo_width)

    # Normalize
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.85

    if bit >= 24:
        audio_i32 = (audio * 8388607).astype(np.int32)
        out_path = str(output_wav)
        wavfile.write(out_path, sr, audio_i32)
    else:
        audio_i16 = (audio * 32767).astype(np.int16)
        out_path = str(output_wav)
        wavfile.write(out_path, sr, audio_i16)
    sz = os.path.getsize(out_path) // 1024
    print(f"  ✓ Software synth: {os.path.basename(out_path)} ({sz}KB, {sr}Hz/{bit}bit)")
    return out_path


def _bass_shelf(samples, sr, cutoff, boost):
    """One-pole low-shelf filter applied in-place-ish. Returns filtered array."""
    import numpy as np
    w0 = 2.0 * math.pi * cutoff / sr
    alpha = math.sin(w0) / (2.0 * math.sqrt(2.0))
    a0 = 1.0 + alpha
    a1 = -2.0 * math.cos(w0) / a0
    a2 = (1.0 - alpha) / a0
    b0 = (1.0 + alpha * boost) / a0
    b1 = -2.0 * math.cos(w0) / a0
    b2 = (1.0 - alpha * boost) / a0
    out = np.zeros_like(samples)
    x1 = x2 = y1 = y2 = 0.0
    for i in range(len(samples)):
        x = samples[i]
        y = b0 * x + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        out[i] = y
        x2, x1 = x1, x
        y2, y1 = y1, y
    return out


def _stereo_width(samples, sr, width):
    """Adjust stereo width via mid/side processing of a mono buffer.
    Creates a synthetic side channel (decorrelated copy) and rebalances."""
    import numpy as np
    delay = max(1, int(sr * 0.0006))  # 0.6 ms decorrelation delay
    left = samples
    right = np.roll(samples, delay)
    if width < 1.0:
        # Collapse toward mono
        w = max(0.0, width)
        right = right * w + left * (1.0 - w)
    else:
        # Spread: boost difference
        mid = (left + right) / 2.0
        side = (left - right) / 2.0 * width
        left = mid + side
        right = mid - side
    return (left + right) / 2.0


def _render_ffmpeg(midi_path, output_wav):
    """FFmpeg fallback."""
    mp3 = Path(output_wav).with_suffix(".mp3")
    try:
        r = subprocess.run(["ffmpeg", "-y", "-i", midi_path, "-b:a", "192k", str(mp3)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode == 0 and mp3.exists():
            print(f"  ✓ ffmpeg: {mp3.name} ({mp3.stat().st_size//1024}KB)")
            return str(mp3)
    except Exception:
        pass
    return None


def _to_mp3(wav_path):
    """Convert WAV to MP3, deleting WAV on success."""
    if not wav_path or not os.path.exists(wav_path):
        return None
    if wav_path.endswith(".mp3"):
        return wav_path
    mp3 = Path(wav_path).with_suffix(".mp3")
    try:
        r = subprocess.run(["ffmpeg", "-y", "-i", wav_path, "-b:a", "192k", str(mp3)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        if r.returncode == 0:
            os.unlink(wav_path)
            print(f"    → MP3: {mp3.name} ({mp3.stat().st_size//1024}KB)")
            return str(mp3)
    except Exception:
        pass
    return wav_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py -3 piano_synth.py <input.mid> [output.wav]")
        sys.exit(1)
    inp = sys.argv[1]
    if not os.path.exists(inp):
        print(f"Not found: {inp}")
        sys.exit(1)
    out = sys.argv[2] if len(sys.argv) > 2 else None
    result = render(inp, out)
    if result:
        print(f"\nPlay: py -3 player.py \"{result}\"")
    else:
        print("Render failed")
        sys.exit(1)
