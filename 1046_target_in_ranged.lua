-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local issecretvalue         = issecretvalue
local LibStub               = LibStub
local UnitExists            = UnitExists

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      目标处于远程范围内
分类：      目标状态
分类索引：  6
位置：      1行46列

说明

优先使用LibRangeCheck-3.0读取目标距离上限，距离不可判断时清除cell，避免保留旧状态。

]]

local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.TARGET_STATUS
local CELL_CLASSIFICATION_INDEX = 6
local CELL_POSITION_X = 46
local CELL_POSITION_Y = 1

local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2
local UNIT_TOKEN = "target"

local function InitFrame()
    local eventFrame = CreateFrame("Frame")
    local rangeChecker = nil

    if LibStub then
        rangeChecker = LibStub("LibRangeCheck-3.0", true)
    end

    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local function updateCell()
        if not UnitExists(UNIT_TOKEN) then
            cell:clearCell()
            return
        end

        if not rangeChecker then
            cell:clearCell()
            return
        end

        local _, maxRange = rangeChecker:GetRange(UNIT_TOKEN)

        if issecretvalue(maxRange) or maxRange == nil then
            cell:clearCell()
            return
        end

        cell:setCellBoolean(maxRange <= addonTable.RANGED_RANGE)
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
    eventFrame:RegisterEvent("UNIT_TARGETABLE_CHANGED")
    eventFrame:RegisterEvent("UNIT_IN_RANGE_UPDATE")
    eventFrame:RegisterEvent("UNIT_DISTANCE_CHECK_UPDATE")
    eventFrame:RegisterEvent("PLAYER_STARTED_MOVING")
    eventFrame:RegisterEvent("PLAYER_STOPPED_MOVING")
    eventFrame:RegisterEvent("SPELL_UPDATE_USABLE")

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCell()
    end)

    local fallbackElapsed = 0
    eventFrame:SetScript("OnUpdate", function(self, elapsed)
        fallbackElapsed = fallbackElapsed + elapsed

        if fallbackElapsed >= FALLBACK_REFRESH_SECONDS then
            fallbackElapsed = 0
            updateCell()
        end
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
