local addonName, addonTable = ...

local insert = table.insert -- 表插入

-- WoW 官方 API
local GetSpellTexture = C_Spell.GetSpellTexture
local GetSpellName = C_Spell.GetSpellName
local GetTime = GetTime

-- DejaVu Core
local DejaVu = _G["DejaVu"]
local COLOR = DejaVu.COLOR
local BadgeCell = DejaVu.BadgeCell
local MartixInitFuncs = DejaVu.MartixInitFuncs

-- UNIT_SPELLCAST_SUCCEEDED

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 事件框架

    local cell = BadgeCell:New(82, 17)      -- 创建一个图标槽位，位置为 (82, 17)

    local timestamp = 0
    -- UNIT_SPELLCAST_SUCCEEDED
    -- 事件说明：施法成功时刷新施法、通道和蓄力状态。
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")

    function eventFrame:UNIT_SPELLCAST_SUCCEEDED(unitTarget, castGUID, spellID, castBarID)
        timestamp = GetTime() -- 记录当前时间戳
        local iconID = GetSpellTexture(spellID)
        local spellName = GetSpellName(spellID)
        cell:setCell(iconID, COLOR.SPELL_TYPE.PLAYER_SPELL, spellName)
    end

    eventFrame:HookScript("OnUpdate", function(frame, elapsed)
        if timestamp < (GetTime() - 5) then -- 如果距离上次施法成功超过5秒，清除图标
            cell:clearCell()
        end
    end)


    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](self, ...)
    end)
end

insert(MartixInitFuncs, InitFrame)
