--[[
LURE Math Processor — LuaJIT AST Evaluator
Receives JSON AST from Python, evaluates using LuaJIT.
Registered via api.register_math_evaluator("LURE", eval_fn, priority=10).
]]

local math_ops = {
    ["+"] = function(a, b) return a + b end,
    ["-"] = function(a, b) return a - b end,
    ["*"] = function(a, b) return a * b end,
    ["//"] = function(a, b) return a // b end,
    ["/"] = function(a, b) return a / b end,
    ["^"] = function(a, b) return a ^ b end,
    ["%"] = function(a, b) return a % b end,
}

local function eval_ast(node, vars)
    if not node then return nil end
    
    local t = node.t  -- type
    
    if t == "NUM" then
        return node.v
    elseif t == "VAR" then
        local name = node.n:sub(2)  -- strip $ prefix
        if vars[name] ~= nil then
            return tonumber(vars[name]) or vars[name]
        end
        return nil
    elseif t == "UNARY" then
        local v = eval_ast(node.o, vars)
        if v == nil then return nil end
        if node.op == "-" then return -v end
        return v
    elseif t == "BINOP" then
        local l = eval_ast(node.l, vars)
        local r = eval_ast(node.r, vars)
        if l == nil or r == nil then return nil end
        local op_fn = math_ops[node.op]
        if op_fn then return op_fn(l, r) end
        return nil
    elseif t == "CALL" then
        local args = {}
        for i, arg in ipairs(node.a or {}) do
            local v = eval_ast(arg, vars)
            if v == nil then return nil end
            table.insert(args, v)
        end
        local name = node.n
        if name == "sin" then return math.sin(args[1] or 0)
        elseif name == "cos" then return math.cos(args[1] or 0)
        elseif name == "sqrt" then return math.sqrt(args[1] or 0)
        elseif name == "pow" then return math.pow(args[1] or 0, args[2] or 1)
        elseif name == "round" then return math.floor((args[1] or 0) + 0.5)
        elseif name == "floor" then return math.floor(args[1] or 0)
        elseif name == "abs" then return math.abs(args[1] or 0)
        elseif name == "min" then
            local m = args[1] or 0
            for i = 2, #args do if args[i] < m then m = args[i] end end
            return m
        elseif name == "max" then
            local m = args[1] or 0
            for i = 2, #args do if args[i] > m then m = args[i] end end
            return m
        elseif name == "quadratic" then
            local a, b, c = args[1] or 0, args[2] or 0, args[3] or 0
            local d = b * b - 4 * a * c
            if d < 0 then return 0 end
            return (-b + math.sqrt(d)) / (2 * a)
        end
        return nil
    end
    
    return nil
end

-- Return a table with the eval function
return { eval = eval_ast }
