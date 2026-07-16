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
if currentSpec ~= 2 then return end

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
    [13] = { spellId = 196277, description = "内爆" },
    [14] = { spellId = 265187, description = "召唤恶魔暴君" },
    [15] = { spellId = 1276467, description = "魔典：邪能破坏者" },
    [16] = { spellId = 105174, description = "古尔丹之手" },
    [17] = { spellId = 1276672, description = "召唤末日守卫" },
    [18] = { spellId = 104316, description = "召唤恐惧猎犬" },
    [19] = { spellId = 264187, description = "恶魔之箭" },
    [20] = { spellId = 1276452, description = "魔典：小鬼领主" },
    [21] = { spellId = 388215, description = "吞噬魔法" },
    [22] = { spellId = 30146, description = "召唤恶魔卫士" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
