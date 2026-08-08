"""EAudio AudioEffectsAPI — reverb, EQ, compressor, delay, convolution."""

import numpy as np


class AudioEffectsAPI:
    """Audio DSP effects for game engines."""

    def __init__(self, device_api):
        self.device = device_api

    def reverb(self, buffer, decay=0.5, delay_ms=30):
        """Simple Schroeder reverb."""
        data = buffer["data"].copy()
        sr = buffer["sample_rate"]
        delay_samples = int(sr * delay_ms / 1000)
        wet = np.zeros_like(data)
        if len(data.shape) == 1:
            wet[delay_samples:] = data[:-delay_samples] * decay
        else:
            wet[delay_samples:] = data[:-delay_samples] * decay
        return self._make_buffer(data + wet * 0.3, sr, buffer["channels"])

    def delay(self, buffer, delay_ms=200, feedback=0.4):
        """Delay effect with feedback."""
        data = buffer["data"].copy()
        sr = buffer["sample_rate"]
        delay_samples = int(sr * delay_ms / 1000)
        out = data.copy()
        for i in range(delay_samples, len(data)):
            out[i] += out[i - delay_samples] * feedback
        return self._make_buffer(out, sr, buffer["channels"])

    def compressor(self, buffer, threshold=0.5, ratio=4.0, attack_ms=5, release_ms=50):
        """Dynamic range compressor."""
        data = buffer["data"].copy()
        sr = buffer["sample_rate"]
        attack = int(sr * attack_ms / 1000)
        release = int(sr * release_ms / 1000)
        envelope = np.zeros_like(data)
        level = 0.0
        for i in range(len(data)):
            sample = abs(data[i]) if len(data.shape) == 1 else np.max(np.abs(data[i]))
            if sample > level:
                level += (sample - level) / attack if attack > 0 else sample
            else:
                level += (sample - level) / release if release > 0 else sample
            envelope[i] = level
        gain = np.where(envelope > threshold, threshold + (envelope - threshold) / ratio, envelope)
        gain = gain / (envelope + 1e-10)
        return self._make_buffer(data * gain, sr, buffer["channels"])

    def eq(self, buffer, bass_gain=0.0, mid_gain=0.0, treble_gain=0.0):
        """Simple 3-band EQ."""
        from scipy import signal
        data = buffer["data"].copy()
        sr = buffer["sample_rate"]
        if len(data.shape) == 1:
            data = data.reshape(-1, 1)
        result = np.zeros_like(data)
        for ch in range(data.shape[1]):
            channel = data[:, ch]
            if bass_gain != 0:
                b, a = signal.butter(2, 200 / (sr / 2), btype="low")
                filtered = signal.filtfilt(b, a, channel)
                channel = channel + filtered * (bass_gain - 1)
            if treble_gain != 0:
                b, a = signal.butter(2, 4000 / (sr / 2), btype="high")
                filtered = signal.filtfilt(b, a, channel)
                channel = channel + filtered * (treble_gain - 1)
            result[:, ch] = channel
        return self._make_buffer(result, sr, buffer["channels"])

    def _make_buffer(self, data, sr, ch):
        data = np.clip(data, -1, 1).astype(np.float32)
        return {"data": data, "sample_rate": sr, "channels": ch, "frames": len(data), "duration": len(data) / sr}
