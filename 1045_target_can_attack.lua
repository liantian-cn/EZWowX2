-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local UnitCanAttack         = UnitCanAttack
local UnitExists            = UnitExists

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      目标可攻击状态
分类：      目标状态
分类索引：  5
位置：      1行55列

说明

使用UnitCanAttack检测玩家是否可以攻击当前目标。

]]

local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.TARGET_STATUS
local CELL_CLASSIFICATION_INDEX = 5
local CELL_POSITION_X = 55
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

        cell:setCellBoolean(UnitCanAttack("player", UNIT_TOKEN))
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
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
