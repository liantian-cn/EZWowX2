-- 插件入口
local addonName, addonTable = ... -- 插件名称与共享表

-- Lua 原生函数
local setmetatable = setmetatable

-- WoW 官方 API
local CreateFrame = CreateFrame                                       -- 创建框体
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 按布尔值映射颜色
local issecretvalue = issecretvalue                                   -- 判断值是否为秘密值

local DejaVu = _G["DejaVu"]

local BLACK = CreateColor(0, 0, 0, 1)
local WHITE = CreateColor(1, 1, 1, 1)
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"



---@class Cell
---@field Texture Texture 单元格纹理
---@field Frame Frame 单元格框架
---@field Slug string 单元格唯一标识（格式: x_y）
---@field X integer X坐标
---@field Y integer Y坐标
---@field lastR? number|string|table 上次设置的红色分量
---@field lastG? number|string|table 上次设置的绿色分量
---@field lastB? number|string|table 上次设置的蓝色分量
---@field lastA? number|string|table 上次设置的透明度分量
---@field lastRGBAIsSecret? boolean 上次颜色分量是否包含秘密值
local Cell = {}
Cell.__index = Cell

---Cell 构造函数
---@param x integer X坐标（以单元格为单位）
---@param y integer Y坐标（以单元格为单位）
---@param backgroundColor? colorRGBA 背景颜色, 默认为黑色
---@return Cell # 返回Cell实例, 如果父框架不存在则返回nil
function Cell:New(x, y, backgroundColor)
    local instance = setmetatable({}, self)
    instance:_initialize(x, y, backgroundColor)
    return instance
end

---Cell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
---@param backgroundColor? colorRGBA 背景颜色
function Cell:_initialize(x, y, backgroundColor)
    if not backgroundColor then
        backgroundColor = BLACK
    end

    local parent = addonTable.MartixFrame
    local cellSize = addonTable.SIZE.CELL
    local cellSlug = x .. "_" .. y
    local cellName = addonName .. "Cell_" .. cellSlug

    local cellFrame = CreateFrame("Frame", cellName, parent)
    cellFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * cellSize, -y * cellSize)
    cellFrame:SetFrameLevel(parent:GetFrameLevel() + 10)
    cellFrame:SetSize(cellSize, cellSize)
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
    self:setCell(backgroundColor)
end

---判断 RGBA 分量里是否包含秘密值
---@param r number|string|table 红色分量
---@param g number|string|table 绿色分量
---@param b number|string|table 蓝色分量
---@param a number|string|table 透明度分量
---@return boolean
local function IsSecretRGBA(r, g, b, a)
    return issecretvalue(r) or issecretvalue(g) or issecretvalue(b) or issecretvalue(a)
end

---比较 RGBA 是否相同（处理秘密值）
---如果任意一方包含秘密值, 返回false（视为不同, 需要更新）
---@private
---@param r number|string|table 红色分量
---@param g number|string|table 绿色分量
---@param b number|string|table 蓝色分量
---@param a number|string|table 透明度分量
---@return boolean # 如果颜色相同返回true, 否则返回false
function Cell:_isSameRGBA(r, g, b, a)
    if self.lastR == nil then
        return false
    end

    if self.lastRGBAIsSecret or IsSecretRGBA(r, g, b, a) then
        return false
    end

    return self.lastR == r
        and self.lastG == g
        and self.lastB == b
        and self.lastA == a
end

---使用最基础的 RGBA 方式设置颜色
---@param r number|string|table 红色分量
---@param g number|string|table 绿色分量
---@param b number|string|table 蓝色分量
---@param a? number|string|table 透明度分量, 默认为1
function Cell:setCellRGBA(r, g, b, a)
    if a == nil then
        a = 1
    end

    if g == nil then
        g = r
    end

    if b == nil then
        b = r
    end

    if self:_isSameRGBA(r, g, b, a) then
        return
    end

    self.lastR = r
    self.lastG = g
    self.lastB = b
    self.lastA = a
    self.lastRGBAIsSecret = IsSecretRGBA(r, g, b, a)
    self.Texture:SetVertexColor(r, g, b, a)
end

---设置颜色方法
---@param color colorRGBA 要设置的颜色
function Cell:setCell(color)
    if color == nil then
        color = BLACK
    end

    self:setCellRGBA(color:GetRGBA())
end

---设置颜色方法, 根据布尔值选择颜色
---@param isTrue boolean 是否为true值
---@param trueColor colorRGBA 要设置的颜色
---@param falseColor colorRGBA 要设置的颜色
---@return nil
function Cell:setCellBoolean(isTrue, trueColor, falseColor)
    trueColor = trueColor or WHITE
    falseColor = falseColor or BLACK
    self:setCell(EvaluateColorFromBoolean(isTrue, trueColor, falseColor))
end

---清除颜色方法, 就是恢复默认的黑色
function Cell:clearCell()
    -- 如果颜色相同, 跳过设置以提高性能
    local color = BLACK
    self:setCell(color)
end

---工厂函数: 创建 Cell 实例
---@param x integer X坐标
---@param y integer Y坐标
---@param backgroundColor? colorRGBA 背景颜色
---@return Cell # 返回Cell实例
DejaVu.CreateCell = function(x, y, backgroundColor)
    return Cell:New(x, y, backgroundColor)
end

DejaVu.Cell = Cell
