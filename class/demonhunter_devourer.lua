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
if currentSpec ~= 3 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 196718, description = "黑暗" },
    [3] = { spellId = 198793, description = "复仇回避" },
    [4] = { spellId = 185123, description = "投掷利刃" },
    [5] = { spellId = 207684, description = "悲苦咒符" },
    [6] = { spellId = 217832, description = "禁锢" },
    [7] = { spellId = 258920, description = "献祭光环" },
    [8] = { spellId = 1234195, description = "虚空新星" },
    [9] = { spellId = 1217605, description = "虚空变形" },
    [10] = { spellId = 1245412, description = "虚空之刃" },
    [11] = { spellId = 1234796, description = "变换" },
    [12] = { spellId = 1226019, description = "收割" },
    [13] = { spellId = 473662, description = "吞噬" },
    [14] = { spellId = 198589, description = "疾影" },
    [15] = { spellId = 473728, description = "虚空射线" },
    [16] = { spellId = 1246167, description = "恶魔追击" },
    [17] = { spellId = 1239123, description = "饥渴斩击" },
    [18] = { spellId = 1245453, description = "剔除" },
}

-- Entries without a source charge count bar use the user-approved Phantom 0..8 fallback.
addonTable.SPEC.ChargeList = {
    [1] = { spellId = 185123, description = "投掷利刃", minValue = 0, maxValue = 8 },
    [2] = { spellId = 1234796, description = "变换", minValue = 0, maxValue = 8 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
