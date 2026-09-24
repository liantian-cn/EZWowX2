--[[
original: ../conditions/player_has_pet@dev/template.lua
uuid: {{uuid}}
摘要：玩家是否存在存活宠物。
描述：只检查 pet 单位，存在且非死亡；事件延后一帧刷新。
修改记录：2026-09-18：按冻结约定新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local After = C_Timer.After -- 延后一帧刷新
local insert = table.insert -- 注册初始化
local UnitExists = UnitExists -- 查询宠物存在性
local UnitIsDeadOrGhost = UnitIsDeadOrGhost -- 排除死亡宠物
--[[
UnitExists("pet") 与 UnitIsDeadOrGhost("pet") 返回 bool；只统计玩家当前宠物。
2026-09-18：按冻结版本约定查阅 @wow-ui-source 的
Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
Wiki 入口：https://warcraft.wiki.gg/wiki/API_UnitIsDeadOrGhost （未取得在线说明）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 显示消费者
local UIInitFuncs = addonTable.UIInitFuncs -- 布局初始化入口
--[[  logical code  ]]
local POSITION_X = {{x1}} -- 冻结横坐标
local POSITION_Y = {{y1}} -- 冻结行
local UNIT_TOKEN = "pet" -- 固定宠物单位
local cell
local eventFrame = CreateFrame("Frame")
local function update()
    if not cell then return end
    cell:setCellBoolean(UnitExists(UNIT_TOKEN) and not UnitIsDeadOrGhost(UNIT_TOKEN))
end
local function initialize()
    cell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterUnitEvent("UNIT_PET", "player")
eventFrame:RegisterUnitEvent("UNIT_HEALTH", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, initialize)
