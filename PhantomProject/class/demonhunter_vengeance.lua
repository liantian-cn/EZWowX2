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
if currentSpec ~= 2 then return end

addonTable.SPEC.SpellList = {
    [1] = { spellId = 61304, description = "公共冷却" },
    [2] = { spellId = 196718, description = "黑暗" },
    [3] = { spellId = 198793, description = "复仇回避" },
    [4] = { spellId = 185123, description = "投掷利刃" },
    [5] = { spellId = 207684, description = "悲苦咒符" },
    [6] = { spellId = 217832, description = "禁锢" },
    [7] = { spellId = 258920, description = "献祭光环" },
    [8] = { spellId = 179057, description = "混乱新星" },
    [9] = { spellId = 187827, description = "恶魔变形" },
    [10] = { spellId = 232893, description = "邪能之刃" },
    [11] = { spellId = 189110, description = "地狱火撞击" },
    [12] = { spellId = 203720, description = "恶魔尖刺" },
    [13] = { spellId = 204021, description = "烈火烙印" },
    [14] = { spellId = 247454, description = "幽魂炸弹" },
    [15] = { spellId = 207407, description = "灵魂切削" },
    [16] = { spellId = 204596, description = "烈焰咒符" },
    [17] = { spellId = 390163, description = "怨念咒符" },
    [18] = { spellId = 228447, description = "灵魂裂劈" },
    [19] = { spellId = 263642, description = "破裂" },
    [20] = { spellId = 212084, description = "邪能毁灭" },
    [21] = { spellId = 202137, description = "沉默咒符" },
}

addonTable.SPEC.ChargeList = {
    [1] = { spellId = 185123, description = "投掷利刃", minValue = 0, maxValue = 2 },
    [2] = { spellId = 189110, description = "地狱火撞击", minValue = 0, maxValue = 2 },
    [3] = { spellId = 204021, description = "烈火烙印", minValue = 0, maxValue = 2 },
    [4] = { spellId = 263642, description = "破裂", minValue = 0, maxValue = 2 },
}

-- These tables are intentionally empty because Fuyutsui provides no finite static player-buff or player-origin target-debuff ID lists to port.
addonTable.SPEC.PlayerBuff = {
}

addonTable.SPEC.TargetDebuff = {
}
