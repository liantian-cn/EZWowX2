-- 插件入口
local addonName, addonTable = ... -- 插件名称与共享表

-- Lua 原生函数
local setmetatable = setmetatable

-- WoW 官方 API
local CreateFrame = CreateFrame     -- 创建框体
local issecretvalue = issecretvalue -- 判断值是否为秘密值

local DejaVu = _G["DejaVu"]

local BLACK = CreateColor(0, 0, 0, 1)


---@class CharCell
---@field Frame Frame CharCell底层框架
---@field Background Texture 背景纹理（+1层）
---@field FontString FontString 文本层（+2层）
---@field Slug string 单元格唯一标识（格式: x_y）
---@field X integer X坐标
---@field Y integer Y坐标
---@field lastText? string 上次设置的文本
---@field lastTextIsSecret boolean 上次文本是否为秘密值
local CharCell = {}
CharCell.__index = CharCell

---CharCell 构造函数
---@param x integer X坐标（以单元格为单位）
---@param y integer Y坐标（以单元格为单位）
---@return CharCell # 返回CharCell实例, 如果父框架不存在则返回nil
function CharCell:New(x, y)
    local instance = setmetatable({}, self)
    instance:_initialize(x, y)
    return instance
end

---CharCell 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
function CharCell:_initialize(x, y)
    local parent = addonTable.MartixFrame
    local cellSize = addonTable.SIZE.CELL
    local megaSize = addonTable.SIZE.MEGA
    local fontSize = addonTable.SIZE.FONT
    local fontPath = addonTable.FontPath
    local cellSlug = x .. "_" .. y
    local cellName = addonName .. "CharCell_" .. cellSlug

    -- 底层Frame（+0层）
    local cellFrame = CreateFrame("Frame", cellName, parent)
    cellFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * cellSize, -y * cellSize)
    cellFrame:SetFrameLevel(parent:GetFrameLevel() + 1)
    cellFrame:SetSize(megaSize, megaSize)
    cellFrame:Show()

    -- 背景色层（+1层）
    local cellTexture = cellFrame:CreateTexture(nil, "BACKGROUND")
    cellTexture:SetAllPoints(cellFrame)
    cellTexture:SetColorTexture(BLACK:GetRGBA())
    cellTexture:Show()

    -- 文本层（+2层）
    local fontString = cellFrame:CreateFontString(nil, "ARTWORK")
    fontString:SetAllPoints(cellFrame)
    fontString:SetJustifyH("CENTER")
    fontString:SetJustifyV("MIDDLE")
    fontString:SetFontObject(GameFontHighlight)
    fontString:SetTextColor(1, 1, 1, 1)
    -- print(fontSize)
    fontString:SetFont(fontPath, fontSize, "MONOCHROME")
    fontString:SetText("")
    fontString:Show()

    self.Frame = cellFrame
    self.Background = cellTexture
    self.FontString = fontString
    self.Slug = cellSlug
    self.X = x
    self.Y = y
    self.lastText = nil
    self.lastTextIsSecret = false
end

---比较文本是否相同（处理秘密值）
---如果任意文本是秘密值, 返回false（视为不同, 需要更新）
---如果都不是秘密值, 直接比较
---@private
---@param text string 要比较的文本
---@return boolean $ 如果文本相同返回true, 否则返回false
function CharCell:_isSameText(text)
    -- 如果当前没有保存的文本, 视为不同
    if not self.lastText then
        return false
    end

    -- 如果任意一方是秘密值, 无法比较, 视为不同
    if self.lastTextIsSecret or issecretvalue(text) then
        return false
    end

    -- 都不是秘密值, 直接比较
    return self.lastText == text
end

---设置单元格方法（设置文本）
---@param text string 要显示的文本
function CharCell:setCell(text)
    -- 如果文本相同, 跳过设置以提高性能
    if self:_isSameText(text) then
        return
    end

    -- 保存文本状态
    self.lastText = text
    self.lastTextIsSecret = issecretvalue(text)

    -- 设置文本
    self.FontString:SetText(text)
end

---清除单元格方法（清空文本）
function CharCell:clearCell()
    self.FontString:SetText("")
    self.lastText = nil
    self.lastTextIsSecret = false
end

---工厂函数: 创建 CharCell 实例
---@param x integer X坐标
---@param y integer Y坐标
---@return CharCell|nil 返回CharCell实例
DejaVu.CreateCharCell = function(x, y)
    return CharCell:New(x, y)
end

-- 暴露 CharCell底层框架
DejaVu.CharCell = CharCell
