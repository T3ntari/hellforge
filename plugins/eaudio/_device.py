"""EAudio AudioDeviceAPI — audio device enumeration, selection, format negotiation."""


class AudioDeviceAPI:
    """Audio device management. Uses pygame.midi or sounddevice."""

    def __init__(self):
        self.available = False
        self.diagnostic = ""
        self.devices = []
        self.device_count = 0
        self.default_output = "Unknown"
        self.default_sample_rate = 44100
        self._init()

    def _init(self):
        # Try pygame first
        if self._try_pygame():
            return
        # Try sounddevice
        if self._try_sounddevice():
            return
        # Minimal fallback
        self.devices = [{"index": 0, "name": "Default Output", "channels": 2, "sample_rate": 44100}]
        self.device_count = 1
        self.default_output = "Default Output"
        self.available = True

    def _try_pygame(self):
        try:
            import pygame
            if not pygame.get_init():
                pygame.init()
            if not pygame.midi.get_init():
                pygame.midi.init()
            count = pygame.midi.get_count()
            for i in range(count):
                try:
                    info = pygame.midi.get_device_info(i)
                    name = info[1].decode() if isinstance(info[1], bytes) else str(info[1])
                    is_output = info[3]
                    if is_output:
                        self.devices.append({
                            "index": i, "name": name,
                            "channels": info[2] if len(info) > 2 else 2,
                            "sample_rate": 44100,
                            "driver": "pygame.midi",
                        })
                except Exception:
                    pass
            self.device_count = len(self.devices)
            if self.devices:
                self.default_output = self.devices[0]["name"]
            self.available = True
            self.diagnostic = "pygame.midi"
            return True
        except Exception:
            return False

    def _try_sounddevice(self):
        try:
            import sounddevice as sd
            sd_devices = sd.query_devices()
            for i, dev in enumerate(sd_devices):
                if dev["max_output_channels"] > 0:
                    self.devices.append({
                        "index": i, "name": dev["name"],
                        "channels": dev["max_output_channels"],
                        "sample_rate": int(dev["default_samplerate"] or 44100),
                        "driver": "sounddevice",
                    })
            self.device_count = len(self.devices)
            default = sd.default.device
            if isinstance(default, (list, tuple)):
                default = default[1] if len(default) > 1 else default[0]
            if default is not None and default < len(self.devices):
                self.default_output = self.devices[default]["name"]
            self.default_sample_rate = int(sd.query_devices(default)["default_samplerate"] or 44100)
            self.available = True
            self.diagnostic = "sounddevice"
            return True
        except Exception:
            return False
