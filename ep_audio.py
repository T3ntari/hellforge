"""
E Audio Driver System — Device enumeration, selection, format handling.
Supports WASAPI, DirectSound, MME, WDM-KS on Windows via pygame/SDL.
Audio encoding/decoding via ffmpeg with format negotiation.
"""

import os
import re
import subprocess
import sys
import json
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()

# ── Color helpers (same as ep_core) ──────────

R_ = "\033[0m"; B_ = "\033[1m"; D_ = "\033[2m"
RED_ = "\033[91m"; GREEN_ = "\033[92m"; YELLOW_ = "\033[93m"
CYAN_ = "\033[96m"; GREY_ = "\033[90m"

def c(text, color=""):
    return f"{color}{text}{R_}" if color and sys.stdout.isatty() else text


# ── Audio Device Database ────────────────────

class AudioDevice:
    """Represents a single audio output device."""
    def __init__(self, idx, name, driver="Unknown", channels=2, default=False,
                 sample_rates=None, latency=None):
        self.idx = idx
        self.name = name
        self.driver = driver
        self.channels = channels
        self.default = default
        self.sample_rates = sample_rates or [44100, 48000, 96000]
        self.latency = latency  # ms

    def __repr__(self):
        return f"<AudioDevice #{self.idx}: {self.name} [{self.driver}]>"


class AudioFormat:
    """Audio format specification."""
    def __init__(self, sample_rate=44100, bit_depth=16, channels=2, encoding="pcm"):
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth
        self.channels = channels
        self.encoding = encoding  # pcm, float, aac, mp3, flac

    def __repr__(self):
        return f"{self.sample_rate}Hz/{self.bit_depth}bit/{self.channels}ch/{self.encoding}"


# ── Device Detection ─────────────────────────

def detect_devices(force_refresh=False):
    """Detect available audio output devices via pygame/SDL."""
    devices = []
    try:
        import pygame
        import pygame.midi
        pygame.midi.init()
        for i in range(pygame.midi.get_count()):
            info = pygame.midi.get_device_info(i)
            name = info[1].decode() if isinstance(info[1], bytes) else str(info[1])
            is_output = info[3]
            is_default = info[4]
            if is_output:
                devices.append(AudioDevice(
                    idx=i, name=name, driver="MIDI",
                    channels=16, default=is_default,
                    latency=info[2] if len(info) > 2 else None
                ))
        pygame.midi.quit()
    except Exception:
        pass

    # Add fallback devices if none found
    if not devices:
        devices.append(AudioDevice(0, "Microsoft GS Wavetable Synth", "MIDI", 16, True))
        if os.name == "nt":
            devices.append(AudioDevice(1, "Default MME Device", "MME", 2))
            devices.append(AudioDevice(2, "Default DirectSound", "DirectSound", 2))
            devices.append(AudioDevice(3, "Default WASAPI", "WASAPI", 2))

    return devices


def detect_host_apis():
    """Detect available audio host APIs."""
    apis = []
    if os.name == "nt":
        apis = ["MME", "DirectSound", "WASAPI", "WDM-KS", "ASIO"]
    else:
        apis = ["ALSA", "PulseAudio", "JACK", "OSS", "CoreAudio"]
    # Check what's actually available via pygame
    try:
        import pygame
        try:
            count = pygame.mixer.get_num_channels()
            apis.insert(0, "SDL (default)")
        except Exception:
            pass
    except Exception:
        pass
    return apis


# ── Format Conversion ────────────────────────

def ffmpeg_available():
    """Check if ffmpeg is available for format conversion."""
    try:
        r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10)
        return r.returncode == 0
    except Exception:
        return False


def convert_audio_format(input_path, output_path, target_format=None, sample_rate=None,
                         bit_depth=None, channels=None, bitrate="320k"):
    """Convert audio between formats using ffmpeg with full control."""
    if not ffmpeg_available():
        return False, "ffmpeg not available"

    target = target_format or os.path.splitext(output_path)[1].lstrip(".")
    if not target:
        target = "wav"

    cmd = ["ffmpeg", "-y", "-i", input_path]

    # Sample rate
    if sample_rate:
        cmd.extend(["-ar", str(sample_rate)])
    # Bit depth (for PCM formats)
    if bit_depth and target in ("wav", "aiff"):
        cmd.extend(["-sample_fmt", f"s{bit_depth}" if bit_depth <= 16 else "s32"])
    # Channels
    if channels:
        cmd.extend(["-ac", str(channels)])
    # Quality
    if target == "mp3":
        cmd.extend(["-codec:a", "libmp3lame", "-b:a", bitrate, "-q:a", "0"])
    elif target == "aac":
        cmd.extend(["-codec:a", "aac", "-b:a", bitrate])
    elif target == "flac":
        cmd.extend(["-codec:a", "flac", "-compression_level", "8"])
    elif target == "ogg":
        cmd.extend(["-codec:a", "libvorbis", "-q:a", "5"])
    elif target == "wav":
        cmd.extend(["-f", "wav"])

    cmd.append(output_path)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        if r.returncode == 0:
            sr = sample_rate or 44100
        bd = bit_depth or 16
        ch = channels or 2
        return True, f"Converted to {target} ({sr}Hz/{bd}bit/{ch}ch)"
        return False, r.stderr[:200]
    except Exception as e:
        return False, str(e)


def probe_audio_file(path):
    """Probe audio file metadata using ffprobe."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", path],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        )
        if r.returncode != 0:
            return {}
        data = json.loads(r.stdout)
        info = {}
        fmt = data.get("format", {})
        info["duration"] = float(fmt.get("duration", 0))
        info["size"] = int(fmt.get("size", 0))
        info["bitrate"] = int(fmt.get("bit_rate", 0))
        streams = data.get("streams", [])
        for s in streams:
            if s.get("codec_type") == "audio":
                info["sample_rate"] = int(s.get("sample_rate", 0))
                info["channels"] = int(s.get("channels", 0))
                info["codec"] = s.get("codec_name", "?")
                info["bit_depth"] = int(s.get("bits_per_sample", 16))
                break
        return info
    except Exception:
        return {}


# ── Audio Processing ─────────────────────────

def apply_audio_effects(input_path, output_path, effects=None):
    """Apply audio processing effects via ffmpeg filter graph."""
    if not ffmpeg_available():
        return False, "ffmpeg not available"
    if not effects:
        return False, "no effects specified"

    cmd = ["ffmpeg", "-y", "-i", input_path]
    filters = []

    if "volume" in effects:
        filters.append(f"volume={effects['volume']}")
    if "bass" in effects:
        filters.append(f"equalizer=f=100:t=q:w=1:g={effects['bass']}")
    if "treble" in effects:
        filters.append(f"equalizer=f=10000:t=q:w=1:g={effects['treble']}")
    if "speed" in effects:
        filters.append(f"atempo={effects['speed']}")
    if "pitch" in effects:
        filters.append(f"asetrate={effects['pitch']}*44100,aresample=44100")
    if "reverb" in effects:
        filters.append("aecho=0.8:0.88:60:0.4")
    if "normalize" in effects:
        filters.append("loudnorm=I=-16:LRA=11:TP=-1.5")
    if "fade_in" in effects:
        filters.append(f"afade=t=in:d={effects['fade_in']}")
    if "fade_out" in effects:
        filters.append(f"afade=t=out:d={effects['fade_out']}")
    if "trim_start" in effects:
        filters.append(f"atrim=start={effects['trim_start']}")
    if "trim_end" in effects:
        filters.append(f"atrim=end={effects['trim_end']}")

    if filters:
        cmd.extend(["-af", ",".join(filters)])
    cmd.append(output_path)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
        return r.returncode == 0, r.stderr[:200] if r.returncode else "OK"
    except Exception as e:
        return False, str(e)


# ── Audio Driver Configuration ───────────────

class AudioConfig:
    """Persistent audio configuration."""
    def __init__(self):
        self.config_path = PROJECT_DIR / "audio_config.json"
        self.data = self._load()

    def _load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "device_id": None,
            "sample_rate": 44100,
            "bit_depth": 16,
            "channels": 2,
            "buffer_size": 2048,
            "latency": "low",
            "driver": "auto",
            "volume": 0.7,
        }

    def save(self):
        with open(self.config_path, "w") as f:
            json.dump(self.data, f, indent=2)
        print(f"  > {c('Audio config saved', GREEN)}")

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value):
        self.data[key] = value
        self.save()

    def apply_to_player(self):
        """Returns pygame mixer init kwargs from config."""
        kwargs = {
            "frequency": self.get("sample_rate", 44100),
            "size": -16 if self.get("bit_depth", 16) <= 16 else -32,
            "channels": self.get("channels", 2),
            "buffer": self.get("buffer_size", 2048),
        }
        return kwargs

    def format_summary(self):
        """Return a formatted string of current config."""
        sr = self.get("sample_rate", 44100)
        bd = self.get("bit_depth", 16)
        ch = self.get("channels", 2)
        dev = self.get("device_id", "default")
        return f"{sr}Hz/{bd}bit/{ch}ch (device #{dev})"


audio_config = AudioConfig()


def list_devices_table():
    """Print a formatted table of detected audio devices."""
    devices = detect_devices()
    if not devices:
        print(f"  {c('No audio devices detected', YELLOW)}")
        return devices
    print(f"  {c('Available Audio Devices:', B_)}")
    for d in devices:
        default_tag = c(" [default]", GREEN_) if d.default else ""
        print(f"    #{d.idx}  {c(d.name, CYAN_)}  {c(f'({d.driver}, {d.channels}ch)', GREY_)}{default_tag}")
    return devices


def set_device(device_id):
    """Set active audio device by index."""
    devices = detect_devices()
    for d in devices:
        if d.idx == device_id:
            audio_config.set("device_id", device_id)
            audio_config.set("driver", d.driver)
            print(f"  > {c('Audio device set:', GREEN)} #{d.idx} {d.name}")
            return True
    print(f"  {c(f'Device #{device_id} not found', RED)}")
    return False
