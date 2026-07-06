-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CheckInteractDistance = CheckInteractDistance
local CreateFrame           = CreateFrame
local LibStub               = LibStub
local UnitCanAttack         = UnitCanAttack
local UnitExists            = UnitExists

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert
local min                   = math.min
local select                = select

-- 代码部分

--[[
简述：      玩家近战范围敌人数量
分类：      玩家属性
分类索引：  11
位置：      1行11列

说明

扫描nameplate1到nameplate40，统计可攻击且处于近战范围的单位数量。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 11
local CELL_POSITION_X = 11
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架
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

    local function unitIsInMeleeRange(unit)
        if rangeChecker then
            local maxRange = select(2, rangeChecker:GetRange(unit))
            return maxRange ~= nil and maxRange <= 5
        end

        return CheckInteractDistance(unit, 3)
    end

    local function updateCell()
        local count = 0

        for index = 1, 40 do
            local unit = "nameplate" .. index

            if UnitExists(unit) and UnitCanAttack("player", unit) and unitIsInMeleeRange(unit) then
                count = count + 1
            end
        end

        local value = min(count / 51, 1)
        cell:setCellRGBA(CELL_CLASSIFICATION / 255, CELL_CLASSIFICATION_INDEX / 255, value)
    end

    updateCell()

    eventFrame:RegisterEvent("NAME_PLATE_UNIT_ADDED")
    eventFrame:RegisterEvent("NAME_PLATE_UNIT_REMOVED")

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
