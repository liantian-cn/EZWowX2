-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "EVOKER" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 365585, description = "净除" },
    [3] = { spellId = 363916, description = "黑曜鳞片" },
    [4] = { spellId = 358385, description = "山崩" },
    [5] = { spellId = 360995, description = "青翠之拥" },
    [6] = { spellId = 357210, description = "深呼吸" },
    [7] = { spellId = 374227, description = "微风" },
    [8] = { spellId = 358267, description = "悬空" },
    [9] = { spellId = 368970, description = "扫尾" },
    [10] = { spellId = 370553, description = "扭转天平" },
    [11] = { spellId = 370665, description = "营救" },
    [12] = { spellId = 374968, description = "时间螺旋" },
    [13] = { spellId = 406732, description = "空间悖论" },
    [14] = { spellId = 357208, description = "火焰吐息" },
    [15] = { spellId = 396286, description = "地壳激变" },
    [16] = { spellId = 409311, description = "先知先觉" },
    [17] = { spellId = 395152, description = "黑檀之力" },
    [18] = { spellId = 442204, description = "亘古吐息" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 363916, description = "黑曜鳞片", minValue = 0, maxValue = 8 },
    [2] = { spellId = 358267, description = "悬空", minValue = 0, maxValue = 8 },
    [3] = { spellId = 409311, description = "先知先觉", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
