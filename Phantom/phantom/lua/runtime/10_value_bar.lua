--[[
original: runtime\10_value_bar.lua
uuid: 99f3155c-0642-41c8-9856-8613628f61ab
runtime_index: 10
摘要：
    复用独立背板创建黑白数值条，提供数值更新接口。

描述：
    在已创建的共享背景第三行构建红色分隔底板、黑色内容背景和白色 StatusBar。
    x 为包含左侧分隔的占位起点，width 为内容宽度，均以 Cell 为单位；
    内容从 x + 0.5 开始，完整占位宽度为 width + 1，下一条由调用方按此宽度排布。
    构造时将数值范围设为 0 到 100、当前值设为 50，仅 reverse 为 true 时启用反向填充。
    ValueBarBackplate 独立登记 width + 1 的占位行宽并调整背景尺寸。
    后续通过实例方法直接设置 StatusBar 的范围和当前值；反向填充方向在构造时确定。
    截图端读取完整占位的中间两行，按白色占黑白像素总数的百分比解码，排除红色及其他颜色。

修改记录：
2026-09-20：复用独立背板，填充使用 Content 静态层级。
2026-09-06：liantian-cn初始化创建。

]]


--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local setmetatable = setmetatable             -- 为数值条实例设置共享方法表
local CreateFrame  = CreateFrame              -- 创建框体

--[[  variable reference  ]]

local COLOR                 = addonTable.COLOR                 -- 共享基础颜色，提供数值条的红色分隔与黑白配色
local ValueBarBackplate     = addonTable.ValueBarBackplate -- 固定黑底与分隔构造器
local FrameLevel            = addonTable.FrameLevel            -- 数值条分隔底板、内容背景与填充层的层级定义
local SIZE                  = addonTable.SIZE                  -- 共享 Cell 尺寸定义
local BackgroundFrameResize = addonTable.BackgroundFrameResize -- 按共享长度数据调整背景尺寸


--[[  logical code  ]]

---@class ValueBar
---@field Backplate ValueBarBackplate 固定黑底与红色分隔
---@field Frame Frame 黑色内容背景框体，不含两侧红色分隔
---@field StatusBar StatusBar 显示当前数值比例的白色填充条
---@field X integer 包含左侧红色分隔的占位起点，以 Cell 为单位
---@field width number 黑白内容宽度，以 Cell 为单位，不含分隔
local ValueBar = {}         -- 数值条实例的共享方法表
ValueBar.__index = ValueBar -- 实例通过元表访问共享方法




---ValueBar 初始化方法（私有）
---@private
---@param x integer 包含左侧分隔的占位起点，以 Cell 为单位
---@param width number 内容宽度，以 Cell 为单位；完整占位为 width + 1
---@param reverse boolean 是否反向填充
function ValueBar:_initialize(x, width, reverse) -- 创建第三行数值条并更新共享占位宽度
    self.Backplate = ValueBarBackplate:New(x, width) -- 背板独立负责分隔、黑底与计数
    local backgroundFrame = self.Backplate.Frame -- 保持 StatusBar 为黑底直接子级
    local bar = CreateFrame("StatusBar", nil, backgroundFrame)        -- 创建由内容背景承载的数值填充条
    bar:SetAllPoints(backgroundFrame)                                 -- 使数值条覆盖完整内容区域
    bar:SetFrameLevel(FrameLevel.Content)                             -- 普通填充使用内容层级
    bar:SetColorFill(COLOR.WHITE:GetRGBA())                           -- 以纯白色填充当前数值对应的比例

    if reverse then                                                   -- 按构造参数选择是否反向填充
        bar:SetReverseFill(true)                                      -- 启用反向填充
    end
    bar:Show()                                                        -- 显示数值填充条

    self.Frame = backgroundFrame                                      -- 保存内容背景框体
    self.X = x                                                        -- 记录包含分隔的占位起点
    self.width = width                                                -- 记录不含分隔的内容宽度
    self.StatusBar = bar                                              -- 保存后续更新数值的 StatusBar
    self:setMinMaxValues(0, 100)                                      -- 初始化数值范围为 0 到 100
    self:setValue(50)                                                 -- 初始化为半满状态
end

---创建数值条；调用前须已创建 addonTable.BackgroundFrame
---@param x integer 包含左侧分隔的占位起点，以 Cell 为单位
---@param width number 内容宽度，以 Cell 为单位；完整占位为 width + 1
---@param reverse boolean|nil 仅 true 启用反向填充，省略时使用默认方向
---@return ValueBar # 返回初始化完成的 Bar 实例
function ValueBar:New(x, width, reverse)    -- 按内容宽度与填充方向构造独立数值条
    if reverse and (reverse == true) then   -- 仅接受布尔值 true 作为反向填充开关
        reverse = true                      -- 启用反向填充
    else
        reverse = false                     -- 其余输入统一使用默认填充方向
    end
    local instance = setmetatable({}, self) -- 创建继承共享方法的独立实例
    instance:_initialize(x, width, reverse) -- 按占位参数创建框体并初始化数值
    return instance                         -- 返回初始化完成的实例
end

---设置数值条的最小值与最大值
---@param minValue number 数值范围下限
---@param maxValue number 数值范围上限
function ValueBar:setMinMaxValues(minValue, maxValue)  -- 更新填充比例使用的数值范围
    self.StatusBar:SetMinMaxValues(minValue, maxValue) -- 将数值范围直接交给 StatusBar
end

---设置数值条的当前值
---@param currentValue number 当前数值
function ValueBar:setValue(currentValue)  -- 更新当前数值对应的白色填充
    self.StatusBar:SetValue(currentValue) -- 将当前值直接交给 StatusBar 更新填充
end

addonTable.ValueBar = ValueBar -- 向后续模块公开 ValueBar 构造与数值设置接口
