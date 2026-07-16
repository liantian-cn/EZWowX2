-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame           = CreateFrame
local EventRegistry         = EventRegistry
local GetCurrentKeyBoardFocus = GetCurrentKeyBoardFocus

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell

-- 本地变量定义
local insert                = table.insert

-- 代码部分

--[[
简述：      玩家正在聊天输入
分类：      玩家属性
分类索引：  13
位置：      1行13列

说明

使用GetCurrentKeyBoardFocus检测当前是否有键盘输入焦点。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local CELL_CLASSIFICATION_INDEX = 13
local CELL_POSITION_X = 13
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
        cell:setCellBoolean(GetCurrentKeyBoardFocus() ~= nil)
    end

    updateCell()

    if EventRegistry then
        EventRegistry:RegisterCallback("ChatFrame.OnEditBoxFocusGained", updateCell, eventFrame)
        EventRegistry:RegisterCallback("ChatFrame.OnEditBoxFocusLost", updateCell, eventFrame)
        EventRegistry:RegisterCallback("ChatFrame.OnEditBoxShow", updateCell, eventFrame)
        EventRegistry:RegisterCallback("ChatFrame.OnEditBoxHide", updateCell, eventFrame)
    end

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
