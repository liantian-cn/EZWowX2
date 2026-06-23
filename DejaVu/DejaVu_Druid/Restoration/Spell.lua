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
end                                 -- 不是死亡骑士则停止
if currentSpec ~= 4 then return end -- 不是鲜血专精则停止
-- DejaVu Core
local DejaVu = _G["DejaVu"]
local cooldownSpells = DejaVu.cooldownSpells
local chargeSpells = DejaVu.chargeSpells

DejaVu.useCustomSpell = true

insert(cooldownSpells, { spellID = 102793, name = "乌索尔旋风" }) --  [乌索尔旋风]
insert(cooldownSpells, { spellID = 474750, name = "共生关系" }) --  [共生关系]
insert(cooldownSpells, { spellID = 1079, name = "割裂" }) -- [割裂]
insert(cooldownSpells, { spellID = 132469, name = "台风" }) --  [台风]
insert(cooldownSpells, { spellID = 774, name = "回春术" }) --  [回春术]
insert(cooldownSpells, { spellID = 210053, name = "坐骑形态" }) --  [坐骑形态]
insert(cooldownSpells, { spellID = 20484, name = "复生" }) --  [复生]
insert(cooldownSpells, { spellID = 99, name = "夺魂咆哮" }) --  [夺魂咆哮]
insert(cooldownSpells, { spellID = 2908, name = "安抚" }) --  [安抚]
insert(cooldownSpells, { spellID = 1850, name = "急奔" }) --  [急奔]
insert(cooldownSpells, { spellID = 8936, name = "愈合" }) --  [愈合]
insert(cooldownSpells, { spellID = 5176, name = "愤怒" }) --  [愤怒]
insert(cooldownSpells, { spellID = 1822, name = "斜掠" }) --  [斜掠]
insert(cooldownSpells, { spellID = 5221, name = "撕碎" }) --  [撕碎]
insert(cooldownSpells, { spellID = 783, name = "旅行形态" }) --  [旅行形态]
insert(cooldownSpells, { spellID = 8921, name = "月火术" }) --  [月火术]
insert(cooldownSpells, { spellID = 22812, name = "树皮术" }) --  [树皮术]
insert(cooldownSpells, { spellID = 29166, name = "激活" }) --  [激活]
insert(cooldownSpells, { spellID = 5487, name = "熊形态" }) --  [熊形态]
insert(cooldownSpells, { spellID = 106898, name = "狂奔怒吼" }) --  [狂奔怒吼]
insert(cooldownSpells, { spellID = 1261867, name = "野性之心" }) --  [野性之心]
insert(cooldownSpells, { spellID = 1126, name = "野性印记" }) --  [野性印记]
insert(cooldownSpells, { spellID = 391528, name = "万灵之召" }) --  [万灵之召]
insert(cooldownSpells, { spellID = 740, name = "宁静" }) --  [宁静]
insert(cooldownSpells, { spellID = 33763, name = "生命绽放" }) --  [生命绽放]
insert(cooldownSpells, { spellID = 132158, name = "自然迅捷" }) --  [自然迅捷]
insert(cooldownSpells, { spellID = 102342, name = "铁木树皮" }) --  [铁木树皮]
insert(cooldownSpells, { spellID = 48438, name = "野性生长" }) --  [野性生长]


insert(chargeSpells, { spellID = 22842, name = "狂暴回复" }) --  [狂暴回复]
insert(chargeSpells, { spellID = 88423, name = "自然之愈" }) --  [自然之愈]
insert(chargeSpells, { spellID = 18562, name = "迅捷治愈" }) --  [迅捷治愈]
