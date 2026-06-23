-- 插件入口
local addonName, addonTable = ... -- 插件名称与共享表

-- Lua 原生函数
local setmetatable = setmetatable
local format = string.format
local tostring = tostring
local insert = table.insert

-- WoW 官方 API
local CreateFrame = CreateFrame     -- 创建框体
local issecretvalue = issecretvalue -- 判断值是否为秘密值

local DejaVu = _G["DejaVu"]

local BLACK = CreateColor(0, 0, 0, 1)
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local BadgeTitleTable = DejaVu.BadgeTitleTable
local BadgeTitleKey = {}


---@class BadgeCell
---@field Frame Frame BadgeCell底层框架
---@field Background Texture 背景纹理（+1层）
---@field Icon Texture 图标纹理（+2层）
---@field BadgeFrame Frame 脚标框架（+3层）
---@field BadgeTexture Texture 脚标纹理（+4层）
---@field Slug string 单元格唯一标识（格式: x_y）
---@field X integer X坐标
---@field Y integer Y坐标
---@field lastIcon? string|number 上次设置的图标（路径或ID）
---@field lastIconIsSecret boolean 上次图标是否为秘密值
---@field lastBadgeColor? colorRGBA 上次设置的脚标颜色
---@field lastBadgeColorIsSecret boolean 上次脚标颜色是否为秘密值
local BadgeCell = {}
BadgeCell.__index = BadgeCell

---BadgeCell 构造函数
---@param x integer X坐标（以单元格为单位）
---@param y integer Y坐标（以单元格为单位）
---@return BadgeCell # 返回BadgeCell实例, 如果父框架不存在则返回nil
function BadgeCell:New(x, y)
    local instance = setmetatable({}, self)
    instance:_initialize(x, y)
    return instance
end

---BadgeCell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
function BadgeCell:_initialize(x, y)
    local parent = addonTable.MartixFrame
    local cellSize = addonTable.SIZE.CELL
    local megaSize = addonTable.SIZE.MEGA
    local badgeSize = addonTable.SIZE.BADGE
    local cellSlug = x .. "_" .. y
    local cellName = addonName .. "BadgeCell_" .. cellSlug

    -- 底层Frame（+0层）
    local cellFrame = CreateFrame("Frame", cellName, parent)
    cellFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * cellSize, -y * cellSize)
    cellFrame:SetFrameLevel(parent:GetFrameLevel() + 1)
    cellFrame:SetSize(megaSize, megaSize)
    cellFrame:Show()

    -- 背景色层（+1层）
    local cellTexture = cellFrame:CreateTexture(nil, "BACKGROUND")
    cellTexture:SetAllPoints(cellFrame)
    cellTexture:SetTexture(WHITE_TEXTURE)
    cellTexture:SetVertexColor(BLACK:GetRGBA())
    cellTexture:Show()

    -- 图标层（+2层）
    local iconTexture = cellFrame:CreateTexture(nil, "ARTWORK")
    iconTexture:SetAllPoints(cellFrame)
    iconTexture:Hide()

    -- 脚标层Frame（+3层）
    local badgeFrame = CreateFrame("Frame", cellName .. "Badge", cellFrame)
    badgeFrame:SetPoint("BOTTOMRIGHT", cellFrame, "BOTTOMRIGHT", 0, 0)
    badgeFrame:SetFrameLevel(cellFrame:GetFrameLevel() + 1)
    badgeFrame:SetSize(badgeSize, badgeSize)
    badgeFrame:Hide()

    -- 脚标层贴图（+4层）
    local badgeTexture = badgeFrame:CreateTexture(nil, "ARTWORK")
    badgeTexture:SetAllPoints(badgeFrame)
    badgeTexture:SetTexture(WHITE_TEXTURE)
    badgeTexture:Hide()

    self.Frame = cellFrame
    self.Background = cellTexture
    self.Icon = iconTexture
    self.BadgeFrame = badgeFrame
    self.BadgeTexture = badgeTexture
    self.Slug = cellSlug
    self.X = x
    self.Y = y
    self.lastIcon = nil
    self.lastIconIsSecret = false
    self.lastBadgeColor = BLACK
    self.lastBadgeColorIsSecret = false
end

---比较图标是否相同（处理秘密值）
---如果任意图标是秘密值, 返回false（视为不同, 需要更新）
---如果都不是秘密值, 直接比较
---@private
---@param icon string|number 要比较的图标
---@return boolean # 如果图标相同返回true, 否则返回false
function BadgeCell:_isSameIcon(icon)
    -- 如果当前没有保存的图标, 视为不同
    if not self.lastIcon then
        return false
    end

    -- 如果任意一方是秘密值, 无法比较, 视为不同
    if self.lastIconIsSecret or issecretvalue(icon) then
        return false
    end

    -- 都不是秘密值, 直接比较
    return self.lastIcon == icon
end

---比较颜色是否相同（处理秘密值）
---如果任意颜色是秘密值, 返回false（视为不同, 需要更新）
---如果都不是秘密值, 使用IsEqualTo比较
---@private
---@param color colorRGBA|nil 要比较的颜色
---@return boolean # 如果颜色相同返回true, 否则返回false
function BadgeCell:_isSameBadgeColor(color)
    -- 如果当前没有保存的颜色, 视为不同
    if not self.lastBadgeColor then
        return false
    end

    -- 如果要比较的颜色是nil, 视为不同
    if not color then
        return false
    end

    -- 如果任意一方是秘密值, 无法比较, 视为不同
    if self.lastBadgeColorIsSecret or issecretvalue(color.r) then
        return false
    end

    -- 都不是秘密值, 使用colorRGBA的IsEqualTo方法
    return self.lastBadgeColor:IsEqualTo(color)
end

---设置单元格方法（设置图标和脚标颜色）
---@param icon string|number 图标路径或纹理ID
---@param color colorRGBA 脚标颜色
---@param title? string 脚标提示文本（目前未使用, 预留接口）
function BadgeCell:setCell(icon, color, title)
    -- 处理图标
    local iconIsSecret = issecretvalue(icon)
    local iconChanged = not self:_isSameIcon(icon)

    if iconChanged then
        self.lastIcon = icon
        self.lastIconIsSecret = iconIsSecret
        self.Icon:SetTexture(icon)
        self.Icon:Show()
    end

    -- 处理脚标颜色
    local colorIsSecret = issecretvalue(color.r)
    local colorChanged = not self:_isSameBadgeColor(color)

    if colorChanged then
        self.lastBadgeColor = color
        self.lastBadgeColorIsSecret = colorIsSecret
        self.BadgeTexture:SetVertexColor(color:GetRGBA())
        self.BadgeFrame:Show()
        self.BadgeTexture:Show()
    end
    if (title ~= nil) and (not issecretvalue(title)) then
        local titleKey = format("%s_%s_%s_%s", tostring(icon), tostring(color.r), tostring(color.g), tostring(color.b))
        if not BadgeTitleKey[titleKey] then
            BadgeTitleKey[titleKey] = true
            insert(BadgeTitleTable, {
                icon = icon,
                color = color,
                title = title
            })
        end
    end
end

---清除单元格方法（隐藏图标和脚标, 显示底色）
function BadgeCell:clearCell()
    self.Icon:Hide()
    self.BadgeFrame:Hide()
    self.BadgeTexture:Hide()
    self.lastIcon = nil
    self.lastIconIsSecret = false
    self.lastBadgeColor = nil
    self.lastBadgeColorIsSecret = false
end

---工厂函数: 创建 BadgeCell 实例
---@param x integer X坐标
---@param y integer Y坐标
---@return BadgeCell # 返回BadgeCell实例
DejaVu.CreateBadgeCell = function(x, y)
    return BadgeCell:New(x, y)
end

DejaVu.BadgeCell = BadgeCell
