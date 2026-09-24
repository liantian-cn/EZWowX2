local pendingTimers = {}
C_Timer = {After = function(delay, callback)
    assert(delay == 0)
    table.insert(pendingTimers, callback)
end}
-- Offline API doubles: assert query behavior and exercise real generated Lua.
local state = {
    class = "DEATHKNIGHT", spec = 1, power = 1/3, health = 0.4,
    runes = 3, charges = 1, overlay = true, usable = true,
    remaining = {[61304] = 2.5, [195292] = 0}, frames = {}, cells = {}, bars = {},
    queries = {}, known = {[50842] = true, [195292] = true, [49998] = true}
}
local function color(value) return {value = value} end
local function curveValue(curve, input)
    for index = 2, #curve.points do
        local before, after = curve.points[index-1], curve.points[index]
        if input <= after[1] then
            return color(before[2].value + (after[2].value-before[2].value)
                * (input-before[1])/(after[1]-before[1]))
        end
    end
    return curve.points[#curve.points][2]
end
CreateColor = function(r, g, b, a) return color(r) end
Enum = {LuaCurveType = {Linear = 0}}
C_CurveUtil = {
    CreateColorCurve = function()
        return {points = {}, SetType = function() end,
            AddPoint = function(self, x, c) table.insert(self.points, {x, c}) end}
    end,
    EvaluateColorFromBoolean = function(value, yes, no) return value and yes or no end
}
CreateFrame = function(kind, name, parent, template)
    local frame = {events = {}, attributes = {}, name = name, template = template}
    function frame:SetAttribute(key, value) self.attributes[key] = value end
    function frame:RegisterForClicks(down, up)
        assert(down == "AnyDown" and up == "AnyUp")
    end
    function frame:RegisterEvent(event) self.events[event] = true end
    function frame:RegisterUnitEvent(event, unit) assert(unit == "player"); self.events[event] = true end
    function frame:SetScript(event, fn) self[event] = fn end
    function frame:HookScript(event, fn) self[event] = fn end
    table.insert(state.frames, frame)
    return frame
end
SetOverrideBindingClick = function(frame, priority, key, name)
    assert(priority == true and frame.name == name)
    assert(frame.template == "SecureActionButtonTemplate")
    assert(frame.attributes.type == "macro" and type(frame.attributes.macrotext) == "string")
end
UnitClass = function(unit) assert(unit == "player"); return "死亡骑士", state.class, 6 end
C_SpecializationInfo = {GetSpecialization = function() return state.spec end}
UnitPowerType = function(unit) assert(unit == "player"); return 6 end
UnitPowerPercent = function(unit, power, unmodified, curve)
    assert(unit == "player" and power == 6 and unmodified == false)
    return curveValue(curve, state.power)
end
UnitHealthPercent = function(unit, predicted, curve)
    assert(unit == "player" and predicted == true)
    return curveValue(curve, state.health)
end
UnitExists = function(unit) return unit == "player" end
GetRuneCooldown = function(index) return 0, 0, index <= state.runes end
C_SpellBook = {IsSpellInSpellBook = function(id)
    assert(id ~= 61304, "GCD must not be checked in spellbook")
    return state.known[id] == true
end}
C_Spell = {
    GetSpellCooldownDuration = function(id, ignore)
        assert((id == 61304 and ignore == false) or (id == 195292 and ignore == true))
        state.queries[id] = (state.queries[id] or 0) + 1
        if state.remaining[id] == nil then return nil end
        return {EvaluateRemainingDuration = function(self, curve)
            return curveValue(curve, state.remaining[id])
        end}
    end,
    GetSpellCharges = function(id) assert(id == 50842); return {currentCharges = state.charges} end,
    IsSpellUsable = function(id) assert(id == 49998); return state.usable, false end
}
C_SpellActivationOverlay = {IsSpellOverlayed = function(id)
    assert(id == 50842); return state.overlay
end}
local addon = {COLOR = {BLACK = color(0), WHITE = color(1)}, UIInitFuncs = {}}
addon.Cell = {New = function(self, pos)
    local cell = {brightness = 0, x = pos.x, y = pos.y}
    function cell:setCell(c) self.brightness = c.value * 255 end
    function cell:setCellRGBA(r, g, b) assert(r == g and g == b); self.brightness = r*255 end
    state.cells[pos.x] = cell
    return cell
end}
addon.ValueBar = {New = function(self, x, width, reverse)
    assert(width == 2 and reverse == false)
    local bar = {value = 0}
    function bar:setMinMaxValues(low, high) assert(low == 0 and high == 2) end
    function bar:setValue(value) self.value = value end
    state.bars[x] = bar
    return bar
end}
function state:flushTimers()
    local pending = pendingTimers
    pendingTimers = {}
    for _, callback in ipairs(pending) do callback() end
end
function state:initialize()
    for _, fn in ipairs(addon.UIInitFuncs) do fn() end
end
function state:update()
    for _, frame in ipairs(self.frames) do
        if frame.OnUpdate then frame.OnUpdate(frame, 2) end
    end
end
function state:event(event)
    -- Opaque payload must not be used; callbacks can only use the ordinary event name.
    local secret = setmetatable({}, {__tostring = function() error("secret payload") end})
    for _, frame in ipairs(self.frames) do
        if frame.events[event] and frame.OnEvent then frame.OnEvent(frame, event, secret, secret) end
    end
end
return state, addon
