-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local issecretvalue         = issecretvalue
local UnitExists            = UnitExists
local UnitName              = UnitName

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      玩家施法目标
分类：      玩家属性
分类索引：  21
位置：      1行21列

说明

使用UNIT_SPELLCAST_SENT记录施法目标，未知或secret目标编码为255。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 21
local CELL_POSITION_X = 21
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 255
local FALLBACK_REFRESH_SECONDS = 2
local NO_TARGET_VALUE = 255

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })
    local lastTargetValue = NO_TARGET_VALUE

    local function setTargetValue(value)
        lastTargetValue = value
        cell:setCellRGBA(CELL_CLASSIFICATION / 255, CELL_CLASSIFICATION_INDEX / 255, value / 255)
    end

    local function clearTarget()
        setTargetValue(NO_TARGET_VALUE)
    end

    local function setCastTarget(targetName)
        if issecretvalue(targetName) then
            clearTarget()
            return
        end

        if not targetName then
            clearTarget()
            return
        end

        local playerName = UnitName("player")
        if not issecretvalue(playerName) and playerName and targetName == playerName then
            setTargetValue(0)
            return
        end

        for partyIndex = 1, 4 do
            local unit = "party" .. partyIndex

            if UnitExists(unit) then
                local unitName = UnitName(unit)

                if not issecretvalue(unitName) and unitName and targetName == unitName then
                    setTargetValue(partyIndex)
                    return
                end
            end
        end

        for raidIndex = 1, 40 do
            local unit = "raid" .. raidIndex

            if UnitExists(unit) then
                local unitName = UnitName(unit)

                if not issecretvalue(unitName) and unitName and targetName == unitName then
                    setTargetValue(raidIndex + 5)
                    return
                end
            end
        end

        clearTarget()
    end

    local function clearStaleTargetValue()
        if lastTargetValue ~= NO_TARGET_VALUE then
            clearTarget()
        end
    end

    clearTarget()

    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SENT", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")

    eventFrame:SetScript("OnEvent", function(self, event, unitTarget, targetName)
        if event == "UNIT_SPELLCAST_SENT" then
            setCastTarget(targetName)
            return
        end

        clearTarget()
    end)

    local fallbackElapsed = 0
    eventFrame:SetScript("OnUpdate", function(self, elapsed)
        fallbackElapsed = fallbackElapsed + elapsed

        if fallbackElapsed >= FALLBACK_REFRESH_SECONDS then
            fallbackElapsed = 0
            clearStaleTargetValue()
        end
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
