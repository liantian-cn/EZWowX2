-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "SHAMAN" then return end
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 57994, description = "风剪" },
    [3] = { spellId = 198103, description = "土元素" },
    [4] = { spellId = 192058, description = "电能图腾" },
    [5] = { spellId = 378081, description = "自然迅捷" },
    [6] = { spellId = 108287, description = "图腾投射" },
    [7] = { spellId = 51514, description = "妖术" },
    [8] = { spellId = 378773, description = "强化净化术" },
    [9] = { spellId = 8143, description = "战栗图腾" },
    [10] = { spellId = 383013, description = "清毒图腾" },
    [11] = { spellId = 192063, description = "阵风" },
    [12] = { spellId = 58875, description = "幽魂步" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
