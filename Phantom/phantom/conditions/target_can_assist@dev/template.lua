--[[
original: ../conditions/target_can_assist@dev/template.lua
uuid: {{uuid}}
摘要：目标是否可辅助。
描述：无目标 false；使用默认可辅助判断，事件延后一帧刷新。
修改记录：2026-09-18：按冻结约定新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local After = C_Timer.After -- 延后一帧刷新
local insert = table.insert -- 注册初始化
local UnitExists = UnitExists -- 查询单位存在性
local UnitCanAssist = UnitCanAssist -- 默认可辅助判断
--[[
UnitCanAssist("player", unit) 返回 bool；canAssistImmunePC/canAssistUninteractable 均使用默认 false。
结果直接交给 setCellBoolean/EvaluateColorFromBoolean，不对潜在秘密布尔结果分支。
2026-09-18：按冻结版本约定查阅 @wow-ui-source 的
Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
Wiki 入口：https://warcraft.wiki.gg/wiki/API_UnitCanAssist （未取得在线说明）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 显示消费者
local UIInitFuncs = addonTable.UIInitFuncs -- 布局初始化入口
--[[  logical code  ]]
local POSITION_X = {{x1}} -- 冻结横坐标
local POSITION_Y = {{y1}} -- 冻结行
local UNIT_TOKEN = "target" -- 固定单位
local cell
local eventFrame = CreateFrame("Frame")
local function update()
    if not cell then return end
    if not UnitExists(UNIT_TOKEN) then
        cell:setCellBoolean(false)
        return
    end
    cell:setCellBoolean(UnitCanAssist("player", UNIT_TOKEN))
end
local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
eventFrame:RegisterUnitEvent("UNIT_FACTION", UNIT_TOKEN, "player")
eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_TOKEN, "player")
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, initialize)
