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
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 49576, description = "死亡之握" },
    [3] = { spellId = 51052, description = "反魔法领域" },
    [4] = { spellId = 221562, description = "窒息" },
    [5] = { spellId = 207167, description = "致盲冰雨" },
    [6] = { spellId = 46585, description = "亡者复生" },
    [7] = { spellId = 55233, description = "吸血鬼之血" },
    [8] = { spellId = 48792, description = "冰封之韧" },
    [9] = { spellId = 49039, description = "巫妖之躯" },
    [10] = { spellId = 108199, description = "血魔之握" },
    [11] = { spellId = 1263569, description = "憎恶附肢" },
    [12] = { spellId = 50, description = "吞噬" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
