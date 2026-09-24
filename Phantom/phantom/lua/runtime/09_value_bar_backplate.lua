--[[
original: runtime\09_value_bar_backplate.lua
uuid: 7a1a4e11-3ff8-43d5-bf1d-e8a088a16549
runtime_index: 9
摘要：创建 ValueBar 的黑色内容背板与红色分隔。
描述：红黑框体均为共享画布的直接子级，左右保留半个 Cell 红边；仅此处累计完整占位宽度。
修改记录：
2026-09-20：拆分固定背板与数值填充消费者。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建背板与分隔框体
local setmetatable = setmetatable -- 构造包装实例

--[[  variable reference  ]]
local SIZE = addonTable.SIZE -- 共享像素尺寸
local COLOR = addonTable.COLOR -- 固定黑红配色
local FrameLevel = addonTable.FrameLevel -- 静态显示层级
local BackgroundFrameResize = addonTable.BackgroundFrameResize -- 更新画布尺寸

--[[  logical code  ]]
---@class ValueBarBackplate
---@field Frame Frame 不含分隔的内容矩形
---@field BackgroundTexture Texture 固定黑底
---@field SeparatorFrame Frame 含左右分隔的红底矩形
---@field SeparatorTexture Texture 固定红色分隔
local ValueBarBackplate = {} -- 固定背板构造器
ValueBarBackplate.__index = ValueBarBackplate

---@param x integer 含左侧分隔的占位起点，以 Cell 为单位
---@param width number 黑色内容宽度，以 Cell 为单位
---@return ValueBarBackplate
function ValueBarBackplate:New(x, width)
    local parent = addonTable.BackgroundFrame
    local barName = addonName .. "Bar_" .. x
    local separator = CreateFrame("Frame", barName .. "separatorFrame", parent)
    separator:SetPoint("TOPLEFT", parent, "TOPLEFT", x * SIZE.CELL, -2 * SIZE.CELL)
    separator:SetFrameStrata("TOOLTIP")
    separator:SetFrameLevel(FrameLevel.Separator)
    separator:SetSize((width + 1) * SIZE.CELL, SIZE.CELL)
    separator:Show()
    local separatorTexture = separator:CreateTexture(nil, "BACKGROUND")
    separatorTexture:SetAllPoints()
    separatorTexture:SetColorTexture(COLOR.RED:GetRGBA())
    local frame = CreateFrame("Frame", barName .. "backgroundFrame", parent)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", (x + 0.5) * SIZE.CELL, -2 * SIZE.CELL)
    frame:SetFrameStrata("TOOLTIP")
    frame:SetFrameLevel(FrameLevel.Backplate)
    frame:SetSize(width * SIZE.CELL, SIZE.CELL)
    frame:Show()
    local texture = frame:CreateTexture(nil, "BACKGROUND")
    texture:SetAllPoints()
    texture:SetColorTexture(COLOR.BLACK:GetRGBA())
    addonTable.ValueBarLength = addonTable.ValueBarLength + width + 1
    BackgroundFrameResize()
    return setmetatable({
        Frame = frame, BackgroundTexture = texture,
        SeparatorFrame = separator, SeparatorTexture = separatorTexture,
    }, self)
end

addonTable.ValueBarBackplate = ValueBarBackplate
