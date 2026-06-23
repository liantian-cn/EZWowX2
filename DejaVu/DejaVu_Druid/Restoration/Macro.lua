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
if classFilename ~= "DRUID" then
    C_AddOns.DisableAddOn(addonName)
    return
end                                 -- 不是德鲁伊则停止
if currentSpec ~= 4 then return end -- 不是恢复专精则停止


local macroList = {}
insert(macroList, { title = "reloadUI", key = "CTRL-F12", text = "/reload" })
insert(macroList, { title = "player铁木树皮", key = "ALT-NUMPAD1", text = "/focus player \n/cast [@player] 铁木树皮" })
insert(macroList, { title = "party1铁木树皮", key = "ALT-NUMPAD2", text = "/focus party1 \n/cast [@party1] 铁木树皮" })
insert(macroList, { title = "party2铁木树皮", key = "ALT-NUMPAD3", text = "/focus party2 \n/cast [@party2] 铁木树皮" })
insert(macroList, { title = "party3铁木树皮", key = "ALT-NUMPAD4", text = "/focus party3 \n/cast [@party3] 铁木树皮" })
insert(macroList, { title = "party4铁木树皮", key = "ALT-NUMPAD5", text = "/focus party4 \n/cast [@party4] 铁木树皮" })
insert(macroList, { title = "player自然之愈", key = "ALT-NUMPAD6", text = "/cast [@player] 自然之愈" })
insert(macroList, { title = "party1自然之愈", key = "ALT-NUMPAD7", text = "/focus party1 \n/cast [@party1] 自然之愈" })
insert(macroList, { title = "party2自然之愈", key = "ALT-NUMPAD8", text = "/focus party2 \n/cast [@party2] 自然之愈" })
insert(macroList, { title = "party3自然之愈", key = "ALT-NUMPAD9", text = "/focus party3 \n/cast [@party3] 自然之愈" })
insert(macroList, { title = "party4自然之愈", key = "ALT-NUMPAD0", text = "/focus party4 \n/cast [@party4] 自然之愈" })
insert(macroList, { title = "player共生关系", key = "ALT-F1", text = "/focus player \n/cast [@player] 共生关系" })
insert(macroList, { title = "party1共生关系", key = "ALT-F2", text = "/focus party1 \n/cast [@party1] 共生关系" })
insert(macroList, { title = "party2共生关系", key = "ALT-F3", text = "/focus party2 \n/cast [@party2] 共生关系" })
insert(macroList, { title = "party3共生关系", key = "ALT-F5", text = "/focus party3 \n/cast [@party3] 共生关系" })
insert(macroList, { title = "party4共生关系", key = "ALT-F6", text = "/focus party4 \n/cast [@party4] 共生关系" })
insert(macroList, { title = "player生命绽放", key = "ALT-F7", text = "/focus player \n/cast [@player] 生命绽放" })
insert(macroList, { title = "party1生命绽放", key = "ALT-F8", text = "/focus party1 \n/cast [@party1] 生命绽放" })
insert(macroList, { title = "party2生命绽放", key = "ALT-F9", text = "/focus party2 \n/cast [@party2] 生命绽放" })
insert(macroList, { title = "party3生命绽放", key = "ALT-F10", text = "/focus party3 \n/cast [@party3] 生命绽放" })
insert(macroList, { title = "party4生命绽放", key = "ALT-F11", text = "/focus party4 \n/cast [@party4] 生命绽放" })
insert(macroList, { title = "player野性成长", key = "ALT-F12", text = "/focus player \n/cast [@player] 野性成长" })
insert(macroList, { title = "party1野性成长", key = "ALT-,", text = "/focus party1 \n/cast [@party1] 野性成长" })
insert(macroList, { title = "party2野性成长", key = "ALT-.", text = "/focus party2 \n/cast [@party2] 野性成长" })
insert(macroList, { title = "party3野性成长", key = "ALT-/", text = "/focus party3 \n/cast [@party3] 野性成长" })
insert(macroList, { title = "party4野性成长", key = "ALT-;", text = "/focus party4 \n/cast [@party4] 野性成长" })
insert(macroList, { title = "player愈合", key = "ALT-'", text = "/focus player \n/cast [@player] 愈合" })
insert(macroList, { title = "party1愈合", key = "ALT-[", text = "/focus party1 \n/cast [@party1] 愈合" })
insert(macroList, { title = "party2愈合", key = "ALT-]", text = "/focus party2 \n/cast [@party2] 愈合" })
insert(macroList, { title = "party3愈合", key = "ALT-=", text = "/focus party3 \n/cast [@party3] 愈合" })
insert(macroList, { title = "party4愈合", key = "ALT-`", text = "/focus party4 \n/cast [@party4] 愈合" })
insert(macroList, { title = "player回春术", key = "SHIFT-NUMPAD1", text = "/focus player \n/cast [@player] 回春术" })
insert(macroList, { title = "party1回春术", key = "SHIFT-NUMPAD2", text = "/focus party1 \n/cast [@party1] 回春术" })
insert(macroList, { title = "party2回春术", key = "SHIFT-NUMPAD3", text = "/focus party2 \n/cast [@party2] 回春术" })
insert(macroList, { title = "party3回春术", key = "SHIFT-NUMPAD4", text = "/focus party3 \n/cast [@party3] 回春术" })
insert(macroList, { title = "party4回春术", key = "SHIFT-NUMPAD5", text = "/focus party4 \n/cast [@party4] 回春术" })
insert(macroList, { title = "树皮术", key = "SHIFT-NUMPAD6", text = "/cast 树皮术" })
insert(macroList, { title = "万灵之召", key = "SHIFT-NUMPAD7", text = "/cast 万灵之召" })
insert(macroList, { title = "宁静", key = "SHIFT-NUMPAD8", text = "/cast 宁静" })
insert(macroList, { title = "自然迅捷", key = "SHIFT-NUMPAD9", text = "/cast 自然迅捷" })
insert(macroList, { title = "迅捷治愈", key = "SHIFT-NUMPAD0", text = "/cast 迅捷治愈" })
insert(macroList, { title = "target斜掠", key = "SHIFT-F1", text = "/cast [@target] 斜掠" })
insert(macroList, { title = "target撕碎", key = "SHIFT-F2", text = "/cast [@target] 撕碎" })
insert(macroList, { title = "target割裂", key = "SHIFT-F3", text = "/cast [@target] 割裂" })
insert(macroList, { title = "target野性之心", key = "SHIFT-F5", text = "/cast 野性之心" })
insert(macroList, { title = "target月火术", key = "SHIFT-F6", text = "/cast [@target] 月火术" })
insert(macroList, { title = "target愤怒", key = "SHIFT-F7", text = "/cast [@target] 愤怒" })
insert(macroList, { title = "激活", key = "SHIFT-F8", text = "/cast [@player] 激活" })
insert(macroList, { title = "mouseover复生", key = "SHIFT-F9", text = "/cast [@mouseover] 复生" })


for _, macro in pairs(macroList) do
    local buttonName = addonName .. "Button" .. macro.title
    local frame = CreateFrame("Button", buttonName, UIParent, "SecureActionButtonTemplate")
    frame:SetAttribute("type", "macro")
    frame:SetAttribute("macrotext", macro.text)
    frame:RegisterForClicks("AnyDown", "AnyUp")
    SetOverrideBindingClick(frame, true, macro.key, buttonName)
    print("RegMacro[" .. macro.title .. "] > " .. macro.key .. " > " .. macro.text)
end
