"""Talisman Audio Culling + Occlusion — psychoacoustic masking engine.
Removes or reduces notes that are inaudible due to masking by louder simultaneous notes.
Based on simplified auditory masking: a loud note masks quieter ones nearby in pitch.

Signed by Tentari v1.0.0"""

import math

OCCLUSION_RATIO = 0.5
CULL_RATIO = 0.2
MASKING_WINDOW_ST = 6
TIME_WINDOW_MS = 20

_culling_enabled = True


def set_culling_enabled(enabled):
    global _culling_enabled
    _culling_enabled = enabled


def get_culling_enabled():
    return _culling_enabled


def cull_and_occlude(events, enabled=None, occlusion_ratio=OCCLUSION_RATIO,
                     cull_ratio=CULL_RATIO, masking_window=MASKING_WINDOW_ST):
    """Apply psychoacoustic culling and occlusion to events.

    Steps:
    1. Group events by timestamp (within TIME_WINDOW_MS)
    2. For each group, find the loudest note
    3. Less loud notes within the masking window are:
       - Culled (removed) if velocity < cull_ratio of loudest
       - Occluded (velocity reduced) if velocity < occlusion_ratio of loudest
    4. Notes outside the masking window are unaffected

    Returns:
        (processed_events, culled_count, occluded_count)
    """
    if enabled is None:
        enabled = get_culling_enabled()
    if not enabled or not events:
        return events, 0, 0

    sorted_events = sorted(events, key=lambda e: (e.get("timestamp", 0), -e.get("velocity", 0)))
    groups = _group_by_time(sorted_events)

    result = []
    culled = 0
    occluded = 0

    for group in groups:
        if len(group) <= 1:
            result.extend(group)
            continue

        loudest = max(group, key=lambda e: e.get("velocity", 0))
        loudest_vel = loudest.get("velocity", 80)
        loudest_note = loudest.get("midi", 60)

        for ev in group:
            if ev is loudest:
                result.append(ev)
                continue

            vel = ev.get("velocity", 0)
            note = ev.get("midi", 60)
            semitone_diff = abs(note - loudest_note)

            pitch_factor = max(0, 1 - (semitone_diff / masking_window))
            effective_ratio = (vel / max(loudest_vel, 1)) * (1 + pitch_factor)

            if effective_ratio < cull_ratio:
                culled += 1
                continue

            if effective_ratio < occlusion_ratio:
                reduction = effective_ratio / occlusion_ratio
                ev["velocity"] = max(1, int(vel * reduction))
                occluded += 1
                result.append(ev)
            else:
                result.append(ev)

    return result, culled, occluded


def _group_by_time(events):
    if not events:
        return []
    groups = []
    current_group = [events[0]]
    for ev in events[1:]:
        last_ts = current_group[-1].get("timestamp", 0)
        this_ts = ev.get("timestamp", 0)
        if abs(this_ts - last_ts) <= TIME_WINDOW_MS:
            current_group.append(ev)
        else:
            groups.append(current_group)
            current_group = [ev]
    if current_group:
        groups.append(current_group)
    return groups
