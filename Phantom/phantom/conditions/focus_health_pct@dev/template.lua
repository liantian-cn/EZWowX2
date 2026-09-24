--[[
original: ../conditions/focus_health_pct@dev/template.lua
uuid: {{uuid}}
摘要：显示焦点生命百分比。
描述：无焦点显示黑色，潜在秘密生命值交颜色曲线显示；单位事件及焦点切换后延至下一帧刷新。
修改记录：
2026-09-18：新增焦点生命百分比。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local UnitExists = UnitExists -- 判断焦点是否存在
local UnitHealthPercent = UnitHealthPercent -- 生命比例经曲线直接转颜色
local CreateColorCurve = C_CurveUtil.CreateColorCurve -- 创建颜色曲线
local Linear = Enum.LuaCurveType.Linear -- 黑白线性插值
local After = C_Timer.After -- 延至下一帧刷新
local insert = table.insert -- 注册初始化
--[[
UnitHealthPercent(unit, usePredicted, curve) 返回曲线求值结果，允许潜在秘密值进入显示消费者。
不对生命比例或颜色分量进行普通运算，UnitExists(unit) 为无单位兜底。
来源：已确认目标版本 Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
https://warcraft.wiki.gg/wiki/API_UnitHealthPercent （本次未重新抓取 Wiki）。
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell -- 普通像素 Cell
local COLOR = addonTable.COLOR -- 黑白端点
local UIInitFuncs = addonTable.UIInitFuncs -- UI 初始化队列

--[[  logical code  ]]
local POSITION_X = {{x1}} -- 冻结横坐标
local POSITION_Y = {{y1}} -- 冻结行号
local USE_PREDICTED = {{use_predicted}} -- 是否使用预测生命值
local UNIT_TOKEN = "focus" -- 固定焦点
local healthCurve = CreateColorCurve()
healthCurve:SetType(Linear)
healthCurve:AddPoint(0, COLOR.BLACK)
healthCurve:AddPoint(1, COLOR.WHITE)
local healthCell
local eventFrame = CreateFrame("Frame")

local function update()
    if not healthCell then return end
    if not UnitExists(UNIT_TOKEN) then
        healthCell:setCell(COLOR.BLACK)
        return
    end
    healthCell:setCell(UnitHealthPercent(UNIT_TOKEN, USE_PREDICTED, healthCurve))
end

local function initialize()
    healthCell = Cell:New({x = POSITION_X, y = POSITION_Y})
    update()
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("PLAYER_FOCUS_CHANGED")
eventFrame:RegisterUnitEvent("UNIT_HEALTH", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", UNIT_TOKEN)
if USE_PREDICTED then
    eventFrame:RegisterUnitEvent("UNIT_HEAL_PREDICTION", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_HEAL_ABSORB_AMOUNT_CHANGED", UNIT_TOKEN)
end
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, initialize)
