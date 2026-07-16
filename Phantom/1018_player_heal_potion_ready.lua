-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local GetItemCooldown       = GetItemCooldown
local IsUsableItem          = IsUsableItem

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      玩家治疗药水可用状态
分类：      玩家属性
分类索引：  18
位置：      1行18列

说明

检测治疗药水物品是否可用。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 18
local CELL_POSITION_X = 18
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2
local ITEM_ID = 258138

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = CELL_CLASSIFICATION_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local function itemUsable(itemID)
        if not itemID then
            return false
        end

        local startTime, duration, enable = GetItemCooldown(itemID)
        local usable, noMana = IsUsableItem(itemID)
        return enable == 1 and duration == 0 and usable and not noMana
    end

    local function updateCell()
        cell:setCellBoolean(itemUsable(ITEM_ID))
    end

    updateCell()

    eventFrame:RegisterEvent("BAG_UPDATE")
    eventFrame:RegisterEvent("BAG_UPDATE_COOLDOWN")
    eventFrame:RegisterEvent("SPELL_UPDATE_COOLDOWN")

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
