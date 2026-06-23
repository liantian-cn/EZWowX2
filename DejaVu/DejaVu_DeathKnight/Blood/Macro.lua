local addonName, addonTable = ... -- 插件入口固定写法


-- Lua 原生函数
local insert                            = table.insert
local pairs                             = pairs

-- WoW 官方 API
local CreateFrame                       = CreateFrame
local SetOverrideBindingClick           = SetOverrideBindingClick
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


local macroList = {}
insert(macroList, { title = "reloadUI", key = "CTRL-F12", text = "/reload" })
insert(macroList, { title = "target灵界打击", key = "ALT-NUMPAD1", text = "/cast [@target] 灵界打击" })
insert(macroList, { title = "focus灵界打击", key = "ALT-NUMPAD2", text = "/cast [@focus] 灵界打击" })
insert(macroList, { title = "target精髓分裂", key = "ALT-NUMPAD3", text = "/cast [@target] 精髓分裂" })
insert(macroList, { title = "focus精髓分裂", key = "ALT-NUMPAD4", text = "/cast [@focus] 精髓分裂" })
insert(macroList, { title = "target死神印记", key = "ALT-NUMPAD5", text = "/cast [@target] 死神印记" })
insert(macroList, { title = "focus死神印记", key = "ALT-NUMPAD6", text = "/cast [@focus] 死神印记" })
insert(macroList, { title = "target心脏打击", key = "ALT-NUMPAD7", text = "/cast [@target] 心脏打击" })
insert(macroList, { title = "focus心脏打击", key = "ALT-NUMPAD8", text = "/cast [@focus] 心脏打击" })
insert(macroList, { title = "target心灵冰冻", key = "ALT-NUMPAD9", text = "/cast [@target] 心灵冰冻" })
insert(macroList, { title = "focus心灵冰冻", key = "ALT-NUMPAD0", text = "/cast [@focus] 心灵冰冻" })
insert(macroList, { title = "就近灵界打击", key = "SHIFT-NUMPAD1", text = "/cleartarget \n/targetenemy [noharm][dead][noexists][help] \n/cast [nocombat] 灵界打击 \n/stopmacro [channeling] \n/startattack \n/cast [harm]灵界打击 \n/targetlasttarget" })
insert(macroList, { title = "就近心脏打击", key = "SHIFT-NUMPAD2", text = "/cleartarget \n/targetenemy [noharm][dead][noexists][help] \n/cast [nocombat] 心脏打击 \n/stopmacro [channeling] \n/startattack \n/cast [harm]心脏打击 \n/targetlasttarget" })
insert(macroList, { title = "死神的抚摩", key = "SHIFT-NUMPAD3", text = "/cast 死神的抚摩" })
insert(macroList, { title = "player枯萎凋零", key = "SHIFT-NUMPAD4", text = "/cast [@player] 枯萎凋零" })
insert(macroList, { title = "血液沸腾", key = "SHIFT-NUMPAD5", text = "/cast 血液沸腾" })
insert(macroList, { title = "亡者复生", key = "SHIFT-NUMPAD6", text = "/cast 亡者复生" })
insert(macroList, { title = "cursor枯萎凋零", key = "SHIFT-NUMPAD7", text = "/cast [@cursor] 枯萎凋零" })
insert(macroList, { title = "target符文刃舞", key = "SHIFT-NUMPAD8", text = "/cast [@target] 符文刃舞" })
insert(macroList, { title = "focus符文刃舞", key = "SHIFT-NUMPAD9", text = "/cast [@focus] 符文刃舞" })


for _, macro in pairs(macroList) do
    local buttonName = addonName .. "Button" .. macro.title
    local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
    frame:SetAttribute("type", "macro")
    frame:SetAttribute("macrotext", macro.text)
    frame:RegisterForClicks("AnyDown", "AnyUp")
    SetOverrideBindingClick(frame, true, macro.key, buttonName)
    print("RegMacro[" .. macro.title .. "] > " .. macro.key .. " > " .. macro.text)
end
