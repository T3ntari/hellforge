-- LURE Event Processor — validate, dedup, sort in LuaJIT

local M = {}

function M.validate(events)
    if not events or #events == 0 then return {}, 0 end
    local cleaned = {}
    local seen = {}
    local removed = 0

    for i = 1, #events do
        local e = events[i]
        local midi = e.midi or -1
        if midi < 0 or midi > 127 then removed = removed + 1; goto continue end
        local dur = e.duration or 0
        if dur <= 0 then removed = removed + 1; goto continue end
        e.velocity = math.max(0, math.min(127, e.velocity or 80))
        local ch = e.channel or 0
        local key = tostring(e.timestamp or 0) .. ":" .. tostring(midi) .. ":" .. tostring(dur) .. ":" .. tostring(e.velocity) .. ":" .. tostring(ch)
        if not seen[key] then
            seen[key] = true
            table.insert(cleaned, e)
        else
            removed = removed + 1
        end
        ::continue::
    end

    -- Sort by timestamp then midi
    table.sort(cleaned, function(a, b)
        local at = a.timestamp or 0
        local bt = b.timestamp or 0
        if at ~= bt then return at < bt end
        return (a.midi or 0) < (b.midi or 0)
    end)

    return cleaned, removed
end

return M
