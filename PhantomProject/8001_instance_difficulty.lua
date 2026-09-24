-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local GetInstanceInfo       = GetInstanceInfo

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      当前副本难度 ID
分类：      环境信息
分类索引：  4
位置：      8行1列

说明

报告当前副本的原始 difficultyID。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.ENVIRONMENT
local CELL_CLASSIFICATION_INDEX = 4
local CELL_POSITION_X = 1
local CELL_POSITION_Y = 8

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
        local _, _, difficultyID = GetInstanceInfo()

        cell:setCellRGBA(
            CELL_CLASSIFICATION / 255,
            CELL_CLASSIFICATION_INDEX / 255,
            difficultyID / 255
        )
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
    eventFrame:RegisterEvent("PLAYER_DIFFICULTY_CHANGED")
    eventFrame:RegisterEvent("UPDATE_INSTANCE_INFO")
    eventFrame:RegisterEvent("INSTANCE_GROUP_SIZE_CHANGED")

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCell()
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
