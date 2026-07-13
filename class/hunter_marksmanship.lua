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
if currentSpec ~= 2 then return end

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
    [11] = { spellId = 147362, description = "反制射击" },
    [12] = { spellId = 19434, description = "瞄准射击" },
    [13] = { spellId = 257044, description = "急速射击" },
    [14] = { spellId = 288613, description = "百发百中" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 19434, description = "瞄准射击", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
