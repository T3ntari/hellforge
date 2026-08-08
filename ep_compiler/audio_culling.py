"""Real audio culling + occlusion — psychoacoustic masking engine.
Removes or reduces notes that are inaudible due to masking by louder simultaneous notes.
Based on simplified auditory masking: a loud note masks quieter ones nearby in pitch."""

import math

# ── Psychoacoustic constants ──

# Velocity ratio below which a note is occluded (velocity reduced)
OCCLUSION_RATIO = 0.5
# Velocity ratio below which a note is culled (removed entirely)
CULL_RATIO = 0.2
# Semitone window for masking: notes within this range mask each other
MASKING_WINDOW_ST = 6
# How much a semitone difference reduces masking (dB per semitone)
MASKING_SLOPE_DB = 5.0
# Time window in ms to group simultaneous events
TIME_WINDOW_MS = 20


def cull_and_occlude(events, enabled=True, occlusion_ratio=OCCLUSION_RATIO,
                     cull_ratio=CULL_RATIO, masking_window=MASKING_WINDOW_ST):
    """Apply psychoacoustic culling and occlusion to events.
    
    Steps:
    1. Group events by timestamp (within TIME_WINDOW_MS)
    2. For each group, find the loudest note
    3. Less loud notes within the masking window are:
       - Culled (removed) if velocity < cull_ratio of loudest
       - Occluded (velocity reduced) if velocity < occlusion_ratio of loudest
    4. Notes outside the masking window are unaffected
    
    Args:
        events: list of event dicts with 'timestamp', 'midi', 'velocity'
        enabled: set False to bypass (return events unchanged)
        occlusion_ratio: reduce velocity of notes quieter than this ratio
        cull_ratio: remove notes quieter than this ratio
        masking_window: semitone range for masking
    
    Returns:
        (processed_events, culled_count, occluded_count)
    """
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
        
        # Find the loudest note in this group
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
            
            # Calculate effective velocity ratio accounting for pitch proximity
            # Notes close in pitch are masked more
            pitch_factor = max(0, 1 - (semitone_diff / masking_window))
            effective_ratio = (vel / max(loudest_vel, 1)) * (1 + pitch_factor)
            
            if effective_ratio < cull_ratio:
                culled += 1
                continue  # remove entirely
            
            if effective_ratio < occlusion_ratio:
                # Reduce velocity proportionally
                reduction = effective_ratio / occlusion_ratio
                ev["velocity"] = max(1, int(vel * reduction))
                occluded += 1
                result.append(ev)
            else:
                result.append(ev)
    
    return result, culled, occluded


def _group_by_time(events):
    """Group events that occur within TIME_WINDOW_MS of each other."""
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


def apply_culling_to_compilation(events):
    """Convenience wrapper for the compile pipeline. Returns events unchanged if disabled."""
    from . import audio_culling as _ac
    return _ac.cull_and_occlude(events)[0]


# ── Default state (can be toggled by sys audio cull on|off) ──

_culling_enabled = True


def set_culling_enabled(enabled):
    global _culling_enabled
    _culling_enabled = enabled


def get_culling_enabled():
    return _culling_enabled
