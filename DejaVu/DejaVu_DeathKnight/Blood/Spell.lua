-- luacheck: globals C_SpellActivationOverlay
local addonName, addonTable             = ...          -- luacheck: ignore addonName

local insert                            = table.insert -- 表插入

-- WoW 官方 API
local UnitClass                         = UnitClass
local GetSpecialization                 = GetSpecialization
-- 专精错误则停止
local className, classFilename, classId = UnitClass("player")
local currentSpec                       = GetSpecialization()
if classFilename ~= "DEATHKNIGHT" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是死亡骑士则停止
if currentSpec ~= 1 then return end -- 不是鲜血专精则停止
-- DejaVu Core
local DejaVu = _G["DejaVu"]
local cooldownSpells = DejaVu.cooldownSpells
local chargeSpells = DejaVu.chargeSpells

DejaVu.useCustomSpell = true

insert(cooldownSpells, { spellID = 46585, name = "亡者复生" }) --  亡者复生
insert(cooldownSpells, { spellID = 48792, name = "冰封之韧" }) --  [冰封之韧]
insert(cooldownSpells, { spellID = 48707, name = "反魔法护罩" }) --  [反魔法护罩]
insert(cooldownSpells, { spellID = 51052, name = "反魔法领域" }) --  [反魔法领域]
insert(cooldownSpells, { spellID = 61999, name = "复活盟友" }) --  [复活盟友]
insert(cooldownSpells, { spellID = 47528, name = "心灵冰冻" }) --  [心灵冰冻]
insert(cooldownSpells, { spellID = 49998, name = "灵界打击" }) --  [灵界打击]
insert(cooldownSpells, { spellID = 207167, name = "致盲冰雨" }) --  [致盲冰雨]
insert(cooldownSpells, { spellID = 55233, name = "吸血鬼之血" }) --  [吸血鬼之血]
insert(cooldownSpells, { spellID = 206930, name = "心脏打击" }) --  [心脏打击]
insert(cooldownSpells, { spellID = 1263569, name = "憎恶附肢" }) --  [憎恶附肢]
insert(cooldownSpells, { spellID = 439843, name = "死神印记" }) --  [死神印记]
insert(cooldownSpells, { spellID = 195292, name = "死神的抚摩" }) --  [死神的抚摩]
insert(cooldownSpells, { spellID = 49028, name = "符文刃舞" }) --  [符文刃舞]
insert(cooldownSpells, { spellID = 195182, name = "精髓分裂" }) --  [精髓分裂]


insert(chargeSpells, { spellID = 43265, name = "枯萎凋零" }) --  [枯萎凋零]
insert(chargeSpells, { spellID = 49576, name = "死亡之握" }) --  [死亡之握]
insert(chargeSpells, { spellID = 48265, name = "死亡脚步" }) --  [死亡脚步]
insert(chargeSpells, { spellID = 50842, name = "血液沸腾" }) --  [血液沸腾]
