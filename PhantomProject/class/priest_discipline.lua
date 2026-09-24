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
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 8122, description = "心灵尖啸" },
    [3] = { spellId = 32375, description = "群体驱散" },
    [4] = { spellId = 527, description = "纯净术" },
    [5] = { spellId = 19236, description = "绝望祷言" },
    [6] = { spellId = 232633, description = "奥术洪流" },
    [7] = { spellId = 47540, description = "苦修" },
    [8] = { spellId = 194509, description = "真言术：耀" },
    [9] = { spellId = 17, description = "真言术：盾" },
    [10] = { spellId = 62618, description = "真言术：障" },
    [11] = { spellId = 421453, description = "终极苦修" },
    [12] = { spellId = 472433, description = "福音" },
    [13] = { spellId = 8092, description = "心灵震爆" },
    [14] = { spellId = 32379, description = "暗言术：灭" },
    [15] = { spellId = 34433, description = "暗影魔" },
    [16] = { spellId = 1235211, description = "暗影分流" },
    [17] = { spellId = 586, description = "渐隐术" },
}

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 47540, description = "苦修", minValue = 0, maxValue = 2 },
    [2] = { spellId = 194509, description = "真言术：耀", minValue = 0, maxValue = 2 },
}

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "虚空之盾", spellIDs = { 1253591 } },
    [2] = { description = "圣光涌动", spellIDs = { 114255 } },
    [3] = { description = "暗影愈合", spellIDs = { 1252217 } },
    [4] = { description = "福音", spellIDs = { 472433 } },
    [5] = { description = "祸福相依", spellIDs = { 390787 } },
}

addonTable.SPEC.TargetDebuff = {
}
