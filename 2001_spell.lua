-- Namespace declaration
local addonName, addonTable = ...

-- WoW API cache
local CreateColor              = CreateColor
local CreateFrame              = CreateFrame
local CreateColorCurve         = C_CurveUtil.CreateColorCurve
local GetSpellCooldownDuration = C_Spell.GetSpellCooldownDuration
local IsSpellOverlayed         = C_SpellActivationOverlay.IsSpellOverlayed
local IsSpellUsable            = C_Spell.IsSpellUsable
local Linear                   = Enum.LuaCurveType.Linear

-- Addon-level variable definitions/references
local Cell                     = addonTable.Cell
local CELL_CLASSIFICATION      = addonTable.CELL_CLASSIFICATION

-- Local variables
local insert                   = table.insert
local type                     = type

local COOLDOWN_CLASSIFICATION  = CELL_CLASSIFICATION.SPELL_COOLDOWN
local USABLE_CLASSIFICATION    = CELL_CLASSIFICATION.SPELL_USABLE
local OVERLAYED_CLASSIFICATION = CELL_CLASSIFICATION.SPELL_OVERLAYED
local CELL_POSITION_Y          = 2
local DEFAULT_VALUE            = 0
local MAX_SPELL_SLOTS          = 26
local USABLE_REFRESH_SECONDS   = 0.1
local COOLDOWN_REFRESH_SECONDS = 0.5

-- Code

--[[
Summary:               Configured specialization spell status
Classifications:       Spell cooldown, usability, and activation overlay
Classification index:  SpellList slot 1-26
Position:              Row 2, three consecutive Cells per slot

Each valid configured slot keeps its original one-based index. Missing or invalid
slots create no Cells, so their matrix area remains black.
]]

local function InitFrame()
    local spellList = addonTable.SPEC and addonTable.SPEC.SpellList
    if type(spellList) ~= "table" then
        return
    end

    local spellCells = {}

    for index = 1, MAX_SPELL_SLOTS do
        local spell = spellList[index]
        local spellID = type(spell) == "table" and spell.spellId or nil

        if type(spellID) == "number" and spellID > 0 and spellID % 1 == 0 then
            local baseX = 3 * index - 2
            local cooldownCell = Cell:New({
                x = baseX,
                y = CELL_POSITION_Y,
                classification = COOLDOWN_CLASSIFICATION,
                index = index,
                default_value = DEFAULT_VALUE,
            })
            local usableCell = Cell:New({
                x = baseX + 1,
                y = CELL_POSITION_Y,
                classification = USABLE_CLASSIFICATION,
                index = index,
                default_value = DEFAULT_VALUE,
            })
            local overlayedCell = Cell:New({
                x = baseX + 2,
                y = CELL_POSITION_Y,
                classification = OVERLAYED_CLASSIFICATION,
                index = index,
                default_value = DEFAULT_VALUE,
            })

            local cooldownCurve = CreateColorCurve()
            cooldownCurve:SetType(Linear)
            cooldownCurve:AddPoint(0.0, CreateColor(COOLDOWN_CLASSIFICATION / 255, index / 255, 0, 1))
            cooldownCurve:AddPoint(5.0, CreateColor(COOLDOWN_CLASSIFICATION / 255, index / 255, 100 / 255, 1))
            cooldownCurve:AddPoint(30.0, CreateColor(COOLDOWN_CLASSIFICATION / 255, index / 255, 150 / 255, 1))
            cooldownCurve:AddPoint(155.0, CreateColor(COOLDOWN_CLASSIFICATION / 255, index / 255, 200 / 255, 1))
            cooldownCurve:AddPoint(375.0, CreateColor(COOLDOWN_CLASSIFICATION / 255, index / 255, 255 / 255, 1))

            insert(spellCells, {
                spellID = spellID,
                cooldownCell = cooldownCell,
                usableCell = usableCell,
                overlayedCell = overlayedCell,
                cooldownCurve = cooldownCurve,
            })
        end
    end

    if #spellCells == 0 then
        return
    end

    local function updateCooldown(spellCell)
        local duration = GetSpellCooldownDuration(spellCell.spellID)

        if duration then
            spellCell.cooldownCell:setCell(duration:EvaluateRemainingDuration(spellCell.cooldownCurve))
        else
            spellCell.cooldownCell:clearCell()
        end
    end

    local function updateCooldownAll()
        for cellIndex = 1, #spellCells do
            updateCooldown(spellCells[cellIndex])
        end
    end

    local function updateUsableAll()
        for cellIndex = 1, #spellCells do
            local spellCell = spellCells[cellIndex]
            local isUsable = IsSpellUsable(spellCell.spellID)
            spellCell.usableCell:setCellBoolean(isUsable)
        end
    end

    local function updateOverlayed(spellCell)
        spellCell.overlayedCell:setCellBoolean(IsSpellOverlayed(spellCell.spellID))
    end

    local function updateOverlayedAll()
        for cellIndex = 1, #spellCells do
            updateOverlayed(spellCells[cellIndex])
        end
    end

    local function updateMatchingOverlayed(spellID)
        for cellIndex = 1, #spellCells do
            local spellCell = spellCells[cellIndex]

            if spellCell.spellID == spellID then
                updateOverlayed(spellCell)
            end
        end
    end

    updateCooldownAll()
    updateUsableAll()
    updateOverlayedAll()

    local eventFrame = CreateFrame("Frame")
    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW")
    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_HIDE")
    eventFrame:SetScript("OnEvent", function(self, event, spellID)
        updateMatchingOverlayed(spellID)
    end)

    local usableElapsed = 0
    local cooldownElapsed = 0
    eventFrame:SetScript("OnUpdate", function(self, elapsed)
        usableElapsed = usableElapsed + elapsed
        if usableElapsed >= USABLE_REFRESH_SECONDS then
            usableElapsed = 0
            updateUsableAll()
        end

        cooldownElapsed = cooldownElapsed + elapsed
        if cooldownElapsed >= COOLDOWN_REFRESH_SECONDS then
            cooldownElapsed = 0
            updateCooldownAll()
        end
    end)
end

insert(addonTable.FrameInitFuncs, InitFrame)
