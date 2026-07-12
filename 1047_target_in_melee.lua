-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CheckInteractDistance = CheckInteractDistance
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
简述：      目标处于近战范围内
分类：      目标状态
分类索引：  7
位置：      1行47列

说明

优先使用LibRangeCheck-3.0读取目标距离上限；无法判断时使用CheckInteractDistance的近战交互距离作为后备。

]]

local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.TARGET_STATUS
local CELL_CLASSIFICATION_INDEX = 7
local CELL_POSITION_X = 47
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

        if rangeChecker then
            local _, maxRange = rangeChecker:GetRange(UNIT_TOKEN)

            if issecretvalue(maxRange) then
                cell:clearCell()
                return
            end

            if maxRange ~= nil then
                cell:setCellBoolean(maxRange <= addonTable.MELEE_RANGE)
                return
            end
        end

        local inMeleeRange = CheckInteractDistance(UNIT_TOKEN, 3)

        if issecretvalue(inMeleeRange) or inMeleeRange == nil then
            cell:clearCell()
        else
            cell:setCellBoolean(inMeleeRange)
        end
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
