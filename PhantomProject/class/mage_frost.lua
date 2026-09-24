-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "MAGE" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
}

addonTable.SPEC.ChargeList = {
}

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "热能真空", spellIDs = { 1247730 } },
    [2] = { description = "冰冷智慧", spellIDs = { 190446 } },
    [3] = { description = "冰冻之雨", spellIDs = { 270232 } },
    [4] = { description = "寒冰指", spellIDs = { 44544 } },
}

addonTable.SPEC.TargetDebuff = {
}
