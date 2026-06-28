if UnitClassBase("player") ~= "DEMONHUNTER" then return end

local addonName, addonTable = ...

local currentSpec           = GetSpecialization()

if currentSpec == 2 then -- 复仇专精
    addonTable.ClassSpells = {
        [1] = { spellId = 196718, name = "黑暗" },
        [2] = { spellId = 198793, name = "复仇回避" },
        [3] = { spellId = 185123, name = "投掷利刃 " },
        [4] = { spellId = 185123, name = "投掷利刃", charge = true },
        [5] = { spellId = 207684, name = "悲苦咒符" },
        [6] = { spellId = 217832, name = "禁锢" },
        [7] = { spellId = 258920, name = "献祭光环" },
        [8] = { spellId = 179057, name = "混乱新星" },
        [9] = { spellId = 187827, name = "恶魔变形" },
        [10] = { spellId = 232893, name = "邪能之刃" },
        [11] = { spellId = 189110, name = "地狱火撞击" },
        [12] = { spellId = 189110, name = "地狱火撞击", charge = true },
        [13] = { spellId = 203720, name = "恶魔尖刺" },
        [14] = { spellId = 204021, name = "烈火烙印" },
        [15] = { spellId = 204021, name = "烈火烙印", charge = true },
        [16] = { spellId = 247454, name = "幽魂炸弹" },
        [17] = { spellId = 207407, name = "灵魂切削" },
        [18] = { spellId = 204596, name = "烈焰咒符" },
        [19] = { spellId = 390163, name = "怨念咒符" },
        [20] = { spellId = 228447, name = "灵魂裂劈" },
        [21] = { spellId = 263642, name = "破裂" },
        [22] = { spellId = 263642, name = "破裂", charge = true },
        [23] = { spellId = 212084, name = "邪能毁灭" },
        [24] = { spellId = 202137, name = "沉默咒符" },
    }
end
