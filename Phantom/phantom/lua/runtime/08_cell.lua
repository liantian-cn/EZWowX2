--[[
original: runtime\08_cell.lua
uuid: 3be6cff3-7f5f-460e-a810-8058d1d27a90
runtime_index: 8
摘要：创建矩阵单元格，并提供 RGB、颜色对象与布尔值着色接口。


描述：
    按指定行列在共享背景框体下创建方形纹理，初始化为不透明黑色并保存坐标。
    复用 CellBackplate 的框体，由背板独立登记行宽与更新画布。
    提供颜色更新、布尔值黑白映射及反转、恢复黑色的方法，并通过 addonTable.Cell 公开。


修改记录：
2026-09-20：复用独立黑色背板，颜色纹理使用 ARTWORK。
2026-09-06：liantian-cn初始化创建。

]]


--[[  namespace initialization  ]]

local addonName, addonTable = ...

--[[  api cache  ]]

local CreateFrame              = CreateFrame  -- 创建框体
local EvaluateColorFromBoolean = C_CurveUtil.EvaluateColorFromBoolean -- 按布尔值选择对应颜色

--[[  variable reference  ]]

local COLOR                 = addonTable.COLOR       -- 共享基础颜色，提供单元格黑白配色
local CellBackplate         = addonTable.CellBackplate -- 固定黑色背板构造器
local FrameLevel            = addonTable.FrameLevel  -- 背景与 Cell 底层框体的层级定义
local SIZE                  = addonTable.SIZE        -- 共享 Cell 尺寸定义
local BackgroundFrameResize = addonTable.BackgroundFrameResize -- 按共享长度数据调整背景尺寸


--[[  logical code  ]]

local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8" -- 用于着色的白色基础纹理
local TRUE_COLOR = COLOR.WHITE -- 布尔真值默认显示白色
local FALSE_COLOR = COLOR.BLACK -- 布尔假值默认显示黑色

---@class Cell
---@field Backplate CellBackplate 固定黑色背板
---@field Texture Texture 单元格纹理
---@field Frame Frame 单元格框架
---@field X integer X坐标
---@field Y integer Y坐标
local Cell = {} -- 单元格的方法集合
Cell.__index = Cell -- 实例从 Cell 表查找方法


---Cell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
function Cell:_initialize(x, y) -- 按列号和行号创建单元格
    self.Backplate = CellBackplate:New({x = x, y = y}) -- 背板负责几何与计数
    local cellFrame = self.Backplate.Frame -- 复用内容矩形
    local cellTexture = cellFrame:CreateTexture(nil, "ARTWORK") -- 在固定黑底上创建颜色纹理
    cellTexture:SetAllPoints(cellFrame) -- 让纹理覆盖整个单元格
    cellTexture:SetTexture(WHITE_TEXTURE) -- 使用白色纹理承载后续颜色
    cellTexture:Show() -- 显示单元格纹理

    self.Texture = cellTexture -- 保存用于更新颜色的纹理
    self.Frame = cellFrame -- 保存单元格框体
    self.X = x -- 保存列号
    self.Y = y -- 保存行号

    self:setCell(COLOR.BLACK) -- 将单元格设为黑色
end

---使用 RGB 分量设置颜色，透明度固定为 1
---@param r number|string|table 红色分量
---@param g number|string|table 绿色分量
---@param b number|string|table 蓝色分量
function Cell:setCellRGBA(r, g, b) -- 按 RGB 分量更新单元格颜色
    self.Texture:SetVertexColor(r, g, b, 1) -- 应用颜色并固定为完全不透明
end

---设置颜色方法
---@param color colorRGBA 要设置的颜色
function Cell:setCell(color) -- 从颜色对象读取分量并更新单元格
    self:setCellRGBA(color:GetRGBA()) -- 传入颜色分量，透明度由 setCellRGBA 固定为 1
end

---Cell 构造函数
---@param options table 构造参数
---@return Cell # 返回初始化后的 Cell 实例
function Cell:New(options) -- 使用 options.x 和 options.y 构造单元格实例
    local instance = setmetatable({}, self) -- 创建共享 Cell 方法的新实例
    instance:_initialize(options.x, options.y) -- 按指定坐标初始化框体和纹理
    return instance -- 返回初始化后的单元格
end

---设置颜色方法, 根据布尔值选择颜色
---@param isTrue boolean 是否为true值
---@param reverse boolean 是否反转颜色选择，默认false
---@return nil
function Cell:setCellBoolean(isTrue, reverse) -- 将布尔值映射为黑白颜色
    if reverse then -- 反转真值与假值的默认配色
        self:setCell(EvaluateColorFromBoolean(isTrue, FALSE_COLOR, TRUE_COLOR)) -- 真值显示黑色，假值显示白色
    else
        self:setCell(EvaluateColorFromBoolean(isTrue, TRUE_COLOR, FALSE_COLOR)) -- 真值显示白色，假值显示黑色
    end
end

---清除颜色方法, 就是恢复默认的黑色
function Cell:clearCell() -- 恢复单元格默认底色
    self:setCell(COLOR.BLACK) -- 将单元格设为黑色
end

addonTable.Cell = Cell -- 向后续模块公开 Cell 构造与颜色操作接口
