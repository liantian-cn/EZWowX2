-- Offline display/API doubles. These do not emulate WoW access restrictions completely.
local state = {
    frames = {}, timers = {}, callbacks = {}, cells = {}, icons = {}, queries = {},
    role = "NONE", combat = false, selfTarget = false, moving = false, vehicle = false,
    mounted = false, targeting = false, grouped = false, raiding = false,
    units = {player = {name = "Player"}}, ranges = {}, inventory = {}, items = {},
    known = {}, spellbook = {}, progress = 0, absorbs = 0, healAbsorbs = 0,
    auras = {}, randomCalls = 0, invalidSpells = {},
}
local secretValues = {}
local function reveal(value)
    if secretValues[value] ~= nil then return secretValues[value] end
    return value
end
function state:secret(value)
    local function forbidden() error("ordinary operation on opaque secret") end
    local token = setmetatable({}, {
        __index = forbidden, __newindex = forbidden, __tostring = forbidden,
        __add = forbidden, __sub = forbidden, __mul = forbidden, __div = forbidden,
        __lt = forbidden, __le = forbidden, __concat = forbidden,
    })
    secretValues[token] = value
    return token
end
issecretvalue = function(value) return secretValues[value] ~= nil end
local function color(value, secret)
    return {value = value, GetRGBA = function()
        local channel = secret and state:secret(value) or value
        return channel, channel, channel, 1
    end}
end
CreateColor = function(r) return color(r) end
Enum = {LuaCurveType = {Linear = 0}}
AuraContainerSortMethod = {BigDefensive = 1}
AuraContainerSortDirection = {Normal = 0}
C_CurveUtil = {
    CreateColorCurve = function()
        return {points = {}, SetType = function(self, value) assert(value == 0) end,
            AddPoint = function(self, x, value) table.insert(self.points, {x, value}) end}
    end,
    EvaluateColorFromBoolean = function(value, yes, no)
        local selected = reveal(value) and yes or no
        return color(selected.value, issecretvalue(value))
    end,
}
math.random = function()
    state.randomCalls = state.randomCalls + 1
    return state.randomCalls / 100 -- deterministic but distinct offsets
end

local function texture()
    return {
        SetAllPoints = function(self, parent) self.parent = parent end,
        SetTexture = function(self, value) self.rawTexture = value; self.texture = reveal(value) end,
        SetColorTexture = function(self, r, g, b, a) self.r = reveal(r); self.g = reveal(g); self.b = reveal(b); self.a = a end,
        SetVertexColor = function(self, r, g, b, a) self.r = reveal(r); self.g = reveal(g); self.b = reveal(b); self.a = a end,
        Show = function(self) self.hidden = false end,
        Hide = function(self) self.hidden = true end,
    }
end
CreateFrame = function(kind, name, parent, template)
    local frame = {kind = kind, name = name, parent = parent, template = template, events = {}, textures = {}, children = {}, slots = {}}
    if parent then table.insert(parent.children, frame) end
    function frame:RegisterEvent(event) self.events[event] = true end
    function frame:RegisterUnitEvent(event, unit)
        assert(unit == "player" or unit == "target" or unit == "focus" or unit == "pet")
        self.events[event] = unit
    end
    function frame:SetScript(script, callback) self[script] = callback end
    function frame:SetAllPoints(anchor) self.anchor = anchor end
    function frame:SetPoint(...) self.point = {...} end
    function frame:SetSize(width, height)
        self.width = width; self.height = height
        -- 按第四行槽位几何识别图标背板，避免把其他匿名画布子级误当图标。
        if kind == "Frame" and not name and parent and parent.isBackground and width == 8 and height == 8 then
            table.insert(state.icons, self)
        end
    end
    function frame:SetFrameStrata(value) self.strata = value end
    function frame:SetFrameLevel(value) self.level = value end
    function frame:Show() self.hidden = false end
    function frame:CreateTexture(_, layer)
        local result = texture(); result.layer = layer
        table.insert(self.textures, result)
        return result
    end
    function frame:SetStatusBarTexture(value) self.barTexture = value end
    function frame:SetStatusBarColor(r, g, b, a) self.barColor = {r, g, b, a} end
    function frame:SetMinMaxValues(low, high) self.low = low; self.high = high end
    function frame:SetValue(value)
        self.rawValue = value -- the plugin must hand over exactly the producer's opaque value
        self.fill = math.max(0, math.min(1, (reveal(value) - self.low) / (self.high - self.low)))
    end
    function frame:SetUnit(unit) assert(unit == "player"); self.unit = unit end
    function frame:AddAuraSlot(key, filter, options)
        assert(kind == "AuraContainer" and self.unit == "player")
        assert(template == "CustomAuraContainerTemplate")
        local button = CreateFrame("AuraButton", nil, self)
        options.initializeFrame(button)
        self.slots[key] = {filter = filter, options = options, button = button}
        return button
    end
    function frame:UpdateAllAuras() self.refreshes = (self.refreshes or 0) + 1 end
    table.insert(state.frames, frame)
    if name then
        local x = name:match("Cell_(%d+)_2$")
        if x then state.cells[tonumber(x)] = frame end
    end
    return frame
end
C_Timer = {
    After = function(delay, callback)
        assert(delay == 0)
        table.insert(state.timers, {delay = delay, callback = callback})
    end,
    NewTimer = function(delay, callback)
        assert(delay == 0.25)
        local timer = {delay = delay, callback = callback, Cancel = function(self) self.cancelled = true end}
        table.insert(state.timers, timer)
        return timer
    end,
}
EventRegistry = {RegisterCallback = function(_, event, callback, owner)
    state.callbacks[event] = {callback = callback, owner = owner}
end}
function state:flushTimers()
    local pending = self.timers
    self.timers = {}
    for _, timer in ipairs(pending) do if not timer.cancelled then timer.callback() end end
end
function state:query(name)
    self.queries[name] = (self.queries[name] or 0) + 1
end
UnitGroupRolesAssigned = function() state:query("role"); return state.role end
UnitAffectingCombat = function(unit)
    state:query("combat")
    if unit == nil or unit == "player" then return state.combat end
    return state.units[unit] and state.units[unit].combat == true
end
UnitIsUnit = function(a, b) assert(a == "player" and b == "target"); return state.selfTarget end
IsPlayerMoving = function() state:query("moving"); return state.moving end
UnitInVehicle = function() return state.vehicle end
IsMounted = function() return state.mounted end
SpellIsTargeting = function() return state.targeting end
GetCurrentKeyBoardFocus = function() return state.focus end
IsInGroup = function() return state.grouped end
IsInRaid = function() return state.raiding end
UnitExists = function(unit) return state.units[unit] ~= nil end
UnitIsDeadOrGhost = function(unit) return state.units[unit] and state.units[unit].dead == true end
UnitHealthPercent = function(unit, predicted, curve)
    state:query("health")
    state.lastHealthUnit = unit
    state.lastHealthPredicted = predicted
    assert(#curve.points == 2)
    assert(curve.points[1][1] == 0 and curve.points[1][2].value == 0)
    assert(curve.points[2][1] == 1 and curve.points[2][2].value == 1)
    local info = assert(state.units[unit])
    local value = predicted and info.predictedHealth or info.health
    return color(reveal(value or 0), true)
end
UnitCanAttack = function(player, unit) assert(player == "player"); return state.units[unit].attackable == true end
UnitName = function(unit) return state.units[unit] and state.units[unit].name end
C_Spell = {IsSpellInRange = function(id, unit)
    state:query("range")
    state.lastRangeSpell = id
    return state.ranges[unit]
end,
    DoesSpellExist = function(id) return not state.invalidSpells[id] end,
}
GetInventoryItemID = function(unit, slot) assert(unit == "player"); return state.inventory[slot] end
C_Item = {
    GetItemCooldown = function(id)
        state:query("item"); state.lastItem = id
        local item = state.items[id] or {duration = 0, enabled = false}
        return 0, item.duration, item.enabled
    end,
    IsUsableItem = function(id)
        local item = state.items[id] or {usable = false, noMana = false}
        return item.usable, item.noMana
    end,
}
C_SpellBook = {
    IsSpellKnown = function(id) state:query("known"); return state.known[id] == true end,
    IsSpellInSpellBook = function(id) return state.spellbook[id] == true end,
}
UnitCastingInfo = function()
    state:query("cast")
    if state.mode == "casting" then return state:secret("cast"), nil, state.castTexture, nil, nil, false, nil, nil, nil, nil, 0 end
end
UnitChannelInfo = function()
    if state.mode == "channeling" then return state:secret("channel"), nil, state.castTexture, nil, nil, false, nil, nil, state.empowered == true end
end
local function duration()
    if state.noDuration then return nil end
    local result = {EvaluateElapsedPercent = function(_, curve)
        assert(#curve.points == 2)
        assert(curve.points[1][1] == 0 and curve.points[1][2].value == 0)
        assert(curve.points[2][1] == 1 and curve.points[2][2].value == 1)
        return color(state.progress, true)
    end}
    if state.secretDuration then secretValues[result] = true end
    return result
end
UnitCastingDuration = function(unit) assert(unit == "player"); return duration() end
UnitChannelDuration = function(unit) assert(unit == "player"); return duration() end
UnitGetTotalAbsorbs = function() return state.absorbs end
UnitGetTotalHealAbsorbs = function() return state.healAbsorbs end
local addon = {
    COLOR = {BLACK = color(0), WHITE = color(1), SPELL_TYPE = {PLAYER_SPELL = color(0.5)}},
    SIZE = {CELL = 4}, FrameLevel = {
        Canvas = 9500, Separator = 9550, Backplate = 9600, Content = 9650,
        AuraContainer = 9700, AuraButton = 9750, AuraContent = 9800, Overlay = 9850, Marker = 9900,
    },
    GeneralCellLength = 0, ConditionCellLength = 0, IconTileLength = 0, UIInitFuncs = {},
    BackgroundFrameResize = function() end,
}
addon.BackgroundFrame = CreateFrame("Frame")
addon.BackgroundFrame.isBackground = true
function state:initialize()
    for _, callback in ipairs(addon.UIInitFuncs) do callback() end
end
function state:event(event, unit, ...)
    for _, frame in ipairs(self.frames) do
        local filter = frame.events[event]
        if filter and (filter == true or filter == unit) and frame.OnEvent then
            frame.OnEvent(frame, event, unit, ...)
        end
    end
end
function state:tick(elapsed)
    for _, frame in ipairs(self.frames) do if frame.OnUpdate then frame.OnUpdate(frame, elapsed) end end
end
function state:brightness(x)
    local frame = self.cells[x]
    assert(frame)
    for _, child in ipairs(frame.children) do
        if child.kind == "StatusBar" then return child.fill * 255 end
    end
    -- 普通 Cell 的颜色纹理位于固定黑底之上，直接背板则只提供黑底。
    for _, region in ipairs(frame.textures) do
        if region.layer == "ARTWORK" then return region.r * 255 end
    end
    return frame.textures[1].r * 255
end
return state, addon
