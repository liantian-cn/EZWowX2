--[[
original: ../conditions/target_in_combat@dev/template.lua
uuid: {{uuid}}
摘要：目标是否处于战斗。
描述：存在前置；秘密布尔直接交给颜色消费者，不在 Lua 中分支或取反。
修改记录：2026-09-18：按已确认契约新增。
]]
--[[  namespace initialization  ]]
local addonName, addonTable = ...
--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建事件框架
local After = C_Timer.After -- 事件下一帧刷新
local insert = table.insert -- 注册初始化
local random = math.random -- 独立错峰
local UnitExists = UnitExists -- 普通单位存在前置
local UnitAffectingCombat = UnitAffectingCombat -- 本条件业务状态
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 安全颜色消费者
--[[
UnitAffectingCombat(unit) 返回单位是否战斗中的 bool；不保证正与玩家交战。
核验：2026-09-18，12.1.0.69587，revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
来源：Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua、CurveUtilDocumentation.lua。
Wiki：https://warcraft.wiki.gg/wiki/API_UnitAffectingCombat （2026-09-18 获取；网页版本不替代目标 build 源码）。
]]
--[[  variable reference  ]]
local Cell = addonTable.Cell -- 黑白像素消费者
local COLOR = addonTable.COLOR -- 颜色常量
local UIInitFuncs = addonTable.UIInitFuncs -- 布局完成后构造
--[[  logical code  ]]
local POSITION_X = {{x1}}
local POSITION_Y = {{y1}}
local UNIT_TOKEN = "target"
local UPDATE_INTERVAL = 1 -- 低频状态兜底
local display
local eventFrame = CreateFrame("Frame")
local function update()
    if not display then return end
    if not UnitExists(UNIT_TOKEN) then display:clearCell(); return end
    display:setCellBoolean(UnitAffectingCombat(UNIT_TOKEN))
end
local function initialize()
    display = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update()
end
eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_FACTION", UNIT_TOKEN)
eventFrame:RegisterUnitEvent("UNIT_HEALTH", UNIT_TOKEN)
eventFrame:SetScript("OnEvent", function() After(0, update) end)
local fastTimeElapsed = -random()
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)
insert(UIInitFuncs, initialize)
