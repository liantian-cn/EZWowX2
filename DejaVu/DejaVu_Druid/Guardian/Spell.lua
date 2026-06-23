-- luacheck: globals C_SpellActivationOverlay
local addonName, addonTable             = ...          -- luacheck: ignore addonName

local insert                            = table.insert -- 表插入

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DRUID" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是德鲁伊则停止
if currentSpec ~= 3 then return end -- 不是守护专精则停止
-- DejaVu Core
local DejaVu = _G["DejaVu"]
local cooldownSpells = DejaVu.cooldownSpells
local chargeSpells = DejaVu.chargeSpells

DejaVu.useCustomSpell = true


insert(cooldownSpells, { spellID = 102793, name = "乌索尔旋风" }) --  [乌索尔旋风]
insert(cooldownSpells, { spellID = 6795, name = "低吼" }) --  [低吼]
insert(cooldownSpells, { spellID = 132469, name = "台风" }) --  [台风]
insert(cooldownSpells, { spellID = 210053, name = "坐骑形态" }) --  [坐骑形态]
insert(cooldownSpells, { spellID = 20484, name = "复生" }) --  [复生]
insert(cooldownSpells, { spellID = 99, name = "夺魂咆哮" }) --  [夺魂咆哮]
insert(cooldownSpells, { spellID = 2908, name = "安抚" }) --  [安抚]
insert(cooldownSpells, { spellID = 8936, name = "愈合" }) --  [愈合]
insert(cooldownSpells, { spellID = 783, name = "旅行形态" }) --  [旅行形态]
insert(cooldownSpells, { spellID = 8921, name = "月火术" }) --  [月火术]
insert(cooldownSpells, { spellID = 22812, name = "树皮术" }) --  [树皮术]
insert(cooldownSpells, { spellID = 213771, name = "横扫" }) --  [横扫]
insert(cooldownSpells, { spellID = 2782, name = "清除腐蚀" }) --  [清除腐蚀]
insert(cooldownSpells, { spellID = 5487, name = "熊形态" }) --  [熊形态]
insert(cooldownSpells, { spellID = 77761, name = "狂奔怒吼" }) --  [狂奔怒吼]
insert(cooldownSpells, { spellID = 77758, name = "痛击" }) --  [痛击]
insert(cooldownSpells, { spellID = 16979, name = "野性冲锋" }) --  [野性冲锋]
insert(cooldownSpells, { spellID = 1126, name = "野性印记" }) --  [野性印记]
insert(cooldownSpells, { spellID = 192081, name = "铁鬃" }) --  [铁鬃]
insert(cooldownSpells, { spellID = 102558, name = "狂暴" }) --  [化身：乌索克的守护者]
insert(cooldownSpells, { spellID = 204066, name = "明月普照" }) --  [明月普照]
insert(cooldownSpells, { spellID = 106839, name = "迎头痛击" }) --  [迎头痛击]
insert(cooldownSpells, { spellID = 6807, name = "重殴" }) --  [重殴]
insert(cooldownSpells, { spellID = 1261867, name = "野性之心" }) -- [野性之心]
insert(cooldownSpells, { spellID = 391528, name = "万灵之召" }) --  [万灵之召]
insert(cooldownSpells, { spellID = 1253799, name = "碎甲咆哮" }) --  [碎甲咆哮]


insert(chargeSpells, { spellID = 22842, name = "狂暴回复" }) --  [狂暴回复]
insert(chargeSpells, { spellID = 33917, name = "裂伤" }) --  [裂伤]
insert(chargeSpells, { spellID = 61336, name = "生存本能" }) --  [生存本能]
-- insert(chargeSpells, { spellID = 61336, name = "生存本能" }) --  [生存本能]
