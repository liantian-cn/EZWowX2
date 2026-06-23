local addonName, addonTable = ...

local insert                = table.insert -- 表插入

-- WoW 官方 API
local GetSpellTexture       = C_Spell.GetSpellTexture
local GetSpellName          = C_Spell.GetSpellName
local GetTime               = GetTime
local GetNextCastSpell      = C_AssistedCombat.GetNextCastSpell

-- DejaVu Core
local DejaVu                = _G["DejaVu"]
local COLOR                 = DejaVu.COLOR
local BadgeCell             = DejaVu.BadgeCell
local MartixInitFuncs       = DejaVu.MartixInitFuncs

-- UNIT_SPELLCAST_SUCCEEDED

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 事件框架

    local cell = BadgeCell:New(43, 14)      -- 创建一个图标槽位，位置为 (82, 17)

    local function updateCell()
        local spellID = GetNextCastSpell(false)
        if spellID == nil then
            cell:clearCell()
            return
        end
        local iconID = GetSpellTexture(spellID)
        local spellName = GetSpellName(spellID)
        cell:setCell(iconID, COLOR.SPELL_TYPE.PLAYER_SPELL, spellName)
    end
    local fastTimeElapsed = -random()
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateCell()
        end
    end)
end

insert(MartixInitFuncs, InitFrame)
