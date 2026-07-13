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
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 121253, description = "醉酿投" },
    [3] = { spellId = 119582, description = "活血酒" },
    [4] = { spellId = 322507, description = "天神酒" },
    [5] = { spellId = 1241059, description = "天神灌注" },
    [6] = { spellId = 322109, description = "轮回之触" },
    [7] = { spellId = 119381, description = "扫堂腿" },
    [8] = { spellId = 322101, description = "移花接木" },
    [9] = { spellId = 101643, description = "魂体双分" },
    [10] = { spellId = 119996, description = "魂体双分：转移" },
    [11] = { spellId = 116705, description = "切喉手" },
    [12] = { spellId = 115181, description = "火焰之息" },
    [13] = { spellId = 123986, description = "真气爆裂" },
    [14] = { spellId = 325153, description = "爆炸酒桶" },
    [15] = { spellId = 198898, description = "赤精之歌" },
    [16] = { spellId = 115399, description = "玄牛酒" },
    [17] = { spellId = 116844, description = "平心之环" },
    [18] = { spellId = 115078, description = "分筋错骨" },
    [19] = { spellId = 132578, description = "玄牛下凡" },
    [20] = { spellId = 205523, description = "幻灭踢" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 121253, description = "醉酿投", minValue = 0, maxValue = 8 },
    [2] = { spellId = 119582, description = "活血酒", minValue = 0, maxValue = 8 },
    [3] = { spellId = 322507, description = "天神酒", minValue = 0, maxValue = 8 },
    [4] = { spellId = 1241059, description = "天神灌注", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
