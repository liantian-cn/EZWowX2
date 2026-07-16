-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "HUNTER" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 53480, description = "牺牲咆哮" },
    [3] = { spellId = 109304, description = "意气风发" },
    [4] = { spellId = 19577, description = "胁迫" },
    [5] = { spellId = 5116, description = "震荡射击" },
    [6] = { spellId = 19801, description = "宁神射击" },
    [7] = { spellId = 187698, description = "焦油陷进" },
    [8] = { spellId = 1513, description = "恐吓野兽" },
    [9] = { spellId = 109248, description = "束缚射击" },
    [10] = { spellId = 195645, description = "摔绊" },
    [11] = { spellId = 1261193, description = "爆裂火铳" },
    [12] = { spellId = 1250646, description = "狩魂一击" },
    [13] = { spellId = 190925, description = "鱼叉猛刺" },
    [14] = { spellId = 186270, description = "猛禽一击" },
    [15] = { spellId = 259495, description = "野火炸弹" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
