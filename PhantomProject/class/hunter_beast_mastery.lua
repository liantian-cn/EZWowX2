-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "HUNTER" then return end
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 53480, description = "牺牲咆哮" },
    [3] = { spellId = 109304, description = "意气风发" },
    [4] = { spellId = 19577, description = "胁迫" },
    [5] = { spellId = 5116, description = "震荡射击" },
    [6] = { spellId = 19801, description = "宁神射击" },
    [7] = { spellId = 187698, description = "焦油陷进" },
    [8] = { spellId = 1513, description = "恐吓野兽" },
    [9] = { spellId = 109248, description = "束缚射击" },
    [10] = { spellId = 195645, description = "摔绊" },
    [11] = { spellId = 34026, description = "杀戮命令" },
    [12] = { spellId = 217200, description = "倒刺射击" },
    [13] = { spellId = 147362, description = "反制射击" },
    [14] = { spellId = 19574, description = "狂野怒火" },
    [15] = { spellId = 1264359, description = "狂野鞭笞" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 34026, description = "杀戮命令", minValue = 0, maxValue = 8 },
    [2] = { spellId = 217200, description = "倒刺射击", minValue = 0, maxValue = 8 },
}

addonTable.SPEC.PlayerBuff = {
    [1] = { description = "自然之友", spellIDs = { 1276720 } },
    [2] = { description = "狂野怒火", spellIDs = { 19574 } },
}

addonTable.SPEC.TargetDebuff = {
}
