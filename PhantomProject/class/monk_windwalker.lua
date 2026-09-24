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
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 122470, description = "业报之触" },
    [3] = { spellId = 107428, description = "旭日东升踢" },
    [4] = { spellId = 1249625, description = "乾元之巅" },
    [5] = { spellId = 218164, description = "清创生血" },
    [6] = { spellId = 152175, description = "升龙霸" },
    [7] = { spellId = 101545, description = "翔龙在天" },
    [8] = { spellId = 113656, description = "怒雷破" },
    [9] = { spellId = 322109, description = "轮回之触" },
    [10] = { spellId = 119381, description = "扫堂腿" },
    [11] = { spellId = 322101, description = "移花接木" },
    [12] = { spellId = 101643, description = "魂体双分" },
    [13] = { spellId = 119996, description = "魂体双分：转移" },
    [14] = { spellId = 116705, description = "切喉手" },
    [15] = { spellId = 198898, description = "赤精之歌" },
    [16] = { spellId = 116844, description = "平心之环" },
    [17] = { spellId = 115078, description = "分筋错骨" },
}

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 1249625, description = "乾元之巅", minValue = 0, maxValue = 2 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
