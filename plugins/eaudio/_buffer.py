"""EAudio AudioBufferAPI — PCM buffer management, streaming, ring buffers."""

import numpy as np


class AudioBufferAPI:
    """Audio buffer creation, mixing, streaming."""

    def __init__(self, device_api):
        self.device = device_api

    def create_buffer(self, samples, sample_rate=None, channels=None):
        """Create an audio buffer from PCM sample data.
        samples: numpy array (samples,) or (samples, channels)
        Returns buffer dict with data, sample_rate, channels, duration."""
        sr = sample_rate or self.device.default_sample_rate
        ch = channels or (samples.shape[1] if len(samples.shape) > 1 else 1)
        arr = np.array(samples, dtype=np.float32)
        duration = len(arr) / sr
        return {
            "data": arr,
            "sample_rate": sr,
            "channels": ch,
            "duration": duration,
            "frames": len(arr),
        }

    def create_sine(self, frequency, duration, sample_rate=None, amplitude=0.5):
        """Generate a sine wave buffer."""
        sr = sample_rate or self.device.default_sample_rate
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        samples = (np.sin(2 * np.pi * frequency * t) * amplitude).astype(np.float32)
        return self.create_buffer(samples, sr, 1)

    def create_silence(self, duration, sample_rate=None, channels=2):
        """Generate a silent buffer."""
        sr = sample_rate or self.device.default_sample_rate
        frames = int(sr * duration)
        samples = np.zeros((frames, channels), dtype=np.float32)
        return self.create_buffer(samples, sr, channels)

    def mix(self, buffers, gain=1.0):
        """Mix multiple buffers together (same sample rate, channels)."""
        if not buffers:
            return None
        max_len = max(len(b["data"]) for b in buffers)
        sr = buffers[0]["sample_rate"]
        ch = buffers[0]["channels"]
        # Normalize all buffers to same shape
        normed = []
        for b in buffers:
            data = b["data"]
            if len(data.shape) == 1:
                data = data.reshape(-1, 1)
            if data.shape[1] == 1 and ch > 1:
                data = np.repeat(data, ch, axis=1)
            elif data.shape[1] > 1 and ch == 1:
                data = data.mean(axis=1, keepdims=True)
            normed.append(data)
        mixed = np.zeros((max_len, ch), dtype=np.float32)
        for data in normed:
            length = min(len(data), max_len)
            mixed[:length] += data[:length]
        mixed = np.clip(mixed, -1, 1) * gain
        if ch == 1:
            mixed = mixed.reshape(-1)
        return self.create_buffer(mixed, sr, ch)

    def resample(self, buffer, target_sample_rate):
        """Resample buffer to a different sample rate."""
        import numpy as np
        data = buffer["data"]
        src_sr = buffer["sample_rate"]
        if src_sr == target_sample_rate:
            return buffer
        ratio = target_sample_rate / src_sr
        new_len = int(len(data) * ratio)
        resampled = np.interp(
            np.linspace(0, len(data) - 1, new_len),
            np.arange(len(data)),
            data,
        ).astype(np.float32)
        return self.create_buffer(resampled, target_sample_rate, buffer["channels"])
