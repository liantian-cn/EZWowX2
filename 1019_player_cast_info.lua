-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateColor           = CreateColor
local CreateFrame           = CreateFrame
local UnitCastingDuration   = UnitCastingDuration
local UnitCastingInfo       = UnitCastingInfo
local UnitChannelDuration   = UnitChannelDuration
local UnitChannelInfo       = UnitChannelInfo

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell
local IconCell              = addonTable.IconCell

-- 本地变量定义
local insert                = table.insert
local select                = select

-- 代码部分

--[[
简述：      玩家施法信息
分类：      玩家属性
分类索引：  19、20
位置：      1行19列、1行20列、3行1列图标

说明

显示玩家施法或引导进度、蓄力引导状态和当前施法图标。

]]

-- 分类定义
local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS
local PROGRESS_CELL_INDEX = 19
local EMPOWERED_CELL_INDEX = 20
local PROGRESS_CELL_POSITION_X = 19
local EMPOWERED_CELL_POSITION_X = 20
local CELL_POSITION_Y = 1
local ICON_CELL_POSITION_X = 1
local ICON_CELL_POSITION_Y = 3

-- 默认值：cell初始化时的B通道值（0-255）
local DEFAULT_VALUE = 0
local PROGRESS_REFRESH_SECONDS = 0.1
local ICON_BORDER_COLOR = CreateColor(64 / 255, 158 / 255, 210 / 255, 1)
local CAST_MODE_CASTING = "casting"
local CAST_MODE_CHANNELING = "channeling"

local function InitFrame()
    local eventFrame = CreateFrame("Frame") -- 每个文件独立的事件框架
    local progressMode = nil

    local progressCell = Cell:New({
        x = PROGRESS_CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = PROGRESS_CELL_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local empoweredCell = Cell:New({
        x = EMPOWERED_CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = EMPOWERED_CELL_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local iconCell = IconCell:New(ICON_CELL_POSITION_X, ICON_CELL_POSITION_Y)

    local function clearIcon()
        iconCell.Icon:SetTexture(nil)
        iconCell.Icon:Hide()
        iconCell.Border:Hide()
    end

    local function updateProgressCell()
        if progressMode == CAST_MODE_CASTING then
            local duration = UnitCastingDuration("player")

            if duration then
                progressCell:setCell(duration:EvaluateElapsedPercent(progressCell.zeroToOneCurve))
            else
                progressCell:clearCell()
            end
        elseif progressMode == CAST_MODE_CHANNELING then
            local duration = UnitChannelDuration("player")

            if duration then
                progressCell:setCell(duration:EvaluateElapsedPercent(progressCell.zeroToOneCurve))
            else
                progressCell:clearCell()
            end
        else
            progressCell:clearCell()
        end
    end

    local function updateCastState()
        local castingTexture = select(3, UnitCastingInfo("player"))

        if castingTexture then
            progressMode = CAST_MODE_CASTING
            iconCell:SetIcon(castingTexture)
            iconCell:SetBorderColor(ICON_BORDER_COLOR)
            empoweredCell:setCellBoolean(false)
            updateProgressCell()
            return
        end

        local channelTexture = select(3, UnitChannelInfo("player"))

        if channelTexture then
            progressMode = CAST_MODE_CHANNELING
            iconCell:SetIcon(channelTexture)
            iconCell:SetBorderColor(ICON_BORDER_COLOR)
            empoweredCell:setCellBoolean(select(9, UnitChannelInfo("player")))
            updateProgressCell()
            return
        end

        progressMode = nil
        progressCell:clearCell()
        empoweredCell:clearCell()
        clearIcon()
    end

    updateCastState()

    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_DELAYED", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTIBLE", "player")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", "player")

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCastState()
    end)

    local progressElapsed = 0
    eventFrame:HookScript("OnUpdate", function(self, elapsed)
        progressElapsed = progressElapsed + elapsed

        if progressElapsed >= PROGRESS_REFRESH_SECONDS then
            progressElapsed = 0
            updateProgressCell()
        end
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
