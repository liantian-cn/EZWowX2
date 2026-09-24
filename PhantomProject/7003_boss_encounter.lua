-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell
local Config                = addonTable.Config
local logging               = addonTable.logging

-- 本地变量定义
local insert                = table.insert
local tostring              = tostring

-- 代码部分

--[[
简述：      当前首领战的 Fuyutsui 兼容紧凑编码
分类：      环境信息
分类索引：  3
位置：      7行3列

说明

已知首领战写入对应紧凑编码。未处于首领战、未知首领 ID 或首领战结束时写入 0。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.ENVIRONMENT
local CELL_CLASSIFICATION_INDEX = 3
local CELL_POSITION_X = 3
local CELL_POSITION_Y = 7

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0

-- Fuyutsui 兼容的 encounterID 到紧凑编码映射
local BOSS_ENCOUNTER_CODES = {
    -- 团本
    [3176] = 1,
    [3177] = 2,
    [3179] = 3,
    [3178] = 4,
    [3180] = 5,
    [3181] = 6,
    [3306] = 7,
    [3182] = 8,
    [3183] = 9,
    [3454] = 10,
    [3459] = 11,
    [3431] = 12,
    [3436] = 13,
    -- 大米
    [3328] = 51,
    [3332] = 52,
    [3333] = 53,
    [3212] = 54,
    [3213] = 55,
    [3214] = 56,
    [3056] = 57,
    [3057] = 58,
    [3058] = 59,
    [3059] = 60,
    [3071] = 61,
    [3072] = 62,
    [3073] = 63,
    [3074] = 64,
    [2065] = 65,
    [2066] = 66,
    [2067] = 67,
    [2068] = 68,
    [2562] = 69,
    [2563] = 70,
    [2564] = 71,
    [2565] = 72,
    [1999] = 73,
    [2001] = 74,
    [2000] = 75,
    [1698] = 76,
    [1699] = 77,
    [1700] = 78,
    [1701] = 79,
}

local unknownEncounterDiagnostic = Config("boss_encounter_unknown_id_diagnostic")
unknownEncounterDiagnostic:set_default(true)

local loggedUnknownEncounterIDs = {}

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local function updateCell(value)
        cell:setCellRGBA(
            CELL_CLASSIFICATION / 255,
            CELL_CLASSIFICATION_INDEX / 255,
            value / 255
        )
    end

    updateCell(DEFAULT_VALUE)

    eventFrame:RegisterEvent("ENCOUNTER_START")
    eventFrame:RegisterEvent("ENCOUNTER_END")

    eventFrame:SetScript("OnEvent", function(_, event, encounterID)
        if event == "ENCOUNTER_START" then
            local value = BOSS_ENCOUNTER_CODES[encounterID] or 0

            if encounterID and encounterID ~= 0 and value == 0
                and unknownEncounterDiagnostic:get_value()
                and not loggedUnknownEncounterIDs[encounterID] then
                loggedUnknownEncounterIDs[encounterID] = true
                logging(" Unknown boss encounter ID: " .. tostring(encounterID))
            end

            updateCell(value)
        elseif event == "ENCOUNTER_END" then
            updateCell(0)
        end
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
