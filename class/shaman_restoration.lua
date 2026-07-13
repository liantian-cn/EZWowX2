-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "SHAMAN" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 57994, description = "风剪" },
    [3] = { spellId = 198103, description = "土元素" },
    [4] = { spellId = 192058, description = "电能图腾" },
    [5] = { spellId = 378081, description = "自然迅捷" },
    [6] = { spellId = 108287, description = "图腾投射" },
    [7] = { spellId = 51514, description = "妖术" },
    [8] = { spellId = 378773, description = "强化净化术" },
    [9] = { spellId = 8143, description = "战栗图腾" },
    [10] = { spellId = 383013, description = "清毒图腾" },
    [11] = { spellId = 192063, description = "阵风" },
    [12] = { spellId = 58875, description = "幽魂步" },
    [13] = { spellId = 51505, description = "熔岩爆裂" },
    [14] = { spellId = 61295, description = "激流" },
    [15] = { spellId = 5394, description = "治疗之泉图腾" },
    [16] = { spellId = 470411, description = "烈焰震击" },
    [17] = { spellId = 77130, description = "净化灵魂" },
    [18] = { spellId = 73685, description = "生命释放" },
    [19] = { spellId = 443454, description = "先祖迅捷" },
    [20] = { spellId = 444995, description = "涌动图腾" },
    [21] = { spellId = 98008, description = "灵魂链接图腾" },
    [22] = { spellId = 114052, description = "升腾" },
    [23] = { spellId = 108280, description = "治疗之潮图腾" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 51505, description = "熔岩爆裂", minValue = 0, maxValue = 8 },
    [2] = { spellId = 61295, description = "激流", minValue = 0, maxValue = 2 },
    [3] = { spellId = 5394, description = "治疗之泉图腾", minValue = 0, maxValue = 4 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
