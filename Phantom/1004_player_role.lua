-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local UnitGroupRolesAssigned = UnitGroupRolesAssigned

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      玩家职责
分类：      玩家属性
分类索引：  4
位置：      1行4列

说明

使用UnitGroupRolesAssigned读取玩家职责，并映射为TANK=10、HEALER=20、DAMAGER=30、NONE=0。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 4
local CELL_POSITION_X = 4
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local function updateCell()
        local role = UnitGroupRolesAssigned("player")
        local value = 0

        if role == "TANK" then
            value = 10
        elseif role == "HEALER" then
            value = 20
        elseif role == "DAMAGER" then
            value = 30
        end

        cell:setCellRGBA(CELL_CLASSIFICATION / 255, CELL_CLASSIFICATION_INDEX / 255, value / 255)
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_ROLES_ASSIGNED")
    eventFrame:RegisterEvent("ROLE_CHANGED_INFORM")
    eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")

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
