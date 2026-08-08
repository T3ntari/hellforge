-- LURE Directives — @bpm, @vol, @key, @scale, @gc, tempo aliases, etc.

local M = {}

local TEMPO_ALIASES = {
    larghissimo=20, grave=40, largo=50, lento=55, adagio=56,
    adagietto=65, andante=76, andantino=85, moderato=100,
    allegretto=110, allegro=120, vivace=140, presto=180, prestissimo=210,
}

local SCALES = {
    C_Major={0,2,4,5,7,9,11}, C_minor={0,2,3,5,7,8,10},
    G_Major={7,9,11,0,2,4,6}, G_minor={7,9,10,0,2,3,5},
    D_Major={2,4,6,7,9,11,1}, D_minor={2,4,5,7,9,10,0},
    A_Major={9,11,1,2,4,6,8}, A_minor={9,11,0,2,4,5,7},
    E_Major={4,6,8,9,11,1,3}, E_minor={4,6,7,9,11,0,2},
    F_Major={5,7,9,10,0,2,4}, F_minor={5,7,8,10,0,1,3},
}

function M.parse_bpm(text, default)
    local bpm = tonumber(text:match("@bpm%s+(%d+%.?%d*)"))
        or tonumber(text:match("@tempo%s+(%d+%.?%d*)"))
    if bpm then return bpm end
    -- Check tempo aliases
    for alias, val in pairs(TEMPO_ALIASES) do
        if text:match("@"..alias) then return val end
    end
    return default or 120
end

function M.parse_scale(text)
    local scale = text:match("@scale%s+(%w+_%w+)")
    if scale and SCALES[scale] then return scale end
    return nil
end

function M.parse_key(text)
    local key = text:match("@key%s+([A-G]#?b?%s*%w*)")
    return key
end

function M.get_scale(scale_name)
    return SCALES[scale_name]
end

return M
