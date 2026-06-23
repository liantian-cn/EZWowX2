--[[

]]
-- 插件入口
local addonName, addonTable = ... -- 插件名称与共享表

-- Lua 原生函数
local setmetatable = setmetatable

-- WoW 官方 API
local CreateFrame = CreateFrame     -- 创建框体
local issecretvalue = issecretvalue -- 判断值是否为秘密值

local DejaVu = _G["DejaVu"]

---@class Bar
---@field Frame Frame 单元格框架
---@field Slug string 单元格唯一标识（格式: x_y）
---@field X integer X坐标
---@field Y integer Y坐标
---@field width number 宽度
---@field minValue number 最小值
---@field maxValue number 最大值
---@field currentValue number 当前值
local Bar = {}
Bar.__index = Bar

Bar.StatusBar = nil
Bar.minMaxIsSecret = nil
Bar.currentValueIsSecret = nil

---Bar 构造函数
---@param x integer X坐标（以单元格为单位）
---@param y integer Y坐标（以单元格为单位）
---@param width number 宽度
---@return Bar|nil # 返回Bar实例, 如果父框架不存在则返回nil
function Bar:New(x, y, width, reverse)
    if reverse and (reverse == true) then
        reverse = true
    else
        reverse = false
    end
    local instance = setmetatable({}, self)
    instance:_initialize(x, y, width, reverse)
    return instance
end

---Bar 初始化方法（私有）
---@private
---@param x integer X坐标
---@param y integer Y坐标
---@param width number 宽度
---@param reverse boolean 是否反向填充
function Bar:_initialize(x, y, width, reverse)
    local parent = addonTable.MartixFrame
    local BarSize = addonTable.SIZE.CELL
    local BarSlug = x .. "_" .. y
    local BarName = addonName .. "Bar_" .. BarSlug

    local BarFrame = CreateFrame("Frame", BarName, parent)
    BarFrame:SetPoint("TOPLEFT", parent, "TOPLEFT", x * BarSize, -y * BarSize)
    BarFrame:SetFrameLevel(parent:GetFrameLevel() + 1)
    BarFrame:SetSize(width * BarSize, BarSize)
    BarFrame:Show()

    -- local BarTexture = BarFrame:CreateTexture(nil, "BACKGROUND")
    -- BarTexture:SetAllPoints(BarFrame)
    -- BarTexture:SetColorTexture(1, 1, 1, 1)

    local StatusBar = CreateFrame("StatusBar", nil, BarFrame)
    StatusBar:SetAllPoints(BarFrame)
    StatusBar:SetStatusBarTexture("Interface\\Buttons\\WHITE8X8")
    StatusBar:SetStatusBarColor(1, 1, 1, 1)
    if reverse then
        StatusBar:SetReverseFill(true)
    end
    -- self.Texture = BarTexture
    self.Frame = BarFrame
    self.Slug = BarSlug
    self.X = x
    self.Y = y
    self.width = width
    self.StatusBar = StatusBar
    self:setMinMaxValues(0, 100)
    self:setValue(50)
end

local function IsSecretMinMax(minValue, maxValue)
    return issecretvalue(minValue) or issecretvalue(maxValue)
end

local function IsSecretBarValue(currentValue)
    return issecretvalue(currentValue)
end

function Bar:_isSameMinMax(minValue, maxValue)
    if self.minValue == nil or self.maxValue == nil then
        return false
    end

    if self.minMaxIsSecret or IsSecretMinMax(minValue, maxValue) then
        return false
    end

    return self.minValue == minValue and self.maxValue == maxValue
end

function Bar:_isSameValue(currentValue)
    if self.currentValue == nil then
        return false
    end

    if self.currentValueIsSecret or IsSecretBarValue(currentValue) then
        return false
    end

    return self.currentValue == currentValue
end

function Bar:setMinMaxValues(minValue, maxValue)
    if self:_isSameMinMax(minValue, maxValue) then
        return
    end

    self.minValue = minValue
    self.maxValue = maxValue
    self.minMaxIsSecret = IsSecretMinMax(minValue, maxValue)
    self.StatusBar:SetMinMaxValues(minValue, maxValue)
end

function Bar:setValue(currentValue)
    if self:_isSameValue(currentValue) then
        return
    end

    self.currentValue = currentValue
    self.currentValueIsSecret = IsSecretBarValue(currentValue)
    self.StatusBar:SetValue(currentValue)
end

DejaVu.Bar = Bar
