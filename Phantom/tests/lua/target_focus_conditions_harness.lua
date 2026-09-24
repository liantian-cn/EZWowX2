-- 用途：扩展现有离线 API 替身，验证目标／焦点、真实 panel/config 和图标消费者。
local state, addon = ...
state.spellTextures = {}
state.failedTextures = {}
state.requests = {}
state.casts = {}
addon.COLOR.SPELL_TYPE.INTERRUPTIBLE = CreateColor(0.8)
UnitIsEnemy = function(player, unit) assert(player == "player"); return state.units[unit].enemy == true end
UnitCanAttack = function(player, unit) assert(player == "player"); return state.units[unit].attackable end
UnitIsDeadOrGhost = function(unit) return state.units[unit].dead end
UnitAffectingCombat = function(unit) return state.units[unit].combat end
UnitCastingInfo = function(unit)
    local cast = state.casts[unit]
    if cast and cast.mode == "casting" then
        return state:secret("cast"), nil, cast.texture, nil, nil, false, nil, cast.blocked, nil, nil, 0
    end
end
UnitChannelInfo = function(unit)
    local cast = state.casts[unit]
    if cast and cast.mode == "channeling" then
        return state:secret("channel"), nil, cast.texture, nil, nil, false, cast.blocked, nil, cast.empowered == true
    end
end
local oldCastingDuration = UnitCastingDuration
UnitCastingDuration = function(unit) state.lastDurationUnit = unit; return oldCastingDuration("player") end
UnitChannelDuration = UnitCastingDuration
C_Spell.GetSpellTexture = function(id) return state.spellTextures[id] end
C_Spell.RequestLoadSpellData = function(id) table.insert(state.requests, id) end
C_Spell.GetSpellDescription = function(id) return "说明" end
C_Spell.GetSpellName = function(id) return "技能" .. id end

local original = CreateFrame
local function noop() end
local function decoration()
    return setmetatable({}, {__index = function(_, key) return noop end})
end
CreateFrame = function(kind, name, parent, template)
    local frame = original(kind, name, parent, template)
    function frame:RegisterUnitEvent(event, ...) self.events[event] = {...} end
    function frame:SetShown(value) self.hidden = not value end
    function frame:Hide() self.hidden = true end
    function frame:IsShown() return not self.hidden end
    function frame:GetName() return self.name end
    function frame:GetWidth() return self.width end
    function frame:SetHeight(value) self.height = value end
    function frame:SetWidth(value) self.width = value end
    function frame:CreateFontString() return decoration() end
    function frame:HookScript(script, callback)
        local previous = self[script]
        self[script] = function(...)
            if previous then previous(...) end
            callback(...)
        end
    end
    function frame:SetUnit(unit) self.unit = unit end
    function frame:AddAuraSlot(key, filter, options)
        assert(kind == "AuraContainer" and template == "CustomAuraContainerTemplate")
        local button = CreateFrame("AuraButton", nil, self)
        options.initializeFrame(button)
        self.slots[key] = {filter = filter, options = options, button = button}
    end
    local oldTexture = frame.CreateTexture
    function frame:CreateTexture(...)
        local tex = oldTexture(self, ...)
        local oldSet = tex.SetTexture
        function tex:SetTexture(value)
            oldSet(self, value)
            -- 普通 Lua 无法模拟 WoW 秘密布尔；仅控制普通返回值验证消费者不依赖真值。
            if state.overrideTextureResult then return state.textureResult end
            return self.texture ~= nil and not state.failedTextures[self.texture]
        end
        tex.SetPoint = noop
        tex.SetSize = noop
        return tex
    end
    frame.EnableMouse = noop
    frame.SetMovable = noop
    frame.RegisterForDrag = noop
    frame.SetClampedToScreen = noop
    frame.StartMoving = noop
    frame.StopMovingOrSizing = noop
    return frame
end
function state:event(event, unit, ...)
    for _, frame in ipairs(self.frames) do
        local filter = frame.events[event]
        local matches = filter == true
        if type(filter) == "table" then
            for _, candidate in ipairs(filter) do if candidate == unit then matches = true end end
        end
        if matches and frame.OnEvent then frame.OnEvent(frame, event, unit, ...) end
    end
end
local function sizes()
    return setmetatable({}, {__index = function() return 4 end})
end
addon.SIZE.PANEL = {MainFrame = sizes(), BUTTON = sizes(), SETTING_LINE = sizes()}
addon.COLOR.PANEL = setmetatable({}, {__index = function() return CreateColor(0) end})
addon.GetUIScaleFactor = function(value) return value end
addon.logging = noop
addon.BurstRemaining = function() return 0 end
addon.InBurst = function() return false end
UIParent = CreateFrame("Frame")
GameTooltip = decoration()

-- 仅测试使用 upvalue 取得私有 Profile，验证真实 switch_profile 的保存与通知语义。
function state:switchProfile(name)
    for index = 1, 10 do
        local key, value = debug.getupvalue(addon.Config, index)
        if key == "Profile" then value.switch_profile(name); return end
    end
    error("找不到配置档案接口")
end
