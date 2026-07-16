-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local GetInventoryItemID    = GetInventoryItemID
local GetItemCooldown       = GetItemCooldown
local IsUsableItem          = IsUsableItem

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      玩家饰品可用状态
分类：      玩家属性
分类索引：  15、16
位置：      1行15列、1行16列

说明

分别检测13号和14号装备栏饰品是否可用。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local FIRST_TRINKET_INDEX = 15
local SECOND_TRINKET_INDEX = 16
local FIRST_TRINKET_SLOT = 13
local SECOND_TRINKET_SLOT = 14
local CELL_POSITION_Y = 1

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架

    local firstTrinketCell = Cell:New({
        x = FIRST_TRINKET_INDEX,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = FIRST_TRINKET_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local secondTrinketCell = Cell:New({
        x = SECOND_TRINKET_INDEX,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = SECOND_TRINKET_INDEX,
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
        firstTrinketCell:setCellBoolean(itemUsable(GetInventoryItemID("player", FIRST_TRINKET_SLOT)))
        secondTrinketCell:setCellBoolean(itemUsable(GetInventoryItemID("player", SECOND_TRINKET_SLOT)))
    end

    updateCell()

    eventFrame:RegisterEvent("PLAYER_EQUIPMENT_CHANGED")
    eventFrame:RegisterEvent("BAG_UPDATE_COOLDOWN")
    eventFrame:RegisterEvent("SPELL_UPDATE_COOLDOWN")

    eventFrame:SetScript("OnEvent", function(self, event, equipmentSlot)
        if event == "PLAYER_EQUIPMENT_CHANGED" and equipmentSlot ~= FIRST_TRINKET_SLOT and equipmentSlot ~= SECOND_TRINKET_SLOT then
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
