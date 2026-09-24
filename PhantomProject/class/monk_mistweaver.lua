-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "MONK" then return end
if currentSpec ~= 2 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 116680, description = "雷光聚神茶" },
    [3] = { spellId = 115151, description = "复苏之雾" },
    [4] = { spellId = 115310, description = "还魂术" },
    [5] = { spellId = 116849, description = "作茧缚命" },
    [6] = { spellId = 115450, description = "清创生血" },
    [7] = { spellId = 443028, description = "天神御身" },
    [8] = { spellId = 322109, description = "轮回之触" },
    [9] = { spellId = 119381, description = "扫堂腿" },
    [10] = { spellId = 1270621, description = "宁神茶" },
    [11] = { spellId = 101643, description = "魂体双分" },
    [12] = { spellId = 119996, description = "魂体双分：转移" },
    [13] = { spellId = 107428, description = "旭日东升踢" },
    [14] = { spellId = 100784, description = "幻灭踢" },
    [15] = { spellId = 116844, description = "平心之环" },
    [16] = { spellId = 115078, description = "分筋错骨" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 116680, description = "雷光聚神茶", minValue = 0, maxValue = 8 },
    [2] = { spellId = 115151, description = "复苏之雾", minValue = 0, maxValue = 8 },
}

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "生生不息1", spellIDs = { 197919 } },
    [2] = { description = "生生不息2", spellIDs = { 197916 } },
    [3] = { description = "灵泉", spellIDs = { 1260565 } },
    [4] = { description = "玄牛之力", spellIDs = { 443112 } },
    [5] = { description = "青龙之心", spellIDs = { 443421, 443616 } },
    [6] = { description = "活力苏醒", spellIDs = { 392883 } },
}

addonTable.SPEC.TargetDebuff = {
}
