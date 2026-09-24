--[[
original: examples\05_player_health.lua
uuid: {{uuid}}
index: 5
摘要：在第二行第 5 个 Cell 中用线性灰度显示玩家生命值比例。

描述：
    通过 UIInitFuncs 创建普通 Cell，立即读取玩家生命值比例并映射为颜色。
    默认使用预测生命值，0 为黑色、1 为白色，中间按比例线性插值。
    独立事件框架仅监听玩家的当前生命值和最大生命值变化，结果直接交给 Cell 渲染。

修改记录：
2026-09-11：按解码开发前的 Lua 示例需求新增玩家血量 Cell。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame                       -- 创建独立的玩家生命值事件框架
local UnitHealthPercent = UnitHealthPercent           -- 获取玩家生命值比例的曲线求值结果
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

核验日期：2026-09-11；本地 @wow-ui-source 版本：12.1.0.69587。
源码 revision：288f40d5cee5089223758d5810cb906ad34d4018。
API 定义：Interface/AddOns/Blizzard_APIDocumentationGenerated/UnitDocumentation.lua。
Wiki 在线访问返回 403；接口说明依据本地源码，不声称已获取最新网页。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell               -- 复用普通 Cell 的构造和颜色接口
local COLOR = addonTable.COLOR             -- 共享黑白颜色作为曲线端点
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建 Cell

--[[  logical code  ]]

-- 类型：RotationsCell，仅作说明；以下参数供未来插件替换。
local POSITION_Y = 2                   -- 第二行，RotationsCell 对应的行
local POSITION_X = 5                   -- 本行第 5 个 Cell
local USE_PREDICTED = true             -- 使用预测生命值，未来作为插件入参

local healthCurve = CreateColorCurve() -- 将生命值比例直接映射为灰度颜色
healthCurve:SetType(Linear)
healthCurve:AddPoint(0.0, COLOR.BLACK)
healthCurve:AddPoint(1.0, COLOR.WHITE)

local healthCell                        -- 等待 UI 初始化创建的玩家血量 Cell
local eventFrame = CreateFrame("Frame") -- 本例独立的玩家生命值事件框架

local function RefreshHealthCell()
    if not healthCell then -- 初始化前的事件不访问尚未创建的 Cell
        return
    end

    local color = UnitHealthPercent("player", USE_PREDICTED, healthCurve)
    healthCell:setCell(color) -- 使用局部曲线的颜色结果，不依赖 Cell 上不存在的曲线字段
end

local function InitializeHealthCell()
    healthCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    RefreshHealthCell() -- 构造后立即显示当前生命值比例
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")        -- 首次进入世界时读取当前法术书
eventFrame:RegisterUnitEvent("UNIT_HEALTH", "player")    -- 只接收玩家当前生命值变化
eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", "player") -- 只接收玩家最大生命值变化
eventFrame:SetScript("OnEvent", RefreshHealthCell)       -- 两类事件均重新查询当前比例
insert(UIInitFuncs, InitializeHealthCell)                -- 沿用共享布局、计数和缩放
