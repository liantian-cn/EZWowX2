-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "ROGUE" then return end
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 5938, description = "毒刃" },
    [3] = { spellId = 2094, description = "致盲" },
    [4] = { spellId = 1966, description = "佯攻" },
    [5] = { spellId = 1856, description = "消失" },
    [6] = { spellId = 1833, description = "偷袭" },
    [7] = { spellId = 114018, description = "潜伏帷幕" },
    [8] = { spellId = 381623, description = "菊花茶" },
    [9] = { spellId = 5277, description = "闪避" },
    [10] = { spellId = 185311, description = "猩红之瓶" },
    [11] = { spellId = 1725, description = "扰乱" },
    [12] = { spellId = 2983, description = "疾跑" },
    [13] = { spellId = 1776, description = "凿击" },
    [14] = { spellId = 408, description = "肾击" },
    [15] = { spellId = 31224, description = "暗影斗篷" },
    [16] = { spellId = 1766, description = "脚踢" },
    [17] = { spellId = 360194, description = "死亡印记" },
    [18] = { spellId = 1293340, description = "死亡印记" },
    [19] = { spellId = 703, description = "锁喉" },
    [20] = { spellId = 385627, description = "君王之灾" },
    [21] = { spellId = 36554, description = "暗影步" },
}

addonTable.SPEC.ChargeList = {
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
