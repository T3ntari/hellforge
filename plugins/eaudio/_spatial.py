"""EAudio SpatialAudioAPI — 3D audio positioning, velocity, doppler, attenuation."""

import numpy as np


class SpatialAudioAPI:
    """3D spatial audio for game engines."""

    def __init__(self, device_api):
        self.device = device_api
        self.listener_position = np.array([0.0, 0.0, 0.0])
        self.listener_velocity = np.array([0.0, 0.0, 0.0])
        self.listener_forward = np.array([0.0, 0.0, -1.0])
        self.listener_up = np.array([0.0, 1.0, 0.0])
        self.sources = {}

    def set_listener(self, position, velocity=None, forward=None, up=None):
        self.listener_position = np.array(position, dtype=np.float32)
        if velocity is not None:
            self.listener_velocity = np.array(velocity, dtype=np.float32)
        if forward is not None:
            self.listener_forward = np.array(forward, dtype=np.float32)
        if up is not None:
            self.listener_up = np.array(up, dtype=np.float32)

    def add_source(self, source_id, position, velocity=None):
        self.sources[source_id] = {
            "position": np.array(position, dtype=np.float32),
            "velocity": np.array(velocity or [0, 0, 0], dtype=np.float32),
            "buffer": None, "looping": False, "gain": 1.0,
            "max_distance": 50.0, "reference_distance": 5.0, "rolloff": 1.0,
        }

    def set_source_buffer(self, source_id, buffer):
        if source_id in self.sources:
            self.sources[source_id]["buffer"] = buffer

    def update_source(self, source_id, position=None, velocity=None):
        if source_id in self.sources:
            if position is not None:
                self.sources[source_id]["position"] = np.array(position, dtype=np.float32)
            if velocity is not None:
                self.sources[source_id]["velocity"] = np.array(velocity, dtype=np.float32)

    def get_spatial_gain(self, source_id):
        if source_id not in self.sources:
            return None
        src = self.sources[source_id]
        direction = src["position"] - self.listener_position
        distance = np.linalg.norm(direction)
        if distance < 0.001:
            return (src["gain"], src["gain"])
        ref = src["reference_distance"]
        rolloff = src["rolloff"]
        if distance > src["max_distance"]:
            return (0.0, 0.0)
        attenuation = ref / (ref + rolloff * (distance - ref))
        attenuation = max(0.0, min(1.0, attenuation))
        forward = self.listener_forward
        right = np.cross(forward, self.listener_up)
        right = right / (np.linalg.norm(right) + 1e-10)
        pan = np.dot(direction / distance, right)
        pan = max(-1.0, min(1.0, pan))
        lg = src["gain"] * attenuation * (1.0 - max(0.0, pan))
        rg = src["gain"] * attenuation * (1.0 - max(0.0, -pan))
        return (lg, rg)

    def doppler_shift(self, source_id, sample_rate):
        if source_id not in self.sources:
            return sample_rate
        speed = 343.0
        src = self.sources[source_id]
        direction = src["position"] - self.listener_position
        dist = np.linalg.norm(direction)
        if dist < 0.001:
            return sample_rate
        v_rel = np.dot(self.listener_velocity - src["velocity"], direction / dist)
        factor = (speed + v_rel) / (speed + 1e-10)
        return int(sample_rate * max(0.5, min(2.0, factor)))

    def remove_source(self, source_id):
        self.sources.pop(source_id, None)
