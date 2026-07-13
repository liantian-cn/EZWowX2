-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "DEATHKNIGHT" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 49576, description = "死亡之握" },
    [3] = { spellId = 51052, description = "反魔法领域" },
    [4] = { spellId = 221562, description = "窒息" },
    [5] = { spellId = 207167, description = "致盲冰雨" },
    [6] = { spellId = 46584, description = "亡者复生" },
    [7] = { spellId = 42650, description = "亡者大军" },
    [8] = { spellId = 1247378, description = "腐化" },
    [9] = { spellId = 1233448, description = "黑暗突变" },
    [10] = { spellId = 343294, description = "灵魂收割" },
    [11] = { spellId = 43265, description = "枯萎凋零" },
}

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 1247378, description = "腐化", minValue = 0, maxValue = 3 },
    [2] = { spellId = 43265, description = "枯萎凋零", minValue = 0, maxValue = 2 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
