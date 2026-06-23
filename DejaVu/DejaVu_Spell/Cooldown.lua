local addonName, addonTable         = ...

local pairs                         = pairs
local insert                        = table.insert
local Enum                          = Enum
local random                        = math.random
local tAppendAll                    = tAppendAll
local After                         = C_Timer.After
local wipe                          = wipe

-- WoW 官方 API
local CreateFrame                   = CreateFrame
local GetSpellTexture               = C_Spell.GetSpellTexture
local GetSpellCooldownDuration      = C_Spell.GetSpellCooldownDuration
local IsSpellOverlayed              = C_SpellActivationOverlay.IsSpellOverlayed
local IsSpellUsable                 = C_Spell.IsSpellUsable
local IsSpellInSpellBook            = C_SpellBook.IsSpellInSpellBook
local EvaluateColorFromBoolean      = C_CurveUtil.EvaluateColorFromBoolean
local CreateColorCurve              = C_CurveUtil.CreateColorCurve
local FindBaseSpellByID             = C_SpellBook.FindBaseSpellByID
local GetSpellName                  = C_Spell.GetSpellName
local GetCooldownViewerCategorySet  = C_CooldownViewer.GetCooldownViewerCategorySet
local GetCooldownViewerCooldownInfo = C_CooldownViewer.GetCooldownViewerCooldownInfo
local GetSpellLink                  = C_Spell.GetSpellLink

-- DejaVu Core
local DejaVu                        = _G["DejaVu"]
local cooldownSpells                = {}
DejaVu.cooldownSpells               = cooldownSpells
insert(cooldownSpells, { spellID = 61304, name = "公共冷却" })
local COLOR = DejaVu.COLOR
local Cell = DejaVu.Cell
local BadgeCell = DejaVu.BadgeCell

local remainingCurve = CreateColorCurve()
remainingCurve:SetType(Enum.LuaCurveType.Linear)
remainingCurve:AddPoint(0.0, COLOR.C0)
remainingCurve:AddPoint(5.0, COLOR.C100)
remainingCurve:AddPoint(30.0, COLOR.C150)
remainingCurve:AddPoint(155.0, COLOR.C200)
remainingCurve:AddPoint(375.0, COLOR.C255)

local COOLDOWN_LENGTH = 40
local MartixInitFuncs = DejaVu.MartixInitFuncs



local function InitSpellListByCoolDownViewer()
    local cooldownIDs = GetCooldownViewerCategorySet(Enum.CooldownViewerCategory.Essential, true)
    tAppendAll(cooldownIDs, GetCooldownViewerCategorySet(Enum.CooldownViewerCategory.Utility, true))

    for _, cooldownID in ipairs(cooldownIDs) do
        local cooldownInfo = GetCooldownViewerCooldownInfo(cooldownID)
        if cooldownInfo and (not cooldownInfo.charges) then
            table.insert(cooldownSpells, {
                spellID = cooldownInfo.overrideSpellID,
                name = GetSpellName(cooldownInfo.overrideSpellID),
            })


            print("从冷却管理器添加了CD技能: " .. GetSpellLink(cooldownInfo.overrideSpellID) .. "ID:" .. cooldownInfo.overrideSpellID)
        end
    end
end



local function InitFrame()
    if #cooldownSpells > COOLDOWN_LENGTH then
        print("DejaVu_Spell: Cooldown spells number is greater than COOLDOWN_LENGTH")
        return
    end
    if not DejaVu.useCustomSpell then
        InitSpellListByCoolDownViewer()
    end
    local cellMap = {}
    local validSpellID = {}
    local baseIDToSpellID = {}
    local eventFrame = CreateFrame("Frame")

    local function getValidSpellID(spellID)
        if not spellID or not validSpellID[spellID] then
            return nil
        end
        return spellID
    end

    local function getSpellIDFromBaseID(baseID)
        if not baseID then
            return nil
        end

        local spellID = baseIDToSpellID[baseID]
        if not spellID or not validSpellID[spellID] then
            return nil
        end
        return spellID
    end

    local function InitCellMap()
        for i = 1, #cooldownSpells do
            local spellID = cooldownSpells[i].spellID
            local x = 2 * i
            local y = 0
            local baseID = FindBaseSpellByID(spellID)

            -- x = x, y = y
            -- 用途：技能图标。
            -- 更新函数：updateIcon
            local iconCell = BadgeCell:New(x, y)
            -- x = x, y = y + 2
            -- 用途：显示冷却剩余时间颜色。
            -- 更新函数：updateRemaining
            local remainingCell = Cell:New(x, y + 2)
            -- x = x + 1, y = y + 2
            -- 用途：显示技能高亮提示。
            -- 更新函数：updateOverlayed
            local overlayedCell = Cell:New(x + 1, y + 2)
            -- x = x, y = y + 3
            -- 用途：显示技能是否不可施放。
            -- 更新函数：updateUnusable
            local isUsableCell = Cell:New(x, y + 3)
            -- x = x + 1, y = y + 3
            -- 用途：显示技能是否未学会。
            -- 更新函数：updateUnknown
            local isKnownCell = Cell:New(x + 1, y + 3)
            local iconID = GetSpellTexture(spellID)
            local spellName = GetSpellName(spellID)


            validSpellID[spellID] = true
            if baseID then
                baseIDToSpellID[baseID] = spellID
            end

            iconCell:setCell(iconID, COLOR.SPELL_TYPE.PLAYER_SPELL, spellName)
            cellMap[spellID] = {
                icon = iconCell,
                remaining = remainingCell,
                overlayed = overlayedCell,
                isUsable = isUsableCell,
                isKnown = isKnownCell,
            }
        end
    end

    InitCellMap()

    -- 说明：刷新单个技能图标。
    -- 依赖事件更新：SPELL_UPDATE_ICON。
    -- 依赖定时刷新：2 秒。
    local function updateIcon(spellID)
        local iconID = GetSpellTexture(spellID)
        local spellName = GetSpellName(spellID)
        cellMap[spellID].icon:setCell(iconID, COLOR.SPELL_TYPE.PLAYER_SPELL, spellName)
    end

    -- 说明：刷新全部技能图标。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：2 秒。
    local function updateIconAll()
        for spellID in pairs(cellMap) do
            updateIcon(spellID)
        end
    end

    -- 说明：刷新单个技能冷却剩余时间颜色。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5 秒。
    local function updateRemaining(spellID)
        local remaining = GetSpellCooldownDuration(spellID)
        local result = remaining:EvaluateRemainingDuration(remainingCurve)
        cellMap[spellID].remaining:setCell(result)
    end

    -- 说明：刷新全部技能冷却剩余时间颜色。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5 秒。
    local function updateRemainingAll()
        for spellID in pairs(cellMap) do
            updateRemaining(spellID)
        end
    end

    -- 说明：刷新单个技能高亮提示状态。
    -- 依赖事件更新：SPELL_ACTIVATION_OVERLAY_GLOW_SHOW、SPELL_ACTIVATION_OVERLAY_GLOW_HIDE。
    -- 依赖定时刷新：无。
    local function updateOverlayed(spellID)
        local isOverlayed = EvaluateColorFromBoolean(IsSpellOverlayed(spellID), COLOR.SPELL_BOOLEAN.IS_HIGH_LIGHTED, COLOR.BLACK)
        cellMap[spellID].overlayed:setCell(isOverlayed)
    end

    -- 说明：刷新全部技能高亮提示状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：无。
    local function updateOverlayedAll()
        for spellID in pairs(cellMap) do
            updateOverlayed(spellID)
        end
    end

    -- 说明：刷新单个技能是否可施放状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateUnusable(spellID)
        local isUsable = EvaluateColorFromBoolean(IsSpellUsable(spellID), COLOR.SPELL_BOOLEAN.IS_USABLE, COLOR.BLACK)
        cellMap[spellID].isUsable:setCell(isUsable)
    end

    -- 说明：刷新全部技能是否可施放状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.1 秒。
    local function updateUnusableAll()
        for spellID in pairs(cellMap) do
            updateUnusable(spellID)
        end
    end

    -- 说明：刷新单个技能是否已学会状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5 秒。
    local function updateUnknown(spellID)
        local isKnown = EvaluateColorFromBoolean(IsSpellInSpellBook(spellID), COLOR.SPELL_BOOLEAN.IS_KNOWN, COLOR.BLACK)
        cellMap[spellID].isKnown:setCell(isKnown)
    end

    -- 说明：刷新全部技能是否已学会状态。
    -- 依赖事件更新：无。
    -- 依赖定时刷新：0.5 秒。
    local function updateUnknownAll()
        for spellID in pairs(cellMap) do
            updateUnknown(spellID)
        end
    end

    -- SPELL_UPDATE_ICON
    -- 事件说明：技能图标变化时刷新对应技能图标。
    -- 对应函数：updateIcon
    eventFrame:RegisterEvent("SPELL_UPDATE_ICON")
    function eventFrame.SPELL_UPDATE_ICON(baseID)
        local spellID = getSpellIDFromBaseID(baseID)
        if not spellID then
            return
        end
        updateIcon(spellID)
    end

    -- SPELL_ACTIVATION_OVERLAY_GLOW_SHOW
    -- 事件说明：技能高亮出现时刷新对应技能高亮状态。
    -- 对应函数：updateOverlayed
    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_SHOW")
    function eventFrame.SPELL_ACTIVATION_OVERLAY_GLOW_SHOW(spellID)
        local validID = getValidSpellID(spellID)
        if not validID then
            return
        end
        updateOverlayed(validID)
    end

    -- SPELL_ACTIVATION_OVERLAY_GLOW_HIDE
    -- 事件说明：技能高亮消失时刷新对应技能高亮状态。
    -- 对应函数：updateOverlayed
    eventFrame:RegisterEvent("SPELL_ACTIVATION_OVERLAY_GLOW_HIDE")
    function eventFrame.SPELL_ACTIVATION_OVERLAY_GLOW_HIDE(spellID)
        local validID = getValidSpellID(spellID)
        if not validID then
            return
        end
        updateOverlayed(validID)
    end

    local fastTimeElapsed = -random()     -- 0.1 秒刷新可施放状态。
    local lowTimeElapsed = -random()      -- 0.5 秒刷新已学会状态和冷却剩余。
    local superLowTimeElapsed = -random() -- 2 秒补正技能图标。
    eventFrame:HookScript("OnUpdate", function(_, elapsed)
        fastTimeElapsed = fastTimeElapsed + elapsed
        if fastTimeElapsed > 0.1 then
            fastTimeElapsed = fastTimeElapsed - 0.1
            updateUnusableAll()
        end

        lowTimeElapsed = lowTimeElapsed + elapsed
        if lowTimeElapsed > 0.5 then
            lowTimeElapsed = lowTimeElapsed - 0.5
            updateUnknownAll()
            updateRemainingAll()
            -- updateOverlayedAll() -- 当前保留低频补正占位，未启用。
        end

        superLowTimeElapsed = superLowTimeElapsed + elapsed
        if superLowTimeElapsed > 2 then
            superLowTimeElapsed = superLowTimeElapsed - 2
            updateIconAll()
        end
    end)

    eventFrame:SetScript("OnEvent", function(self, event, ...)
        self[event](...)
    end)

    -- 首次刷新
    updateIconAll()
    updateRemainingAll()
    updateOverlayedAll()
    updateUnusableAll()
    updateUnknownAll()
end
insert(MartixInitFuncs, InitFrame)
