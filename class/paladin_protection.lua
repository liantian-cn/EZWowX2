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
if currentSpec ~= 2 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 115750, description = "盲目之光" },
    [3] = { spellId = 853, description = "制裁之锤" },
    [4] = { spellId = 642, description = "圣盾术" },
    [5] = { spellId = 6940, description = "牺牲祝福" },
    [6] = { spellId = 1044, description = "自由祝福" },
    [7] = { spellId = 1022, description = "保护祝福" },
    [8] = { spellId = 633, description = "圣疗术" },
    [9] = { spellId = 432459, description = "神圣壁垒" },
    [10] = { spellId = 213644, description = "清毒术" },
    [11] = { spellId = 275779, description = "审判" },
    [12] = { spellId = 375576, description = "圣洁鸣钟" },
    [13] = { spellId = 31935, description = "复仇者之盾" },
    [14] = { spellId = 26573, description = "奉献" },
    [15] = { spellId = 53600, description = "正义盾击" },
    [16] = { spellId = 204019, description = "祝福之锤" },
    [17] = { spellId = 24275, description = "正义之锤" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 432459, description = "神圣壁垒", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
