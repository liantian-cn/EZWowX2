-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local GetSpecialization     = C_SpecializationInfo.GetSpecialization

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      玩家专精
分类：      玩家属性
分类索引：  3
位置：      1行3列

说明

使用C_SpecializationInfo.GetSpecialization读取当前专精序号，并编码为specializationIndex * 10。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 3
local CELL_POSITION_X = 3
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
        local value = 0
        local specializationIndex = GetSpecialization()

        if specializationIndex then
            value = specializationIndex * 10
        end

        cell:setCellRGBA(CELL_CLASSIFICATION / 255, CELL_CLASSIFICATION_INDEX / 255, value / 255)
    end

    updateCell()

    eventFrame:RegisterEvent("ACTIVE_PLAYER_SPECIALIZATION_CHANGED")
    eventFrame:RegisterEvent("PLAYER_SPECIALIZATION_CHANGED")

    eventFrame:SetScript("OnEvent", function(self, event, unitTarget)
        if event == "PLAYER_SPECIALIZATION_CHANGED" and unitTarget ~= "player" then
            return
        end

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
