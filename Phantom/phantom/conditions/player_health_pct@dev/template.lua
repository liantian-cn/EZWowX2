--[[
original: ../conditions/player_health_pct@dev/template.lua
uuid: {{uuid}}
plugin: player_health_pct@dev
摘要：在分配的第二行 Cell 中用线性灰度显示玩家生命值比例。

描述：
    通过 UIInitFuncs 创建普通 Cell，立即读取玩家生命值比例并映射为颜色。
    默认使用预测生命值，0 为黑色、1 为白色，中间按比例线性插值。
    独立事件框架监听玩家生命值、最大生命值变化；预测模式额外监听预测治疗和吸收变化。

修改记录：
2026-09-18：统一 use_predicted 参数、无单位零值和预测生命事件刷新。
2026-09-15：事件统一延至下一帧刷新。
2026-09-12：生成器条件模板 @1.0，参数校验与解码见同目录 condition.py。
2026-09-11：按解码开发前的 Lua 示例需求新增玩家血量 Cell。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After -- 事件后延至下一帧刷新

local CreateFrame = CreateFrame                       -- 创建独立的玩家生命值事件框架
local UnitHealthPercent = UnitHealthPercent           -- 获取玩家生命值比例的曲线求值结果
local UnitExists = UnitExists -- 无单位时显示零值
local CreateColorCurve = C_CurveUtil.CreateColorCurve -- 创建黑白颜色曲线
local Linear = Enum.LuaCurveType.Linear               -- 按生命值比例线性插值
local insert = table.insert                           -- 注册 UI 初始化函数

--[[
UnitHealthPercent：返回生命值比例，或将比例交给曲线生成显示值。
来源：https://warcraft.wiki.gg/wiki/API_UnitHealthPercent
签名：result = UnitHealthPercent(unit, usePredicted, curve)
参数：unit 为单位标识，本例 "player"；usePredicted 为是否使用预测生命值，默认 true；
    curve 为可选的 LuaCurveObjectBase，本例传入 0 到 1 的黑白颜色曲线。
返回值：LuaCurveEvaluatedResult；未提供曲线时为浮点比例，提供本例颜色曲线时为颜色对象。
限制标记：SecretReturns、SecretWhenCurveSecret；SecretArguments = "AllowedWhenUntainted"。
    本例直接传递颜色对象，不比较、计算或打印生命值比例及颜色分量。

核验日期：2026-09-12；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
Wiki 在线访问返回 403；接口说明依据本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell               -- 复用普通 Cell 的构造和颜色接口
local COLOR = addonTable.COLOR             -- 共享黑白颜色作为曲线端点
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建 Cell

--[[  logical code  ]]

local UNIT_TOKEN = "player" -- 本版本固定采集玩家
local RATIO_MIN = 0.0 -- 灰度曲线黑色端点
local RATIO_MAX = 1.0 -- 灰度曲线白色端点
-- 条件实例位置由 Python 生成器填入。
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local POSITION_X = {{x1}} -- 本实例冻结的横向位置
local USE_PREDICTED = {{use_predicted}} -- 是否使用预测生命值

local healthCurve = CreateColorCurve() -- 将生命值比例直接映射为灰度颜色
healthCurve:SetType(Linear)
healthCurve:AddPoint(RATIO_MIN, COLOR.BLACK)
healthCurve:AddPoint(RATIO_MAX, COLOR.WHITE)

local healthCell                        -- 等待 UI 初始化创建的玩家血量 Cell
local eventFrame = CreateFrame("Frame") -- 本例独立的玩家生命值事件框架

local function update()
    if not healthCell then -- 初始化前的事件不访问尚未创建的 Cell
        return
    end

    if not UnitExists(UNIT_TOKEN) then
        healthCell:setCell(COLOR.BLACK)
        return
    end
    local color = UnitHealthPercent(UNIT_TOKEN, USE_PREDICTED, healthCurve)
    healthCell:setCell(color) -- 使用局部曲线的颜色结果，不依赖 Cell 上不存在的曲线字段
end

local function InitializeHealthCell()
    healthCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update() -- 构造后立即显示当前生命值比例
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")        -- 首次进入世界时刷新当前状态
eventFrame:RegisterUnitEvent("UNIT_HEALTH", UNIT_TOKEN)    -- 只接收玩家当前生命值变化
eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", UNIT_TOKEN) -- 只接收玩家最大生命值变化
if USE_PREDICTED then
    eventFrame:RegisterUnitEvent("UNIT_HEAL_PREDICTION", UNIT_TOKEN) -- 预测治疗变化
    eventFrame:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", UNIT_TOKEN) -- 吸收量变化
    eventFrame:RegisterUnitEvent("UNIT_HEAL_ABSORB_AMOUNT_CHANGED", UNIT_TOKEN) -- 治疗吸收变化
end
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, InitializeHealthCell)                -- 沿用共享布局、计数和缩放
