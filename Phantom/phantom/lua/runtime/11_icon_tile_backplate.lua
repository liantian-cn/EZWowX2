--[[
original: runtime\11_icon_tile_backplate.lua
uuid: 82e7be2b-78fb-49d9-92b4-55c2b8589375
runtime_index: 11
摘要：创建 IconTile 的固定黑色背板。
描述：第四行按槽位编号紧密排列，每槽占两个 Cell，仅此处累计行宽并更新画布。
修改记录：
2026-09-20：拆分固定背板与图标消费者。
]]

--[[  namespace initialization  ]]
local addonName, addonTable = ...

--[[  api cache  ]]
local CreateFrame = CreateFrame -- 创建槽位框体
local setmetatable = setmetatable -- 构造包装实例

--[[  variable reference  ]]
local SIZE = addonTable.SIZE -- 共享像素尺寸
local FrameLevel = addonTable.FrameLevel -- 静态显示层级
local BackgroundFrameResize = addonTable.BackgroundFrameResize -- 更新画布尺寸

--[[  logical code  ]]
---@class IconTileBackplate
---@field Frame Frame 内容矩形
---@field BackgroundTexture Texture 固定黑底
local IconTileBackplate = {} -- 固定背板构造器
IconTileBackplate.__index = IconTileBackplate

---@param x integer 从 1 开始的槽位编号
---@return IconTileBackplate
function IconTileBackplate:New(x)
    local parent = addonTable.BackgroundFrame
    local iconSize = 2 * SIZE.CELL
    local frame = CreateFrame("Frame", nil, parent)
    frame:SetSize(iconSize, iconSize)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", SIZE.CELL + (x - 1) * iconSize, -3 * SIZE.CELL)
    frame:SetFrameStrata("TOOLTIP")
    frame:SetFrameLevel(FrameLevel.Backplate)
    local texture = frame:CreateTexture(nil, "BACKGROUND")
    texture:SetAllPoints(frame)
    texture:SetColorTexture(0, 0, 0, 1)
    addonTable.IconTileLength = addonTable.IconTileLength + 2
    BackgroundFrameResize()
    return setmetatable({Frame = frame, BackgroundTexture = texture}, self)
end

addonTable.IconTileBackplate = IconTileBackplate
