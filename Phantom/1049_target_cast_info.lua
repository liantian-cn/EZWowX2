-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateColor           = CreateColor
local CreateFrame           = CreateFrame
local issecretvalue         = issecretvalue
local UnitCastingDuration   = UnitCastingDuration
local UnitCastingInfo       = UnitCastingInfo
local UnitChannelDuration   = UnitChannelDuration
local UnitChannelInfo       = UnitChannelInfo
local UnitExists            = UnitExists

-- 插件级变量定义/引用
local Cell                  = addonTable.Cell
local IconCell              = addonTable.IconCell

-- 本地变量定义
local insert                = table.insert
local select                = select

-- 代码部分

--[[
简述：      目标施法信息
分类：      目标状态
分类索引：  9、10
位置：      1行49列、1行50列、3行3列图标

说明

显示目标施法或引导进度、可中断状态和当前施法图标。施法纹理、可中断标记和持续时间对象使用secret检查后再显示。

]]

local CELL_CLASSIFICATION = addonTable.CELL_CLASSIFICATION.TARGET_STATUS
local PROGRESS_CELL_INDEX = 9
local INTERRUPTIBLE_CELL_INDEX = 10
local PROGRESS_CELL_POSITION_X = 49
local INTERRUPTIBLE_CELL_POSITION_X = 50
local CELL_POSITION_Y = 1
local ICON_CELL_POSITION_X = 3
local ICON_CELL_POSITION_Y = 3

local DEFAULT_VALUE = 0
local FALLBACK_REFRESH_SECONDS = 2
local PROGRESS_REFRESH_SECONDS = 0.1
local ICON_BORDER_COLOR = CreateColor(64 / 255, 158 / 255, 210 / 255, 1)
local CAST_MODE_CASTING = "casting"
local CAST_MODE_CHANNELING = "channeling"
local UNIT_TOKEN = "target"

local function InitFrame()
    local eventFrame = CreateFrame("Frame")
    local progressMode = nil

    local progressCell = Cell:New({
        x = PROGRESS_CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = PROGRESS_CELL_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local interruptibleCell = Cell:New({
        x = INTERRUPTIBLE_CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = CELL_CLASSIFICATION,
        index = INTERRUPTIBLE_CELL_INDEX,
        default_value = DEFAULT_VALUE,
    })

    local iconCell = IconCell:New(ICON_CELL_POSITION_X, ICON_CELL_POSITION_Y)

    local function clearIcon()
        iconCell.Icon:SetTexture(nil)
        iconCell.Icon:Hide()
        iconCell.Border:Hide()
    end

    local function clearCastState()
        progressMode = nil
        progressCell:clearCell()
        interruptibleCell:clearCell()
        clearIcon()
    end

    local function updateProgressCell()
        if not UnitExists(UNIT_TOKEN) then
            clearCastState()
            return
        end

        if progressMode == CAST_MODE_CASTING then
            local duration = UnitCastingDuration(UNIT_TOKEN)

            if issecretvalue(duration) then
                clearCastState()
                return
            end

            if duration then
                progressCell:setCell(duration:EvaluateElapsedPercent(progressCell.zeroToOneCurve))
            else
                progressCell:clearCell()
            end
        elseif progressMode == CAST_MODE_CHANNELING then
            local duration = UnitChannelDuration(UNIT_TOKEN)

            if issecretvalue(duration) then
                clearCastState()
                return
            end

            if duration then
                progressCell:setCell(duration:EvaluateElapsedPercent(progressCell.zeroToOneCurve))
            else
                progressCell:clearCell()
            end
        else
            progressCell:clearCell()
        end
    end

    local function applyInterruptibleState(notInterruptible)
        if issecretvalue(notInterruptible) then
            clearCastState()
            return false
        end

        interruptibleCell:setCellBoolean(notInterruptible, true)
        return true
    end

    local function updateCastState()
        if not UnitExists(UNIT_TOKEN) then
            clearCastState()
            return
        end

        local castingTexture = select(3, UnitCastingInfo(UNIT_TOKEN))

        if issecretvalue(castingTexture) then
            clearCastState()
            return
        end

        if castingTexture then
            local castNotInterruptible = select(8, UnitCastingInfo(UNIT_TOKEN))

            progressMode = CAST_MODE_CASTING
            iconCell:SetIcon(castingTexture)
            iconCell:SetBorderColor(ICON_BORDER_COLOR)

            if not applyInterruptibleState(castNotInterruptible) then
                return
            end

            updateProgressCell()
            return
        end

        local channelTexture = select(3, UnitChannelInfo(UNIT_TOKEN))

        if issecretvalue(channelTexture) then
            clearCastState()
            return
        end

        if channelTexture then
            local channelNotInterruptible = select(7, UnitChannelInfo(UNIT_TOKEN))
            local isEmpowered = select(9, UnitChannelInfo(UNIT_TOKEN))

            if issecretvalue(isEmpowered) then
                clearCastState()
                return
            end

            progressMode = CAST_MODE_CHANNELING
            iconCell:SetIcon(channelTexture)
            iconCell:SetBorderColor(ICON_BORDER_COLOR)

            if not applyInterruptibleState(channelNotInterruptible) then
                return
            end

            updateProgressCell()
            return
        end

        clearCastState()
    end

    updateCastState()

    eventFrame:RegisterEvent("PLAYER_TARGET_CHANGED")
    eventFrame:RegisterEvent("UNIT_TARGETABLE_CHANGED")
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_START", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_STOP", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTED", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_FAILED_QUIET", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_DELAYED", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_SUCCEEDED", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_START", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_STOP", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_CHANNEL_UPDATE", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_START", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_EMPOWER_STOP", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_INTERRUPTIBLE", UNIT_TOKEN)
    eventFrame:RegisterUnitEvent("UNIT_SPELLCAST_NOT_INTERRUPTIBLE", UNIT_TOKEN)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        updateCastState()
    end)

    local fallbackElapsed = 0
    local progressElapsed = 0
    eventFrame:SetScript("OnUpdate", function(self, elapsed)
        fallbackElapsed = fallbackElapsed + elapsed

        if fallbackElapsed >= FALLBACK_REFRESH_SECONDS then
            fallbackElapsed = 0
            updateCastState()
        end

        if progressMode then
            progressElapsed = progressElapsed + elapsed

            if progressElapsed >= PROGRESS_REFRESH_SECONDS then
                progressElapsed = 0
                updateProgressCell()
            end
        else
            progressElapsed = 0
        end
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
