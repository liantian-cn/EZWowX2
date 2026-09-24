-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "WARLOCK" then return end
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 5782, description = "恐惧" },
    [3] = { spellId = 6789, description = "死亡缠绕" },
    [4] = { spellId = 20707, description = "灵魂石" },
    [5] = { spellId = 30283, description = "暗影之怒" },
    [6] = { spellId = 333889, description = "邪能统御" },
    [7] = { spellId = 108416, description = "黑暗契约" },
    [8] = { spellId = 111771, description = "恶魔传送门" },
    [9] = { spellId = 127174, description = "虚弱灾厄" },
    [10] = { spellId = 1271802, description = "语言灾厄" },
    [11] = { spellId = 48018, description = "恶魔法阵" },
    [12] = { spellId = 48020, description = "恶魔法阵：传送" },
    [13] = { spellId = 1122, description = "召唤地狱火" },
    [14] = { spellId = 6353, description = "灵魂之火" },
    [15] = { spellId = 17962, description = "燃烧" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 17962, description = "燃烧", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
