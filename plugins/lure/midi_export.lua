-- LURE MIDI Export — fast tick calculation

local M = {}

function M.calc_ticks(events, bpm, tpb)
    tpb = tpb or 480
    local factor = tpb * bpm / 60000
    for i = 1, #events do
        local e = events[i]
        local ts = e.timestamp or 0
        local dur = e.duration or 500
        e._start_tick = math.floor(ts * factor + 0.5)
        e._end_tick = math.floor((ts + dur) * factor + 0.5)
    end
    return events
end

function M.build_midi_events(events, bpm, tpb)
    M.calc_ticks(events, bpm, tpb)
    local midi_ev = {}
    for i = 1, #events do
        local e = events[i]
        local ch = e.channel or 0
        local vel = math.max(1, math.min(127, e.velocity or 80))
        table.insert(midi_ev, {tick=e._start_tick, type="note_on", note=e.midi, vel=vel, ch=ch})
        table.insert(midi_ev, {tick=e._end_tick, type="note_off", note=e.midi, vel=0, ch=ch})
    end
    table.sort(midi_ev, function(a, b)
        if a.tick ~= b.tick then return a.tick < b.tick end
        if a.type ~= b.type then return a.type == "note_off" end
        return false
    end)
    return midi_ev
end

return M
