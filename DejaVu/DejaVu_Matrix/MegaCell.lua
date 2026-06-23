-- 插件入口
local addonName, addonTable = ... -- 插件名称与共享表

-- Lua 原生函数
local setmetatable = setmetatable

-- WoW 官方 API
local CreateFrame = CreateFrame     -- 创建框体
local issecretvalue = issecretvalue -- 判断值是否为秘密值

local DejaVu = _G["DejaVu"]

local BLACK = CreateColor(0, 0, 0, 1)
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"


---@class MegaCell
---@field Frame Frame MegaCell框架
---@field Background Texture 背景纹理
---@field Icon Texture 图标纹理
---@field Slug string 单元格唯一标识（格式: x_y）
---@field X integer X坐标
---@field Y integer Y坐标
---@field lastIcon? string|number 上次设置的图标（路径或ID）
---@field lastIconIsSecret boolean 上次图标是否为秘密值
local MegaCell = {}
MegaCell.__index = MegaCell

---MegaCell 构造函数
---@param x integer X坐标（以单元格为单位）
---@param y integer Y坐标（以单元格为单位）
---@param backgroundColor? colorRGBA 背景颜色, 默认为黑色
---@return MegaCell # 返回MegaCell实例, 如果父框架不存在则返回nil
function MegaCell:New(x, y, backgroundColor)
    local instance = setmetatable({}, self)
    instance:_initialize(x, y, backgroundColor)
    return instance
end

---MegaCell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
---@param backgroundColor? colorRGBA 背景颜色
function MegaCell:_initialize(x, y, backgroundColor)
    if not backgroundColor then
        backgroundColor = BLACK
    end

    local parent = addonTable.MartixFrame
    local cellSize = addonTable.SIZE.CELL
    local megaSize = addonTable.SIZE.MEGA
    local cellSlug = x .. "_" .. y
    local cellName = addonName .. "MegaCell_" .. cellSlug

    -- 底层Frame
    local cellFrame = CreateFrame("Frame", cellName, parent)
    cellFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * cellSize, -y * cellSize)
    cellFrame:SetFrameLevel(parent:GetFrameLevel() + 1)
    cellFrame:SetSize(megaSize, megaSize)
    cellFrame:Show()

    -- 中层背景色
    local cellTexture = cellFrame:CreateTexture(nil, "BACKGROUND")
    cellTexture:SetAllPoints(cellFrame)
    cellTexture:SetTexture(WHITE_TEXTURE)
    cellTexture:SetVertexColor(backgroundColor:GetRGBA())
    cellTexture:Show()

    -- 顶层图标
    local iconTexture = cellFrame:CreateTexture(nil, "ARTWORK")
    iconTexture:SetAllPoints(cellFrame)
    iconTexture:Hide()

    self.Frame = cellFrame
    self.Background = cellTexture
    self.Icon = iconTexture
    self.Slug = cellSlug
    self.X = x
    self.Y = y
    self.lastIcon = nil
    self.lastIconIsSecret = false
end

---设置图标方法
---@param icon string|number 图标路径或纹理ID
function MegaCell:setCell(icon)
    -- 检查是否为秘密值
    local isSecret = issecretvalue(icon)

    -- 如果图标相同且都不是秘密值, 跳过设置以提高性能
    if not isSecret and not self.lastIconIsSecret and self.lastIcon == icon then
        return
    end

    -- 保存图标状态
    self.lastIcon = icon
    self.lastIconIsSecret = isSecret

    -- 设置图标
    self.Icon:SetTexture(icon)
    self.Icon:Show()
end

---清除图标方法
function MegaCell:clearCell()
    self.Icon:Hide()
    self.lastIcon = nil
    self.lastIconIsSecret = false
end

---工厂函数: 创建 MegaCell 实例
---@param x integer X坐标
---@param y integer Y坐标
---@param backgroundColor? colorRGBA 背景颜色
---@return MegaCell # 返回MegaCell实例
DejaVu.CreateMegaCell = function(x, y, backgroundColor)
    return MegaCell:New(x, y, backgroundColor)
end

DejaVu.MegaCell = MegaCell
