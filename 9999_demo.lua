-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame = CreateFrame
local CreateColor = CreateColor

-- 插件级变量定义/引用
local SIZE = addonTable.SIZE

-- 本地变量定义
local ICON_BORDER_COLOR = CreateColor(64 / 255, 158 / 255, 210 / 255, 1)
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local BORDER_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga"
local ICON_SIZE = 16  -- 4倍cell大小 (16 * scale)

-- 代码部分

---@class IconCell
---@field Frame Frame 图标框体
---@field Icon Texture 图标纹理
---@field Border Texture 边框纹理
---@field X integer X坐标
---@field Y integer Y坐标
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
    local iconName = addonName .. "IconCell_" .. x .. "_" .. y

    -- 创建主框体
    local frame = CreateFrame("Frame", iconName, parent)
    frame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * SIZE.CELL, -(y - 1) * SIZE.CELL)
    frame:SetFrameLevel(parent:GetFrameLevel() + 10)
    frame:SetSize(SIZE.CELL, SIZE.CELL)
    frame:Show()

    -- 创建边框纹理
    local border = frame:CreateTexture(nil, "BORDER")
    border:SetAllPoints(frame)
    border:SetTexture(BORDER_TEXTURE)
    border:SetVertexColor(ICON_BORDER_COLOR:GetRGBA())
    border:Show()

    -- 创建图标纹理
    local icon = frame:CreateTexture(nil, "ARTWORK")
    icon:SetPoint("TOPLEFT", frame, "TOPLEFT", 2, -2)
    icon:SetPoint("BOTTOMRIGHT", frame, "BOTTOMRIGHT", -2, 2)
    icon:SetTexture(WHITE_TEXTURE)
    icon:Show()

    self.Frame = frame
    self.Icon = icon
    self.Border = border
    self.X = x
    self.Y = y
end

---设置图标纹理
---@param iconID number|string 图标ID或纹理路径
function IconCell:SetIcon(iconID)
    self.Icon:SetTexture(iconID)
end

---设置边框颜色
---@param color ColorMixin 颜色对象
function IconCell:SetBorderColor(color)
    self.Border:SetVertexColor(color:GetRGBA())
end

addonTable.IconCell = IconCell
