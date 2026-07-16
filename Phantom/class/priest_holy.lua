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
if currentSpec ~= 2 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 8122, description = "心灵尖啸" },
    [3] = { spellId = 32375, description = "群体驱散" },
    [4] = { spellId = 527, description = "纯净术" },
    [5] = { spellId = 19236, description = "绝望祷言" },
    [6] = { spellId = 232633, description = "奥术洪流" },
    [7] = { spellId = 33076, description = "愈合祷言" },
    [8] = { spellId = 2050, description = "圣言术：静" },
    [9] = { spellId = 88625, description = "圣言术：罚" },
    [10] = { spellId = 200183, description = "神圣化身" },
    [11] = { spellId = 14914, description = "神圣之火" },
    [12] = { spellId = 120517, description = "光晕" },
    [13] = { spellId = 64843, description = "神圣赞美诗" },
}

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 33076, description = "愈合祷言", minValue = 0, maxValue = 2 },
    [2] = { spellId = 2050, description = "圣言术：静", minValue = 0, maxValue = 2 },
}

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "织光者", spellIDs = { 390993 } },
    [2] = { description = "圣光涌动", spellIDs = { 114255 } },
    [3] = { description = "祈福", spellIDs = { 1262766 } },
}

addonTable.SPEC.TargetDebuff = {
}
