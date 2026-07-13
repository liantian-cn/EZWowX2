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
if currentSpec ~= 2 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 22812, description = "树皮术" },
    [3] = { spellId = 132469, description = "台风" },
    [4] = { spellId = 99, description = "夺魂咆哮" },
    [5] = { spellId = 29166, description = "激活" },
    [6] = { spellId = 102793, description = "乌索尔旋风" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
