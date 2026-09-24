-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local UnitExists            = UnitExists
local UnitIsDeadOrGhost     = UnitIsDeadOrGhost

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      目标处于存活状态
分类：      目标状态
分类索引：  2
位置：      1行42列

说明

使用UnitIsDeadOrGhost检测目标是否死亡，并通过Cell:setCellBoolean的反转参数显示为“存活”。

]]

local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.TARGET_STATUS
local CELL_CLASSIFICATION_INDEX = 2
local CELL_POSITION_X = 42
local CELL_POSITION_Y = 1

local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2
local UNIT_TOKEN = "target"

local function InitFrame()
    local eventFrame = CreateFrame("Frame")

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

        cell:setCellBoolean(UnitIsDeadOrGhost(UNIT_TOKEN), true)
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
    eventFrame:RegisterEvent("UNIT_TARGETABLE_CHANGED")
    eventFrame:RegisterUnitEvent("UNIT_HEALTH", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_MAXHEALTH", UNIT_TOKEN)

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
