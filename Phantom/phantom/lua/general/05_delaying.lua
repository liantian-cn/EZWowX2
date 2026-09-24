--[[
original: general\05_delaying.lua
uuid: db99c08a-9f97-4ae8-b076-dd2981bf99cc
index: 5
摘要：在第一行第 5 个 Cell 中以黑白显示插件延迟状态。

描述：
    通过 UIInitFuncs 创建普通 Cell，沿用共享缩放和背景扩宽，初始保持黑色。
    独立 OnUpdate 使用随机初始延迟错峰刷新，累计时间超过 0.1 秒时扣除 0.1 秒并更新一次。
    每次读取当前延迟状态，true 显示白色，false 显示黑色。

修改记录：
2026-09-09：按通用延迟状态 Cell 需求新增。
]]

--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame = CreateFrame -- 创建独立更新框架
local random = math.random -- 生成初始随机延迟，使各状态 Cell 错峰刷新
local insert = table.insert -- 注册 UI 初始化函数

--[[  variable reference  ]]

local Cell = addonTable.Cell -- 复用普通 Cell 的构造与布尔值着色接口
local UIInitFuncs = addonTable.UIInitFuncs -- 在共享尺寸和背景初始化后创建状态 Cell

--[[  logical code  ]]

local delayingCell -- 延迟状态 Cell，等待 UI 初始化后赋值
local eventFrame = CreateFrame("Frame") -- 独立承载本字段的 OnUpdate 刷新
local fastTimeElapsed = -random() -- 随机负初值推迟首次刷新，不改变全局随机种子

local function RefreshDelayingCell()
    if not delayingCell then -- 更新回调可能先于延迟 UI 初始化到达
        return
    end

    delayingCell:setCellBoolean(addonTable.Delaying()) -- 实时读取延迟状态，true 白色、false 黑色
end

local function InitializeDelayingCell()
    delayingCell = Cell:New({ x = 5, y = 1 }) -- 构造后保持默认黑色，等待错峰首次刷新
end

eventFrame:HookScript("OnUpdate", function(_, elapsed)
    fastTimeElapsed = fastTimeElapsed + elapsed -- 累加本帧时间
    if fastTimeElapsed > 0.1 then -- 严格超过阈值才刷新，每帧最多一次
        fastTimeElapsed = fastTimeElapsed - 0.1 -- 保留剩余累计时间
        RefreshDelayingCell()
    end
end)
insert(UIInitFuncs, InitializeDelayingCell) -- 沿用共享初始化顺序和缩放
