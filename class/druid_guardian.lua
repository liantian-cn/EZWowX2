-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "DRUID" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 22812, description = "树皮术" },
    [3] = { spellId = 132469, description = "台风" },
    [4] = { spellId = 99, description = "夺魂咆哮" },
    [5] = { spellId = 29166, description = "激活" },
    [6] = { spellId = 102793, description = "乌索尔旋风" },
    [7] = { spellId = 22842, description = "狂暴回复" },
    [8] = { spellId = 61336, description = "生存本能" },
    [9] = { spellId = 102558, description = "化身：乌索克的守护者" },
    [10] = { spellId = 1261867, description = "野性之心" },
    [11] = { spellId = 1253799, description = "碎甲咆哮" },
    [12] = { spellId = 1252871, description = "赤红之月" },
    [13] = { spellId = 6807, description = "重殴" },
    [14] = { spellId = 77758, description = "痛击" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 22842, description = "狂暴回复", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
