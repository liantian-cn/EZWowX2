-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local GetSpecialization = GetSpecialization
local UnitClassBase = UnitClassBase

-- Addon-level variable definitions/references

-- Local variables
local currentSpec = GetSpecialization()

-- Code
if UnitClassBase("player") ~= "DEMONHUNTER" then return end
if currentSpec ~= 1 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 196718, description = "黑暗" },
    [3] = { spellId = 198793, description = "复仇回避" },
    [4] = { spellId = 185123, description = "投掷利刃" },
    [5] = { spellId = 207684, description = "悲苦咒符" },
    [6] = { spellId = 217832, description = "禁锢" },
    [7] = { spellId = 258920, description = "献祭光环" },
    [8] = { spellId = 179057, description = "混乱新星" },
    [9] = { spellId = 191427, description = "恶魔变形" },
    [10] = { spellId = 232893, description = "邪能之刃" },
    [11] = { spellId = 188499, description = "刃舞" },
    [12] = { spellId = 162794, description = "混乱打击" },
    [13] = { spellId = 198589, description = "疾影" },
    [14] = { spellId = 370965, description = "恶魔追击" },
    [15] = { spellId = 198013, description = "眼棱" },
    [16] = { spellId = 195072, description = "邪能冲撞" },
    [17] = { spellId = 258860, description = "精华破碎" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 185123, description = "投掷利刃", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
