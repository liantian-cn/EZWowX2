-- luacheck: globals C_SpellActivationOverlay
local addonName, addonTable             = ...          -- luacheck: ignore addonName

local insert                            = table.insert -- 表插入

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DEMONHUNTER" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是恶魔猎手则停止
if currentSpec ~= 3 then return end -- 不是噬灭专精则停止
-- DejaVu Core
local DejaVu = _G["DejaVu"]
local cooldownSpells = DejaVu.cooldownSpells
local chargeSpells = DejaVu.chargeSpells



insert(cooldownSpells, { spellID = 473662, name = "吞噬" }) --  [吞噬]
insert(cooldownSpells, { spellID = 1226019, name = "收割" }) --  [收割]
insert(cooldownSpells, { spellID = 473728, name = "虚空射线" }) --  [虚空射线]
insert(cooldownSpells, { spellID = 1225826, name = "根除" }) --  [根除]
insert(cooldownSpells, { spellID = 1217605, name = "虚空变形" }) --  [虚空变形]
insert(cooldownSpells, { spellID = 1221150, name = "坍缩之星" }) --  [坍缩之星]
insert(cooldownSpells, { spellID = 183752, name = "瓦解" }) --  [瓦解]
insert(cooldownSpells, { spellID = 198589, name = "疾影" }) --  [疾影]
