-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "PRIEST" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 8122, description = "心灵尖啸" },
    [3] = { spellId = 32375, description = "群体驱散" },
    [4] = { spellId = 527, description = "纯净术" },
    [5] = { spellId = 19236, description = "绝望祷言" },
    [6] = { spellId = 232633, description = "奥术洪流" },
    [7] = { spellId = 8092, description = "心灵震爆" },
    [8] = { spellId = 32379, description = "暗言术：灭" },
    [9] = { spellId = 263165, description = "虚空洪流" },
    [10] = { spellId = 228260, description = "虚空形态" },
    [11] = { spellId = 1227280, description = "触须猛击" },
    [12] = { spellId = 15286, description = "吸血鬼的拥抱" },
    [13] = { spellId = 120644, description = "光晕" },
    [14] = { spellId = 1242173, description = "虚空齐射" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
