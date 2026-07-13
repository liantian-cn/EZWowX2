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
if currentSpec ~= 2 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 49576, description = "死亡之握" },
    [3] = { spellId = 51052, description = "反魔法领域" },
    [4] = { spellId = 221562, description = "窒息" },
    [5] = { spellId = 207167, description = "致盲冰雨" },
    [6] = { spellId = 51271, description = "冰霜之柱" },
    [7] = { spellId = 279302, description = "冰霜巨龙之怒" },
    [8] = { spellId = 439843, description = "死神印记" },
    [9] = { spellId = 47568, description = "符文武器增效" },
    [10] = { spellId = 1249658, description = "冰龙吐息" },
}

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 47568, description = "符文武器增效", minValue = 0, maxValue = 2 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
