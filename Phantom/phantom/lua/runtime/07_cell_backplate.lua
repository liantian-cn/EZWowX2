--[[
original: runtime\07_cell_backplate.lua
uuid: da68dc60-2939-4526-b12c-e779e7eb14d6
runtime_index: 7
摘要：创建 Cell 的固定黑色背板。
描述：按原行列坐标构造内容矩形，独立登记行宽并更新画布。
修改记录：
2026-09-20：拆分固定背板与内容消费者。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建背板框体
local setmetatable = setmetatable -- 构造包装实例

--[[  variable reference  ]]
local SIZE = addonTable.SIZE -- 共享像素尺寸
local FrameLevel = addonTable.FrameLevel -- 静态显示层级
local BackgroundFrameResize = addonTable.BackgroundFrameResize -- 更新画布尺寸

--[[  logical code  ]]
---@class CellBackplate
---@field Frame Frame 内容矩形
---@field BackgroundTexture Texture 固定黑底
local CellBackplate = {} -- 固定背板构造器
CellBackplate.__index = CellBackplate

---@param options table 包含 x、y 的 Cell 坐标
---@return CellBackplate
function CellBackplate:New(options)
    local x, y = options.x, options.y
    local parent = addonTable.BackgroundFrame
    local frame = CreateFrame("Frame", addonName .. "Cell_" .. x .. "_" .. y, parent)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * SIZE.CELL, -(y - 1) * SIZE.CELL)
    frame:SetFrameStrata("TOOLTIP")
    frame:SetFrameLevel(FrameLevel.Backplate)
    frame:SetSize(SIZE.CELL, SIZE.CELL)
    frame:Show()
    local texture = frame:CreateTexture(nil, "BACKGROUND")
    texture:SetAllPoints(frame)
    texture:SetColorTexture(0, 0, 0, 1)
    if y == 1 then
        addonTable.GeneralCellLength = addonTable.GeneralCellLength + 1
    end
    if y == 2 then
        addonTable.ConditionCellLength = addonTable.ConditionCellLength + 1
    end
    BackgroundFrameResize()
    return setmetatable({Frame = frame, BackgroundTexture = texture}, self)
end

addonTable.CellBackplate = CellBackplate
