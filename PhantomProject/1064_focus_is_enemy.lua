-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local UnitExists            = UnitExists
local UnitIsEnemy           = UnitIsEnemy

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      焦点敌对状态
分类：      焦点目标
分类索引：  4
位置：      1行64列

说明

使用UnitIsEnemy检测当前焦点是否为玩家的敌对单位。

]]

local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.FOCUS_TARGET
local CELL_CLASSIFICATION_INDEX = 4
local CELL_POSITION_X = 64
local CELL_POSITION_Y = 1

local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2
local UNIT_TOKEN = "focus"

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

        cell:setCellBoolean(UnitIsEnemy(UNIT_TOKEN, "player"))
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_FOCUS_CHANGED")
    eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")
    eventFrame:RegisterEvent("UNIT_TARGETABLE_CHANGED")
    eventFrame:RegisterUnitEvent("UNIT_FACTION", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_FLAGS", UNIT_TOKEN)

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
