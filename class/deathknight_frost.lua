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

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "黑暗援助", spellIDs = { 101568 } },
    [2] = { description = "杀戮机器", spellIDs = { 51124 } },
    [3] = { description = "白霜", spellIDs = { 59052 } },
    [4] = { description = "冰霜灾祸", spellIDs = { 1229310 } },
    [5] = { description = "冰霜之柱", spellIDs = { 51271 } },
    [6] = { description = "霜巢之眷", spellIDs = { 1265630 } },
    [7] = { description = "霜巢之眷-冰霜巨龙之怒", spellIDs = { 1265639 } },
}

addonTable.SPEC.TargetDebuff = {
}
