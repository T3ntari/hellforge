-- LURE Line Parser
-- Parses a single line of E code and returns an event table or nil.
-- No state management, no cursor tracking. Pure pattern matching.
-- Runs under LuaJIT, called from Python via lupa.

local M = {}

-- Note name to MIDI number
local NOTE_SEMIS = {C=0, D=2, E=4, F=5, G=7, A=9, B=11,
                    ["C#"]=1, Db=1, ["D#"]=3, Eb=3,
                    ["F#"]=6, Gb=6, ["G#"]=8, Ab=8,
                    ["A#"]=10, Bb=10}

local function name_to_midi(name)
    if not name then return 60 end
    local note, oct = name:match("([A-G]#?b?)(%d+)")
    if not note then return 60 end
    local oct_n = tonumber(oct) or 4
    return (NOTE_SEMIS[note] or 0) + (oct_n + 1) * 12
end

local DUR_MS = {w=2000, h=1000, q=500, e=250, s=125, t=62}
local function dur_code(code)
    if not code then return 500 end
    local c = code:lower():sub(1,1)
    return DUR_MS[c] or 500
end

local DYN_VEL = {ppp=16, pp=33, p=49, mp=64, mf=80, f=96, ff=112, fff=126}
local function dyn_code(dyn)
    if not dyn then return 80 end
    local d = dyn:lower()
    return DYN_VEL[d] or (tonumber(d) or 80)
end

local CHORD_INTERVALS = {
    major={0,4,7}, minor={0,3,7}, dom7={0,4,7,10}, min7={0,3,7,10},
    Maj7={0,4,7,11}, dim={0,3,6}, aug={0,4,8}, sus4={0,5,7},
}

-- Parse a single line. Returns event table or nil.
function M.parse(line)
    if not line or line == "" then return nil end

    -- Strip inline comment
    local comment_pos = line:find("//")
    if comment_pos then line = line:sub(1, comment_pos - 1) end
    line = line:match("^%s*(.-)%s*$")
    if line == "" or line:sub(1,1) == "#" or line:sub(1,1) == "@" then return nil end
    if line:find("^/%*") or line:find("^%*%/") then return nil end

    -- CH[channel] prefix
    local ch = nil
    local ch_str = line:match("CH%[(%d+)%]")
    if ch_str then ch = tonumber(ch_str); line = line:gsub("CH%[%d+%]", "") end

    -- Machine: T<N> N<MIDI> D<DUR> V<VEL> (all combos)
    local ts, midi, dur, vel_str = line:match("^%s*T(%d+)%s+N(%d+)%s+D(%d+)%s+V([%d.]+)")
    if not ts then
        ts, midi, vel_str = line:match("^%s*T(%d+)%s+N(%d+)%s+V([%d.]+)")
    end
    if not ts then
        ts, midi, dur = line:match("^%s*T(%d+)%s+N(%d+)%s+D(%d+)")
    end
    if not ts then
        ts, midi = line:match("^%s*T(%d+)%s+N(%d+)")
    end
    if ts then
        local vel = 80
        if vel_str then
            local v = tonumber(vel_str)
            if v then vel = math.floor(v * 127 + 0.5) end
        end
        vel = math.max(1, math.min(127, vel))
        return {
            timestamp = tonumber(ts),
            midi = math.max(0, math.min(127, tonumber(midi))),
            duration = tonumber(dur) or 500,
            velocity = vel,
            channel = ch,
        }
    end

    -- Human: play note(C4) @dur:q @vel:mf
    local note_name = line:match("^play%s+note%(([A-G]#?b?%d+)%)")
    if note_name then
        local dur_c = line:match("@dur:(%w+)") or "q"
        local vel_c = line:match("@vel:(%w+)") or "mf"
        local ch_h = line:match("@ch:(%d+)")
        return {
            timestamp = 0,
            midi = name_to_midi(note_name),
            duration = dur_code(dur_c),
            velocity = dyn_code(vel_c),
            channel = tonumber(ch_h) or ch,
        }
    end

    -- Human: play chord(C, major) @dur:q @vel:mf
    local root, quality = line:match("^play%s+chord%(([A-G]#?b?)%s*,%s*(%w+)%)")
    if root and quality then
        local intervals = CHORD_INTERVALS[quality:lower()] or {0, 4, 7}
        local r = name_to_midi(root .. "3")
        local dur_c = line:match("@dur:(%w+)") or "q"
        local vel_c = line:match("@vel:(%w+)") or "mf"
        local ch_c = line:match("@ch:(%d+)")
        -- Return first note of chord; Python handles expansion
        return {
            timestamp = 0,
            midi = math.max(0, math.min(127, r + (intervals[1] or 0))),
            duration = dur_code(dur_c),
            velocity = dyn_code(vel_c),
            channel = tonumber(ch_c) or ch,
            _chord_root = r,
            _chord_intervals = intervals,
        }
    end

    -- v3 shorthand: C4 q or C4 q mf
    local note3, dur3, vel3 = line:match("^([A-G]#?b?)(%d+)%s+([whqest])%s*(%w*)")
    if note3 then
        return {
            timestamp = 0,
            midi = name_to_midi(note3 .. dur3),
            duration = dur_code(dur3),
            velocity = dyn_code(vel3 or "mf"),
            channel = ch,
        }
    end

    return nil
end

-- Parse multiple lines (batch mode for speed)
function M.parse_batch(lines)
    local results = {}
    for _, line in ipairs(lines) do
        table.insert(results, M.parse(line))
    end
    return results
end

return M
