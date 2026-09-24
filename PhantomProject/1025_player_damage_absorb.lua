-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame = CreateFrame
local UnitGetTotalAbsorbs = UnitGetTotalAbsorbs

-- 插件级变量定义/引用
local PLAYER_STATUS = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local ABSORB_THRESHOLD = addonTable.PLAYER_DAMAGE_ABSORB_THRESHOLD

-- 本地变量定义
local insert = table.insert
local CELL_INDEX = 25
local CELL_POSITION_X = 25
local CELL_POSITION_Y = 1
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"

-- 代码部分

--[[
简述：      玩家伤害吸收量是否超过阈值
分类：      玩家状态
分类索引：  25
位置：      1行25列

说明

状态条直接接收可能为秘密值的伤害吸收量，不在Lua中读取或计算该值。
吸收量不超过10000时显示B=0，至少为10001时显示B=1。
]]

local function InitFrame()
    local parent = addonTable.MartixFrame
    local SIZE = addonTable.SIZE
    local r = PLAYER_STATUS / 255
    local g = CELL_INDEX / 255

    local absorbBar = CreateFrame("StatusBar", nil, parent)
    absorbBar:SetSize(SIZE.CELL, SIZE.CELL)
    absorbBar:SetPoint("TOPLEFT", parent, "TOPLEFT", CELL_POSITION_X * SIZE.CELL, -(CELL_POSITION_Y - 1) * SIZE.CELL)
    absorbBar:SetStatusBarTexture(WHITE_TEXTURE)
    absorbBar:SetStatusBarColor(r, g, 1, 1)
    absorbBar:SetMinMaxValues(ABSORB_THRESHOLD, ABSORB_THRESHOLD + 1)

    local background = absorbBar:CreateTexture(nil, "BACKGROUND")
    background:SetAllPoints(absorbBar)
    background:SetColorTexture(r, g, 0, 1)

    local function updateBar()
        absorbBar:SetValue(UnitGetTotalAbsorbs("player"))
    end

    absorbBar:SetScript("OnEvent", updateBar)
    absorbBar:RegisterUnitEvent("UNIT_ABSORB_AMOUNT_CHANGED", "player")
    updateBar()
end

insert(addonTable.FrameInitFuncs, InitFrame)
