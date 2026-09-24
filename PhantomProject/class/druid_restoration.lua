-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "DRUID" then return end
if currentSpec ~= 4 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 22812, description = "树皮术" },
    [3] = { spellId = 132469, description = "台风" },
    [4] = { spellId = 99, description = "夺魂咆哮" },
    [5] = { spellId = 29166, description = "激活" },
    [6] = { spellId = 102793, description = "乌索尔旋风" },
    [7] = { spellId = 18562, description = "迅捷治愈" },
    [8] = { spellId = 48438, description = "野性成长" },
    [9] = { spellId = 391528, description = "万灵之召" },
    [10] = { spellId = 88423, description = "自然之愈" },
    [11] = { spellId = 102342, description = "铁木树皮" },
    [12] = { spellId = 132158, description = "自然迅捷" },
    [13] = { spellId = 1261867, description = "野性之心" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 18562, description = "迅捷治愈", minValue = 0, maxValue = 8 },
}

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "节能施法", spellIDs = { 16870 } },
    [2] = { description = "丛林之魂", spellIDs = { 114108 } },
}

addonTable.SPEC.TargetDebuff = {
}
