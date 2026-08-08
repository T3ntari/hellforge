-- LURE Scale Quantizer — vectorized-like scale quantization in LuaJIT

local M = {}

local SCALES = {
    C_Major={0,2,4,5,7,9,11}, C_minor={0,2,3,5,7,8,10},
    G_Major={7,9,11,0,2,4,6}, G_minor={7,9,10,0,2,3,5},
    D_Major={2,4,6,7,9,11,1}, D_minor={2,4,5,7,9,10,0},
    A_Major={9,11,1,2,4,6,8}, A_minor={9,11,0,2,4,5,7},
    E_Major={4,6,8,9,11,1,3}, E_minor={4,6,7,9,11,0,2},
    F_Major={5,7,9,10,0,2,4}, F_minor={5,7,8,10,0,1,3},
}

local LOOKUP_CACHE = {}

local function build_lookup(scale_name)
    local cached = LOOKUP_CACHE[scale_name]
    if cached then return cached end
    local semitones = SCALES[scale_name]
    if not semitones then return nil end
    local table = {}
    for semi = 0, 11 do
        local nearest = semitones[1]
        local min_dist = 12
        for _, s in ipairs(semitones) do
            local dist = math.abs(s - semi)
            if dist < min_dist then
                min_dist = dist
                nearest = s
            end
        end
        table[semi + 1] = nearest
    end
    LOOKUP_CACHE[scale_name] = table
    return table
end

function M.quantize(events, scale_name)
    local lookup = build_lookup(scale_name)
    if not lookup then return events end

    for i = 1, #events do
        local e = events[i]
        local midi = e.midi or 60
        local semi = midi % 12
        local octave = math.floor(midi / 12) * 12
        local snapped = octave + (lookup[semi + 1] or semi)
        if snapped < 0 then snapped = snapped + 12
        elseif snapped > 127 then snapped = snapped - 12 end
        e.midi = snapped
    end
    return events
end

return M
