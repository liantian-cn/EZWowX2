-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "PALADIN" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 115750, description = "盲目之光" },
    [3] = { spellId = 853, description = "制裁之锤" },
    [4] = { spellId = 642, description = "圣盾术" },
    [5] = { spellId = 6940, description = "牺牲祝福" },
    [6] = { spellId = 1044, description = "自由祝福" },
    [7] = { spellId = 1022, description = "保护祝福" },
    [8] = { spellId = 633, description = "圣疗术" },
    [9] = { spellId = 213644, description = "清毒术" },
    [10] = { spellId = 20271, description = "审判" },
    [11] = { spellId = 375576, description = "圣洁鸣钟" },
    [12] = { spellId = 184575, description = "公正之剑" },
    [13] = { spellId = 343527, description = "处决宣判" },
    [14] = { spellId = 255937, description = "灰烬觉醒" },
    [15] = { spellId = 31884, description = "复仇之怒" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 20271, description = "审判", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
