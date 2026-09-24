--[[
original: ../conditions/spec_power_fury@dev/template.lua
uuid: {{uuid}}
摘要：显示玩家恶魔之怒比例。
描述：固定 Fury，秘密资源只经黑白曲线交给 Cell；初始化及资源事件刷新。
修改记录：2026-09-18：新增固定资源条件。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local After = C_Timer.After -- 下一帧刷新
local CreateFrame = CreateFrame -- 独立事件框架
local UnitPowerPercent = UnitPowerPercent -- 资源比例曲线求值
local CreateColorCurve = C_CurveUtil.CreateColorCurve -- 黑白颜色曲线
local Linear = Enum.LuaCurveType.Linear -- 线性插值
local POWER_TYPE = Enum.PowerType.Fury -- 固定恶魔之怒资源
local insert = table.insert -- 注册初始化
--[[
UnitPowerPercent(unitToken, powerType, unmodified, curve) 返回曲线求值结果。
固定 player、Fury、false；SecretWhenUnitPowerRestricted/SecretWhenCurveSecret，
不比较或运算秘密结果，直接交给 Cell:setCell。
来源：@wow-ui-source/Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
2026-09-18：按 todo_list2.md 已确认目标版本约定核对签名，不重新复核 build 差异。
https://warcraft.wiki.gg/wiki/API_UnitPowerPercent （本次未读取 Wiki 页面）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 普通像素格
local COLOR = addonTable.COLOR -- 黑白端点
local UIInitFuncs = addonTable.UIInitFuncs -- UI 初始化队列
--[[  logical code  ]]
local UNIT_TOKEN = "player" -- 固定玩家
local POSITION_X = {{x1}} -- 冻结列
local POSITION_Y = {{y1}} -- 冻结行
local powerCurve = CreateColorCurve()
powerCurve:SetType(Linear)
powerCurve:AddPoint(0, COLOR.BLACK)
powerCurve:AddPoint(1, COLOR.WHITE)
local powerCell
local eventFrame = CreateFrame("Frame")
local function update()
    if not powerCell then return end -- 初始化前不访问 Cell
    powerCell:setCell(UnitPowerPercent(UNIT_TOKEN, POWER_TYPE, false, powerCurve))
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterUnitEvent("UNIT_POWER_UPDATE", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_MAXPOWER", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_DISPLAYPOWER", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, function()
    powerCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end)
