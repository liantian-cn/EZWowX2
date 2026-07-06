-- 命名空间声明
local addonName, addonTable    = ...

-- WOW API 缓存
local After                    = C_Timer.After
local insert                   = table.insert -- 插入表元素
local CreateFrame              = CreateFrame  -- 创建框体
local CreateColor              = CreateColor
local UIParent                 = UIParent     -- 游戏主界面父框体
local CreateColorCurve         = C_CurveUtil.CreateColorCurve
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean
local Linear                   = Enum.LuaCurveType.Linear

-- 插件级变量定义/引用

local GetUIScaleFactor         = addonTable.GetUIScaleFactor -- UI 缩放计算
addonTable.FrameInitFuncs      = {}                          -- 框架初始化函数表
addonTable.SIZE                = {}                          -- 尺寸表


-- 本地变量定义
local scale         = 6
local SIZE          = addonTable.SIZE
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local BLACK         = CreateColor(0, 0, 0, 1)

-- 代码部分

local function InitializeSize()             -- 初始化尺寸
    SIZE = {                                -- 尺寸表主体
        Martix = {                          -- MartixFrame有多个Cell
            Width = 258,                    -- Cell横向个数
            Height = 10,                    -- Cell纵向个数
        },
        CELL = GetUIScaleFactor(scale * 4), -- Cell尺寸
        FONT = GetUIScaleFactor(scale * 6), -- Font尺寸
        -- MEGA = GetUIScaleFactor(scale * 8),  -- MegaCell尺寸
        -- BADGE = GetUIScaleFactor(scale * 2), -- Badge尺寸
        -- PAD = GetUIScaleFactor(scale * 1),  -- Padding尺寸
    }
    addonTable.SIZE = SIZE -- 将尺寸表赋值给插件级变量
end
After(0, function()
    for _, func in ipairs(addonTable.FrameInitFuncs) do
        func()
    end
end)


local function CreateMartixFrame() -- 创建矩阵框架
    InitializeSize()

    local frame = CreateFrame("Frame", addonName .. "MartixFrame", UIParent)
    frame:SetPoint("TOPLEFT", UIParent, "TOPLEFT", 0, 0)
    frame:SetSize(SIZE.CELL * SIZE.Martix.Width, SIZE.CELL * SIZE.Martix.Height)
    frame:SetFrameStrata("TOOLTIP")
    frame:SetFrameLevel(9000)
    frame:Show()

    local bg = frame:CreateTexture(nil, "BACKGROUND")
    bg:SetAllPoints()
    bg:SetColorTexture(0, 0, 0, 1)
    bg:Show()
    addonTable.MartixFrame = frame
end
insert(addonTable.FrameInitFuncs, CreateMartixFrame)

---@class Cell
---@field Texture Texture 单元格纹理
---@field Frame Frame 单元格框架
---@field X integer X坐标
---@field Y integer Y坐标
---@field classification integer 分类（根据cell用途不同，每个cell有个分类设置，范围0-255）
---@field index integer 索引（相同分类的cell，每个cell有个索引设置，范围0-255）
---@field default_value number 默认值（范围0-255），用于初始化cell的颜色分量
---@field backgroundColor colorRGBA 背景颜色
---@field trueColor colorRGBA 真值颜色
---@field falseColor colorRGBA 假值颜色
---@field zeroToOneCurve ColorCurveObject 颜色曲线（0-1）
---@field quantizedCurve ColorCurveObject 颜色曲线（0-51）
local Cell = {}
Cell.__index = Cell

---Cell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
---@param classification integer 分类（根据cell用途不同，每个cell有个分类设置，范围0-255）
---@param index integer 索引（相同分类的cell，每个cell有个索引设置，范围1-255，0保留不用）
---@param default_value number 默认值（范围0-255），用于初始化cell的颜色分量
function Cell:_initialize(x, y, classification, index, default_value)
    local parent = addonTable.MartixFrame
    local cellName = addonName .. "Cell_" .. x .. "_" .. y

    local cellFrame = CreateFrame("Frame", cellName, parent)
    cellFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * SIZE.CELL, -(y - 1) * SIZE.CELL)
    cellFrame:SetFrameLevel(parent:GetFrameLevel() + 10)
    cellFrame:SetSize(SIZE.CELL, SIZE.CELL)
    cellFrame:Show()

    local cellTexture = cellFrame:CreateTexture(nil, "BACKGROUND")
    cellTexture:SetAllPoints(cellFrame)
    cellTexture:SetTexture(WHITE_TEXTURE)
    cellTexture:Show()

    self.Texture = cellTexture
    self.Frame = cellFrame
    self.Slug = cellSlug
    self.X = x
    self.Y = y
    self.classification = classification
    self.index = index
    self.default_value = default_value
    self.backgroundColor = CreateColor(classification / 255, index / 255, default_value / 255, 1)
    self.trueColor = CreateColor(classification / 255, index / 255, 1, 1)
    self.falseColor = CreateColor(classification / 255, index / 255, 0, 1)

    local zeroToOneCurve = CreateColorCurve()
    zeroToOneCurve:SetType(Linear)
    zeroToOneCurve:AddPoint(0.0, CreateColor(classification / 255, index / 255, 0, 1))
    zeroToOneCurve:AddPoint(1.0, CreateColor(classification / 255, index / 255, 1, 1))

    local quantizedCurve = CreateColorCurve()
    quantizedCurve:SetType(Linear)
    quantizedCurve:AddPoint(0.0, CreateColor(classification / 255, index / 255, 0, 1))
    quantizedCurve:AddPoint(51.0, CreateColor(classification / 255, index / 255, 1, 1))

    self.zeroToOneCurve = zeroToOneCurve
    self.quantizedCurve = quantizedCurve

    self:setCell(self.backgroundColor)
end

---Cell 构造函数
---@param options table 构造参数
-- -@field x integer X坐标（以单元格为单位）
-- -@field y integer Y坐标（以单元格为单位）
-- -@field classification integer 分类（根据cell用途不同，每个cell有个分类设置，范围0-255）
-- -@field index integer 索引（相同分类的cell，每个cell有个索引设置，范围0-255）
-- -@field default_value? number 默认值（范围0-255），用于初始化cell的颜色分量
---@return Cell # 返回Cell实例, 如果父框架不存在则返回nil
function Cell:New(options)
    local instance = setmetatable({}, self)
    local default_value = options.default_value or 0
    instance:_initialize(options.x, options.y, options.classification, options.index, default_value)
    return instance
end

---使用最基础的 RGBA 方式设置颜色
---@param r number|string|table 红色分量
---@param g number|string|table 绿色分量
---@param b number|string|table 蓝色分量
function Cell:setCellRGBA(r, g, b)
    self.Texture:SetVertexColor(r, g, b, 1)
end

---设置颜色方法
---@param color colorRGBA 要设置的颜色
function Cell:setCell(color)
    self:setCellRGBA(color:GetRGBA())
end

---设置颜色方法, 根据布尔值选择颜色
---@param isTrue boolean 是否为true值
---@param reverse boolean 是否反转颜色选择，默认false
---@return nil
function Cell:setCellBoolean(isTrue, reverse)
    if reverse then
        self:setCell(EvaluateColorFromBoolean(isTrue, self.falseColor, self.trueColor))
    else
        self:setCell(EvaluateColorFromBoolean(isTrue, self.trueColor, self.falseColor))
    end
end

---清除颜色方法, 就是恢复默认的黑色
function Cell:clearCell()
    self:setCell(self.backgroundColor)
end

addonTable.Cell = Cell

---@class IconCell
---@field Frame Frame 图标框体
---@field Background Texture 背景纹理
---@field Icon Texture 图标纹理
---@field Border Texture 边框纹理
---@field BorderColor ColorMixin 边框颜色
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
    local iconSize = 4 * SIZE.CELL  -- 4倍cell大小

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
    border:SetTexture("Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga")
    border:SetVertexColor(0, 0, 0, 0)  -- 默认透明
    border:Hide()

    self.Frame = frame
    self.Background = background
    self.Icon = icon
    self.Border = border
    self.BorderColor = CreateColor(0, 0, 0, 0)  -- 默认透明
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
    self.BorderColor = color
    self.Border:SetVertexColor(color:GetRGBA())
    self.Border:Show()
end

addonTable.IconCell = IconCell

local function InitMarkFrame()
    local MARKER_CLASSIFICATION = 255
    local MARKER_VALUE = 255
    local MARKER_VALUE_START = 255
    local MARKER_VALUE_END = 0
    Cell:New({ x = 0, y = 1, classification = MARKER_CLASSIFICATION, index = 1, default_value = MARKER_VALUE_START })
    Cell:New({ x = 257, y = 1, classification = MARKER_CLASSIFICATION, index = 1, default_value = MARKER_VALUE_END })
end
insert(addonTable.FrameInitFuncs, InitMarkFrame)
