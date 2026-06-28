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
local SPELL_ROW                = 1
local SPELL_START_X            = 2
local DEFAULT_VALUE            = 0
local CELLS_PER_SPELL          = 4

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
    local allSpells = {}
    local spellCells = {}
    local eventFrame = CreateFrame("Frame")

    for _, spell in ipairs(CommonSpells) do
        insert(allSpells, spell)
    end

    for _, spell in ipairs(addonTable.ClassSpells) do
        insert(allSpells, spell)
    end

    for i, spell in ipairs(allSpells) do
        local baseX = SPELL_START_X + (i - 1) * CELLS_PER_SPELL
        local baseIndex = baseX - 2
        local remainingCell = Cell:New({
            x = baseX,
            y = SPELL_ROW,
            classification = SPELL_CLASSIFICATION,
            index = baseIndex,
            default_value = DEFAULT_VALUE,
        })
        local usableCell = Cell:New({
            x = baseX + 1,
            y = SPELL_ROW,
            classification = SPELL_CLASSIFICATION,
            index = baseIndex + 1,
            default_value = DEFAULT_VALUE,
        })
        local overlayedCell = Cell:New({
            x = baseX + 2,
            y = SPELL_ROW,
            classification = SPELL_CLASSIFICATION,
            index = baseIndex + 2,
            default_value = DEFAULT_VALUE,
        })
        local emptyCell = Cell:New({
            x = baseX + 3,
            y = SPELL_ROW,
            classification = SPELL_CLASSIFICATION,
            index = baseIndex + 3,
            default_value = DEFAULT_VALUE,
        })

        insert(spellCells, {
            spellId = spell.spellId,
            remainingCell = remainingCell,
            usableCell = usableCell,
            overlayedCell = overlayedCell,
            emptyCell = emptyCell,
        })
    end

    local function UpdateRemainingAll()
        for cellIndex = 1, #spellCells do
            local spellCell = spellCells[cellIndex]
            local remaining = GetSpellCooldownDuration(spellCell.spellId)
            if remaining then
                spellCell.remainingCell:setCell(remaining:EvaluateRemainingDuration(spellCell.remainingCell.quantizedCurve))
            else
                spellCell.remainingCell:clearCell()
            end
        end
    end

    local function UpdateUsableAll()
        for cellIndex = 1, #spellCells do
            local spellCell = spellCells[cellIndex]
            spellCell.usableCell:setCellBoolean(IsSpellUsable(spellCell.spellId))
        end
    end

    local function UpdateOverlayedAll()
        for cellIndex = 1, #spellCells do
            local spellCell = spellCells[cellIndex]
            spellCell.overlayedCell:setCellBoolean(IsSpellOverlayed(spellCell.spellId))
        end
    end

    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW")
    function eventFrame.SPELL_ACTIVATION_OVERLAY_GLOW_SHOW()
        UpdateOverlayedAll()
    end

    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_HIDE")
    function eventFrame.SPELL_ACTIVATION_OVERLAY_GLOW_HIDE()
        UpdateOverlayedAll()
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
