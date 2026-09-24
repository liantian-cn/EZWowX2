--[[
original: ../conditions/player_primary_power@dev/template.lua
uuid: {{uuid}}
plugin: player_primary_power@dev
摘要：在分配的第二行 Cell 中用线性灰度显示玩家首要能量比例。

描述：
    通过 UIInitFuncs 创建普通 Cell，立即读取玩家首要能量比例并映射为颜色。
    使用当前首要能量类型与非原始单位比例，0 为黑色、1 为白色，中间按比例线性插值。
    独立事件框架仅监听玩家的首要能量数值和显示能量类型变化，结果直接交给 Cell 渲染。

修改记录：
2026-09-15：事件统一延至下一帧刷新。
2026-09-12：生成器条件模板 @1.0，参数校验与解码见同目录 condition.py。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]
local After = C_Timer.After -- 事件后延至下一帧刷新

local CreateFrame = CreateFrame                       -- 创建独立的玩家首要能量事件框架
local UnitPowerType = UnitPowerType -- 查询玩家当前主要能量类型
local UnitPowerPercent = UnitPowerPercent           -- 获取玩家首要能量比例的曲线求值结果
local CreateColorCurve = C_CurveUtil.CreateColorCurve -- 创建黑白颜色曲线
local Linear = Enum.LuaCurveType.Linear               -- 按首要能量比例线性插值
local insert = table.insert                           -- 注册 UI 初始化函数

--[[
UnitPowerPercent(unitToken, powerType, unmodified, curve) 返回曲线求值结果。
本插件固定 player、当前 UnitPowerType("player")、false 和黑白线性颜色曲线。
UnitPowerType(unit) 返回 powerType、token 和显示颜色，本插件只取普通 powerType。
能量可能是秘密值，不在 Lua 中比较、缩放或读取颜色分量；直接交给 Cell 渲染。
来源：https://warcraft.wiki.gg/wiki/API_UnitPowerPercent
来源：https://warcraft.wiki.gg/wiki/API_UnitPowerType
2026-09-12 Wiki 页面访问失败；依据本地 UnitDocumentation.lua 核验签名。
@wow-ui-source，12.1.0.69587，
revision a89e9d0ceb7f6cd31e8fc5ca7df1a338ac0b1b58。
]]

--[[  variable reference  ]]

local Cell = addonTable.Cell               -- 复用普通 Cell 的构造和颜色接口
local COLOR = addonTable.COLOR             -- 共享黑白颜色作为曲线端点
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景就绪后创建 Cell

--[[  logical code  ]]

local UNIT_TOKEN = "player" -- 本版本固定采集玩家
local RATIO_MIN = 0.0 -- 灰度曲线黑色端点
local RATIO_MAX = 1.0 -- 灰度曲线白色端点
local UNMODIFIED = false -- 使用非原始单位能量比例
-- 条件实例位置由 Python 生成器填入。
local POSITION_Y = {{y1}} -- 本实例冻结的 Cell 行
local POSITION_X = {{x1}} -- 本实例冻结的横向位置

local powerCurve = CreateColorCurve() -- 将首要能量比例直接映射为灰度颜色
powerCurve:SetType(Linear)
powerCurve:AddPoint(RATIO_MIN, COLOR.BLACK)
powerCurve:AddPoint(RATIO_MAX, COLOR.WHITE)

local powerCell                        -- 等待 UI 初始化创建的玩家能量 Cell
local eventFrame = CreateFrame("Frame") -- 本例独立的玩家首要能量事件框架

local function update()
    if not powerCell then -- 初始化前的事件不访问尚未创建的 Cell
        return
    end

    local color = UnitPowerPercent(UNIT_TOKEN, UnitPowerType(UNIT_TOKEN), UNMODIFIED, powerCurve)
    powerCell:setCell(color) -- 使用局部曲线的颜色结果，不依赖 Cell 上不存在的曲线字段
end

local function InitializePowerCell()
    powerCell = Cell:New({ x = POSITION_X, y = POSITION_Y })
    update() -- 构造后立即显示当前首要能量比例
end

eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")        -- 首次进入世界时刷新当前状态
eventFrame:RegisterUnitEvent("UNIT_POWER_UPDATE", UNIT_TOKEN)    -- 只接收玩家当前首要能量变化
eventFrame:RegisterUnitEvent("UNIT_DISPLAYPOWER", UNIT_TOKEN) -- 只接收玩家显示能量类型变化
eventFrame:SetScript("OnEvent", function()
    After(0, function() update() end)
end)
insert(UIInitFuncs, InitializePowerCell)                -- 沿用共享布局、计数和缩放
