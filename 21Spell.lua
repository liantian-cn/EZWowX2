-- 命名空间声明
local addonName, addonTable    = ...

-- WOW API 缓存
local insert                   = table.insert
local random                   = math.random
local CreateFrame              = CreateFrame
local GetSpellCooldownDuration = C_Spell.GetSpellCooldownDuration
local IsSpellOverlayed         = C_SpellActivationOverlay.IsSpellOverlayed
local IsSpellUsable            = C_Spell.IsSpellUsable

-- 插件级变量定义/引用

local Cell                     = addonTable.Cell
addonTable.ClassSpells         = {}

-- 本地变量定义
local SPELL_CLASSIFICATION     = 1
local MARKER_CLASSIFICATION    = 255
local SPELL_ROW                = 1
local SPELL_START_X            = 3
local MARKER_VALUE             = SPELL_CLASSIFICATION
local DEFAULT_VALUE            = 0

local CommonSpells             = {
    [1] = { spellId = 61304, name = "公共冷却" },
}


-- 说明
-- 技能冷却在第一行，2个标记为后开始
-- 每个技能冷却占用4个cell
-- 第一个：remainingCell，表示技能冷却剩余，通过 remaining = GetSpellCooldownDuration(spellID) 获得冷却对象，使用 remaining:EvaluateRemainingDuration(cell.quantizedCurve)获得冷却颜色，最后setCell更新颜色
-- 第二个：usableCell，表示技能是否可用，使用IsSpellUsable(spellID)获取技能是否可用的状态，使用setCellBoolean赋值颜色。
-- 第三个：overlayedCell，表示技能是否高亮，使用IsSpellOverlayed(spellID)获取技能是否高亮的状态，使用setCellBoolean赋值颜色。
-- 第四个：empty1Cell, 占位符，暂时没想到做啥。


-- 开始代码

local function InitSpellFrame()
    Cell:New({ x = 1, y = SPELL_ROW, classification = MARKER_CLASSIFICATION, index = 1, default_value = MARKER_VALUE })
    Cell:New({ x = 2, y = SPELL_ROW, classification = MARKER_CLASSIFICATION, index = 2, default_value = MARKER_VALUE })

    local offsetX = SPELL_START_X -- 从第3列开始放置技能冷却状态
    local offsetIndex = 0         -- index 从零开始。每个cell增1。

    local allSpells = {}
    local spellRecords = {}
    local spellIDToRecords = {}
    local eventFrame = CreateFrame("Frame")

    for _, spell in ipairs(CommonSpells) do
        insert(allSpells, spell)
    end

    for _, spell in ipairs(addonTable.ClassSpells) do
        insert(allSpells, spell)
    end

    local function CreateSpellCell(x, index)
        return Cell:New({
            x = x,
            y = SPELL_ROW,
            classification = SPELL_CLASSIFICATION,
            index = index,
            default_value = DEFAULT_VALUE,
        })
    end

    local function AddSpellRecord(spell, remainingCell, usableCell, overlayedCell, emptyCell)
        local spellID = spell.spellId
        if not spellID then
            return
        end

        local record = {
            spellID = spellID,
            remaining = remainingCell,
            usable = usableCell,
            overlayed = overlayedCell,
            empty = emptyCell,
        }
        local records = spellIDToRecords[spellID]

        if not records then
            records = {}
            spellIDToRecords[spellID] = records
        end

        insert(spellRecords, record)
        insert(records, record)
    end

    for i, spell in ipairs(allSpells) do
        local remainingCell = CreateSpellCell(offsetX, offsetIndex)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1
        local usableCell = CreateSpellCell(offsetX, offsetIndex)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1
        local overlayedCell = CreateSpellCell(offsetX, offsetIndex)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1
        local emptyCell = CreateSpellCell(offsetX, offsetIndex)
        offsetIndex = offsetIndex + 1
        offsetX = offsetX + 1

        AddSpellRecord(spell, remainingCell, usableCell, overlayedCell, emptyCell)
    end

    local function UpdateRecords(records, updateFunc)
        if not records then
            return
        end

        for recordIndex = 1, #records do
            updateFunc(records[recordIndex])
        end
    end

    local function UpdateRemaining(record)
        local remaining = GetSpellCooldownDuration(record.spellID)
        if not remaining then
            record.remaining:clearCell()
            return
        end

        record.remaining:setCell(remaining:EvaluateRemainingDuration(record.remaining.quantizedCurve))
    end

    local function UpdateRemainingAll()
        UpdateRecords(spellRecords, UpdateRemaining)
    end

    local function UpdateUsable(record)
        record.usable:setCellBoolean(IsSpellUsable(record.spellID))
    end

    local function UpdateUsableAll()
        UpdateRecords(spellRecords, UpdateUsable)
    end

    local function UpdateOverlayed(record)
        record.overlayed:setCellBoolean(IsSpellOverlayed(record.spellID))
    end

    local function UpdateOverlayedAll()
        UpdateRecords(spellRecords, UpdateOverlayed)
    end

    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW")
    function eventFrame.SPELL_ACTIVATION_OVERLAY_GLOW_SHOW(spellID)
        UpdateRecords(spellIDToRecords[spellID], UpdateOverlayed)
    end

    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_HIDE")
    function eventFrame.SPELL_ACTIVATION_OVERLAY_GLOW_HIDE(spellID)
        UpdateRecords(spellIDToRecords[spellID], UpdateOverlayed)
    end

    local fastTimeElapsed = -random() -- 0.1 秒刷新可施放状态。
    local lowTimeElapsed = -random()  -- 0.5 秒刷新冷却剩余。
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            UpdateUsableAll()
        end

        lowTimeElapsed = lowTimeElapsed + elapsed
        if lowTimeElapsed > 0.5 then
            lowTimeElapsed = lowTimeElapsed - 0.5
            UpdateRemainingAll()
        end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](...)
    end)

    UpdateRemainingAll()
    UpdateUsableAll()
    UpdateOverlayedAll()
end
insert(addonTable.FrameInitFuncs, InitSpellFrame)
