-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame = CreateFrame
local CreateColor = CreateColor

-- 插件级变量定义/引用
local SIZE = addonTable.SIZE

-- 本地变量定义
local ICON_BORDER_COLOR = CreateColor(64 / 255, 158 / 255, 210 / 255, 1)
local BORDER_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga"
local ICON_SIZE = 16

-- 代码部分

---@class IconCell
---@field Frame Frame 图标框体
---@field Background Texture 背景纹理
---@field Icon Texture 图标纹理
---@field Border Texture 边框纹理
local IconCell = {}
IconCell.__index = IconCell

---IconCell 构造函数
---@param x integer X坐标（以单元格为单位）
---@param y integer Y坐标（以单元格为单位）
---@return IconCell # 返回IconCell实例
function IconCell:New(x, y)
    local instance = setmetatable({}, self)
    instance:_initialize(x, y)
    return instance
end

---IconCell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
function IconCell:_initialize(x, y)
    local parent = addonTable.MartixFrame
    local scale = 6
    local iconSize = ICON_SIZE * scale

    -- 创建背景Frame
    local frame = CreateFrame("Frame", nil, parent)
    frame:SetSize(iconSize, iconSize)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * SIZE.CELL, -(y - 1) * SIZE.CELL)

    -- 背景层
    local background = frame:CreateTexture(nil, "BACKGROUND")
    background:SetAllPoints(frame)
    background:SetColorTexture(0, 0, 0, 1)

    -- 图标层
    local icon = frame:CreateTexture(nil, "ARTWORK")
    icon:SetAllPoints(frame)
    icon:Hide()

    -- 边框层
    local border = frame:CreateTexture(nil, "OVERLAY")
    border:SetAllPoints(frame)
    border:SetTexture(BORDER_TEXTURE)
    border:SetVertexColor(ICON_BORDER_COLOR:GetRGBA())

    self.Frame = frame
    self.Background = background
    self.Icon = icon
    self.Border = border
end

---设置图标纹理
---@param iconID number|string 图标ID或纹理路径
function IconCell:SetIcon(iconID)
    self.Icon:SetTexture(iconID)
    self.Icon:Show()
end

---设置边框颜色
---@param color ColorMixin 颜色对象
function IconCell:SetBorderColor(color)
    self.Border:SetVertexColor(color:GetRGBA())
end

addonTable.IconCell = IconCell
