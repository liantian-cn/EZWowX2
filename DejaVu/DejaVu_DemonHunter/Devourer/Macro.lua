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
if classFilename ~= "DEMONHUNTER" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是恶魔猎手则停止
if currentSpec ~= 3 then return end -- 不是噬灭专精则停止


local macroList = {}
insert(macroList, { title = "reloadUI", key = "CTRL-F12", text = "/reload" })
insert(macroList, { title = "target吞噬", key = "ALT-NUMPAD1", text = "/cast [@target] 吞噬" })
insert(macroList, { title = "focus吞噬", key = "ALT-NUMPAD2", text = "/cast [@focus] 吞噬" })
insert(macroList, { title = "就近吞噬", key = "ALT-NUMPAD3", text = "/cleartarget \n/targetenemy [noharm][dead][noexists][help] \n/cast [nocombat] 就近吞噬 \n/stopmacro [channeling] \n/startattack \n/cast [harm]就近吞噬 \n/targetlasttarget" })
insert(macroList, { title = "target收割", key = "ALT-NUMPAD4", text = "/cast [@target] 收割" })
insert(macroList, { title = "虚空射线", key = "ALT-NUMPAD5", text = "/cast 虚空射线" })
insert(macroList, { title = "target根除", key = "ALT-NUMPAD6", text = "/cast [@target] 根除" })
insert(macroList, { title = "虚空变形", key = "ALT-NUMPAD7", text = "/cast 虚空变形" })
insert(macroList, { title = "target坍缩之星", key = "ALT-NUMPAD8", text = "/cast [@target] 坍缩之星" })
insert(macroList, { title = "target瓦解", key = "ALT-NUMPAD9", text = "/cast [@target] 瓦解" })
insert(macroList, { title = "focus瓦解", key = "ALT-NUMPAD0", text = "/cast [@focus] 瓦解" })
insert(macroList, { title = "疾影", key = "SHIFT-NUMPAD1", text = "/cast 疾影" })


for _, macro in pairs(macroList) do
    local buttonName = addonName .. "Button" .. macro.title
    local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
    frame:SetAttribute("type", "macro")
    frame:SetAttribute("macrotext", macro.text)
    frame:RegisterForClicks("AnyDown", "AnyUp")
    SetOverrideBindingClick(frame, true, macro.key, buttonName)
    print("RegMacro[" .. macro.title .. "] > " .. macro.key .. " > " .. macro.text)
end
