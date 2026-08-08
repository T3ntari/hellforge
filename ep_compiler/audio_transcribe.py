"""Audio-to-MIDI transcription via FFT spectral analysis.
Converts WAV/MP3/MP4/MOV/OGG/FLAC to E language events.

Uses scipy + numpy for spectral processing and pydub for audio loading.
For best results with polyphonic piano, consider basic-pitch (TensorFlow).
"""
import os
import struct
import json

def load_audio(audio_path, sample_rate=44100):
    """Load any audio file to mono numpy array using pydub."""
    try:
        from pydub import AudioSegment
    except ImportError:
        print("Error: pydub required for audio transcription")
        return None, sample_rate
    try:
        audio = AudioSegment.from_file(audio_path)
        audio = audio.set_channels(1).set_frame_rate(sample_rate)
        raw = audio.raw_data
    except Exception as e:
        print(f"  Error loading audio: {e}")
        return None, sample_rate
    import numpy as np
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    return samples, sample_rate


def spectral_flux(samples, sr, hop=512):
    """Compute onset detection function via spectral flux."""
    import numpy as np
    from scipy.signal import (
        get_window,
        spectrogram,
    )
    f, t, Sxx = spectrogram(samples, fs=sr, window=get_window("hann", 2048), nperseg=2048,
                            noverlap=2048 - hop, mode="magnitude")
    flux = np.sqrt(np.sum(np.diff(np.maximum(Sxx, 0), axis=1)**2, axis=0))
    return t[:-1], flux


def detect_onsets(samples, sr, hop=512, threshold=1.5):
    """Detect note onset times."""
    import numpy as np
    t, flux = spectral_flux(samples, sr, hop)
    if len(flux) < 2:
        return []
    mean_f = np.mean(flux)
    std_f = np.std(flux)
    thresh = mean_f + threshold * std_f
    onsets = []
    for i in range(1, len(flux) - 1):
        if flux[i] > thresh and flux[i] > flux[i-1] and flux[i] >= flux[i+1]:
            onsets.append(t[i] * 1000)
    return onsets


def freq_to_midi(freq):
    """Convert frequency in Hz to closest MIDI note number."""
    if freq <= 0:
        return None
    import numpy as np
    midi = 69 + 12 * np.log2(freq / 440.0)
    midi_int = int(round(midi))
    if 0 <= midi_int <= 127:
        return midi_int
    return None


def f0_from_spectrum(magnitude, freqs, min_note=21, max_note=108):
    """Estimate fundamental frequency using spectral peak picking."""
    import numpy as np
    min_freq = 440.0 * (2.0 ** ((min_note - 69) / 12.0))
    max_freq = 440.0 * (2.0 ** ((max_note - 69) / 12.0))
    from scipy.signal import find_peaks
    peaks, props = find_peaks(magnitude, height=np.max(magnitude) * 0.1, distance=3)
    if len(peaks) == 0:
        return None, None
    best_idx = peaks[np.argmax(props["peak_heights"])]
    freq = freqs[best_idx]
    if min_freq <= freq <= max_freq:
        midi = freq_to_midi(freq)
        if midi is not None:
            return freq, midi
    return None, None


def transcribe_audio(audio_path, bpm=120, hop=512, threshold=0.5, sample_rate=44100,
                     min_note=21, max_note=108, note_overlap_ms=30):
    """Transcribe audio file to E events.
    Returns: (events: list[dict], bpm: float)
    """
    import numpy as np
    from scipy.signal import (
        get_window,
        spectrogram,
    )

    samples, sr = load_audio(audio_path, sample_rate)
    if samples is None:
        return [], bpm

    # Compute full spectrogram
    f, t, Sxx = spectrogram(samples, fs=sr, window=get_window("hann", 2048), nperseg=2048,
                            noverlap=2048 - hop, mode="magnitude")
    freqs = f
    events = []

    # Detect onsets for note boundaries
    onset_times = detect_onsets(samples, sr, hop, threshold)
    onset_times = sorted(set(onset_times))

    # Frame-by-frame pitch detection
    frame_notes = {}
    for idx in range(len(t)):
        mag = Sxx[:, idx]
        if np.max(mag) < 0.001:
            continue
        freq, midi = f0_from_spectrum(mag, freqs, min_note, max_note)
        if midi is not None:
            frame_notes[idx] = midi

    # Group frames into notes using onsets as boundaries
    onsets_ms = sorted(onset_times)
    if not onsets_ms:
        # Fallback: use frame-based grouping without onsets
        midi_events = []
        prev_midi = None
        for idx in sorted(frame_notes):
            midi = frame_notes[idx]
            frame_time = t[idx] * 1000
            if midi != prev_midi:
                if prev_midi is not None and midi_events:
                    midi_events[-1]["duration"] = max(1, int(frame_time - midi_events[-1]["timestamp"]))
                midi_events.append({"timestamp": int(frame_time), "midi": midi, "duration": 250})
                prev_midi = midi
        if midi_events:
            for i in range(len(midi_events) - 1):
                midi_events[i]["duration"] = max(1, int(midi_events[i+1]["timestamp"] - midi_events[i]["timestamp"]))
        events = midi_events
    else:
        # Use onset boundaries
        for i, onset in enumerate(onsets_ms):
            end = onsets_ms[i + 1] if i + 1 < len(onsets_ms) else onsets_ms[-1] + 500
            mid_notes = []
            for idx in frame_notes:
                ft = t[idx] * 1000
                if onset - note_overlap_ms <= ft <= end:
                    mid_notes.append(frame_notes[idx])
            if mid_notes:
                import collections
                note = collections.Counter(mid_notes).most_common(1)[0][0]
                events.append({
                    "timestamp": max(0, int(onset)),
                    "midi": note,
                    "duration": max(1, int(end - onset)),
                    "velocity": 80,
                })

    events = filter_ghost_notes(events)
    events.sort(key=lambda e: e["timestamp"])
    return events, bpm


def filter_ghost_notes(events, velocity_threshold=0.15, min_duration_ms=30, harmonic_overlap_pct=0.5):
    """Post-transcription filter to remove ghost notes caused by harmonic overlap.
    - velocity_threshold: remove events quieter than this fraction of max velocity
    - min_duration_ms: remove events shorter than this
    - harmonic_overlap_pct: if multiple events share the same onset, keep only the loudest
    """
    if not events:
        return events
    max_vel = max(e.get("velocity", 80) for e in events)
    filtered = []
    for e in events:
        vel = e.get("velocity", 80) / max_vel if max_vel > 0 else 1.0
        dur = e.get("duration", 0)
        if vel < velocity_threshold:
            continue
        if dur < min_duration_ms < 1000:
            continue
        filtered.append(e)

    # Deduplicate by onset: if multiple notes start at the same time,
    # keep only the loudest (the rest are likely harmonics)
    if filtered:
        import collections
        by_onset = collections.defaultdict(list)
        for e in filtered:
            by_onset[e["timestamp"]].append(e)
        filtered = []
        for ts, notes in by_onset.items():
            notes.sort(key=lambda x: x.get("velocity", 0), reverse=True)
            filtered.append(notes[0])  # keep loudest
            for n in notes[1:]:
                # Keep if it's at least 3 semitones from the loudest (likely a real chord tone)
                if abs(n["midi"] - notes[0]["midi"]) >= 3:
                    filtered.append(n)

    return filtered


def transcribe_to_midi(audio_path, midi_path, bpm=120, **kwargs):
    """Transcribe audio to a standard MIDI file (intermediate step)."""
    events, bp = transcribe_audio(audio_path, bpm, **kwargs)
    if not events:
        return False
    try:
        import mido
    except ImportError:
        return False
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    us_per_beat = int(60_000_000 / bp)
    track.append(mido.MetaMessage("set_tempo", tempo=us_per_beat, time=0))
    track.append(mido.MetaMessage("time_signature", numerator=4, denominator=4,
                                   clocks_per_click=24, notated_32nd_notes_per_beat=8, time=0))
    midi_msgs = []
    for e in events:
        st = int(e["timestamp"] * 480 * bp / 60000)
        et = int((e["timestamp"] + e["duration"]) * 480 * bp / 60000)
        vel = min(127, max(1, e.get("velocity", 80)))
        ch = e.get("channel", 0)
        midi_msgs.append((st, "note_on", e["midi"], vel, ch))
        midi_msgs.append((et, "note_off", e["midi"], 0, ch))
    midi_msgs.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))
    cur = 0
    for tick, etype, note, vel, ch in midi_msgs:
        delta = max(0, tick - cur)
        track.append(mido.Message(
            "note_on" if etype == "note_on" else "note_off",
            note=note, velocity=vel, channel=ch, time=delta,
        ))
        cur = tick
    if midi_msgs:
        track.append(mido.MetaMessage("end_of_track", time=midi_msgs[-1][0] + 480 * 2 - cur))
    else:
        track.append(mido.MetaMessage("end_of_track", time=480))
    mid.save(midi_path)
    return True
