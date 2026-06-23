-- luacheck: globals C_SpellActivationOverlay
local addonName, addonTable             = ...          -- luacheck: ignore addonName

local insert                            = table.insert -- 表插入

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "PRIEST" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是牧师则停止
if currentSpec ~= 1 then return end -- 不是戒律专精则停止
-- DejaVu Core
local DejaVu = _G["DejaVu"]
local cooldownSpells = DejaVu.cooldownSpells
local chargeSpells = DejaVu.chargeSpells

DejaVu.useCustomSpell = true

insert(cooldownSpells, { spellID = 17, name = "真言术：盾" })
insert(cooldownSpells, { spellID = 472433, name = "福音" })
insert(cooldownSpells, { spellID = 10060, name = "能量灌注" })
insert(cooldownSpells, { spellID = 589, name = "暗言术：痛" })
insert(cooldownSpells, { spellID = 586, name = "渐隐术" })
insert(cooldownSpells, { spellID = 19236, name = "绝望祷言" })
insert(cooldownSpells, { spellID = 200829, name = "恳求" })
insert(cooldownSpells, { spellID = 2061, name = "快速治疗" })
insert(cooldownSpells, { spellID = 585, name = "惩击" })



insert(chargeSpells, { spellID = 47540, name = "苦修" })
insert(chargeSpells, { spellID = 8092, name = "心灵震爆" })
insert(chargeSpells, { spellID = 194509, name = "真言术：耀" })
insert(chargeSpells, { spellID = 32379, name = "暗言术：灭" })
insert(chargeSpells, { spellID = 527, name = "纯净术" })
insert(chargeSpells, { spellID = 33206, name = "痛苦压制" })
