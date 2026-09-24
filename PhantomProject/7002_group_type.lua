-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local UnitInParty           = UnitInParty
local UnitInRaid            = UnitInRaid

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      当前队伍类型
分类：      环境信息
分类索引：  2
位置：      7行2列

说明

报告 Fuyutsui 兼容的当前队伍类型：团队为玩家的团队索引，队伍为 46，单人为 0。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.ENVIRONMENT
local CELL_CLASSIFICATION_INDEX = 2
local CELL_POSITION_X = 2
local CELL_POSITION_Y = 7

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0

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
        local raidIndex = UnitInRaid("player")
        local value

        if raidIndex then
            value = raidIndex
        elseif UnitInParty("player") then
            value = 46
        else
            value = 0
        end

        cell:setCellRGBA(
            CELL_CLASSIFICATION / 255,
            CELL_CLASSIFICATION_INDEX / 255,
            value / 255
        )
    end

    updateCell()

    eventFrame:RegisterEvent("GROUP_ROSTER_UPDATE")
    eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCell()
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
