--[[
original: ../conditions/target_in_range@dev/template.lua
uuid: {{uuid}}
摘要：显示指定技能对目标的射程结果。
描述：0.1 秒随机错峰轮询，潜在秘密结果直接交布尔颜色消费者；普通 nil、无单位、无效技能显示否。
修改记录：
2026-09-18：新增目标射程条件。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建轮询框架
local UnitExists = UnitExists -- 单位存在判断
local DoesSpellExist = C_Spell.DoesSpellExist -- 技能有效性判断
local IsSpellInRange = C_Spell.IsSpellInRange -- 技能射程结果
local issecretvalue = issecretvalue -- 先识别秘密值再判断 nil
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 秘密布尔值直接显示
local random = math.random -- 错峰轮询
local insert = table.insert -- 注册 UI 初始化
--[[
C_Spell.IsSpellInRange(spellIdentifier, targetUnit) 返回 bool 或 nil，不提供实际距离。
秘密 bool 直接传给 EvaluateColorFromBoolean(value, trueColor, falseColor)，不在 Lua 中比较。
来源：已确认目标版本 Blizzard_APIDocumentationGenerated/SpellDocumentation.lua、CurveUtilDocumentation.lua。
https://warcraft.wiki.gg/wiki/API_C_Spell.IsSpellInRange （本次未重新抓取 Wiki）。
]]

--[[  variable reference  ]]
local Cell = addonTable.Cell -- 普通 Cell 显示
local COLOR = addonTable.COLOR -- 共享黑白颜色
local UIInitFuncs = addonTable.UIInitFuncs -- UI 初始化队列

--[[  logical code  ]]
local POSITION_X = {{x1}} -- 冻结横坐标
local POSITION_Y = {{y1}} -- 冻结行号
local SPELL_ID = {{spell_id}} -- 检测技能
local UNIT_TOKEN = "target" -- 固定目标
local UPDATE_INTERVAL = 0.1 -- 持续轮询间隔
local rangeCell
local eventFrame = CreateFrame("Frame")

local function update()
    if not rangeCell then return end
    if not UnitExists(UNIT_TOKEN) or not DoesSpellExist(SPELL_ID) then
        rangeCell:setCell(COLOR.BLACK)
        return
    end
    local inRange = IsSpellInRange(SPELL_ID, UNIT_TOKEN)
    if issecretvalue(inRange) then
        rangeCell:setCell(EvaluateColorFromBoolean(inRange, COLOR.WHITE, COLOR.BLACK))
    elseif inRange == nil then
        rangeCell:setCell(COLOR.BLACK)
    else
        rangeCell:setCell(EvaluateColorFromBoolean(inRange, COLOR.WHITE, COLOR.BLACK))
    end
end

local function initialize()
    rangeCell = Cell:New({x = POSITION_X, y = POSITION_Y})
end

local fastTimeElapsed = -random()
eventFrame:SetScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed
    if fastTimeElapsed > UPDATE_INTERVAL then
        fastTimeElapsed = fastTimeElapsed - UPDATE_INTERVAL
        update()
    end
end)
insert(UIInitFuncs, initialize)
