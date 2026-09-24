-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateFrame = CreateFrame
local IsSpellKnown = C_SpellBook.IsSpellKnown
local IsSpellInSpellBook = C_SpellBook.IsSpellInSpellBook
local NewTimer = C_Timer.NewTimer

-- 插件级变量定义/引用
local Cell = addonTable.Cell
local PLAYER_STATUS = addonTable.CELL_CLASSIFICATION.PLAYER_STATUS

-- 本地变量定义
local insert = table.insert
local CELL_INDEX = 24
local CELL_POSITION_X = 24
local CELL_POSITION_Y = 1
local REFRESH_DELAY_SECONDS = 0.25
local HERO_TALENT_SPELLS = {
    -- Warrior
    { 436358, 1 },  -- Colossus
    { 444767, 2 },  -- Slayer
    { 434969, 3 },  -- Mountain Thane
    -- Paladin
    { 431377, 1 },  -- Herald of the Sun
    { 432459, 2 },  -- Lightsmith
    { 427445, 3 },  -- Templar
    -- Hunter
    { 466930, 1 },  -- Dark Ranger
    { 466932, 1 },  -- Dark Ranger
    { 471876, 2 },  -- Pack Leader
    { 1253599, 3 }, -- Sentinel
    -- Rogue
    { 457052, 1 },  -- Deathstalker
    { 452536, 2 },  -- Fatebound
    { 441146, 3 },  -- Trickster
    -- Priest
    { 1248423, 1 }, -- Oracle
    { 263165, 2 },  -- Voidweaver
    { 447444, 2 },  -- Voidweaver
    { 120517, 3 },  -- Archon
    { 102644, 3 },  -- Archon
    -- Death Knight
    { 439843, 1 },  -- Deathbringer
    { 433901, 2 },  -- San'layn
    { 444005, 3 },  -- Rider of the Apocalypse
    -- Shaman
    { 443450, 1 },  -- Farseer
    { 454009, 2 },  -- Stormbringer
    { 444995, 3 },  -- Totemic
    { 445024, 3 },  -- Totemic
    -- Mage
    { 443739, 1 },  -- Spellslinger
    { 448601, 2 },  -- Sunfury
    { 431044, 3 },  -- Frostfire
    -- Warlock
    { 445486, 1 },  -- Hellcaller
    { 449614, 2 },  -- Soul Harvester
    { 428514, 3 },  -- Diabolist
    -- Monk
    { 450508, 1 },  -- Master of Harmony
    { 450615, 2 },  -- Shado-Pan
    { 443028, 3 },  -- Conduit of the Celestials
    { 123904, 3 },  -- Conduit of the Celestials
    -- Druid
    { 424058, 1 },  -- Elune's Chosen
    { 433831, 2 },  -- Keeper of the Grove
    { 441583, 3 },  -- Druid of the Claw
    { 439528, 4 },  -- Wildstalker
    -- Demon Hunter
    { 442290, 1 },  -- Aldrachi Reaver
    { 452402, 2 },  -- Fel-Scarred
    { 1253304, 3 }, -- Annihilator
    -- Evoker
    { 1264269, 1 }, -- Flameshaper
    { 436335, 2 },  -- Scalecommander
    { 438587, 2 },  -- Scalecommander
    { 431442, 2 },  -- Chronowarden
}

-- 代码部分

--[[
简述：      玩家英雄天赋
分类：      玩家状态
分类索引：  24
位置：      1行24列

说明

Uses Fuyutsui-compatible representative spells and compact values to encode the active hero talent.
Phantom uses Fuyutsui source declaration order as a deterministic tie-breaker when multiple representative spells match.
]]

local function InitFrame()
    local eventFrame = CreateFrame("Frame")
    local cell = Cell:New({
        x = CELL_POSITION_X,
        y = CELL_POSITION_Y,
        classification = PLAYER_STATUS,
        index = CELL_INDEX,
        default_value = 0,
    })
    local pendingRefreshTimer

    local function updateCell()
        local value = 0

        for i = 1, #HERO_TALENT_SPELLS do
            local heroTalentSpell = HERO_TALENT_SPELLS[i]
            local spellID = heroTalentSpell[1]

            if IsSpellKnown(spellID) or IsSpellInSpellBook(spellID) then
                value = heroTalentSpell[2]
                break
            end
        end

        cell:setCellRGBA(PLAYER_STATUS / 255, CELL_INDEX / 255, value / 255)
    end

    local function requestRefresh()
        if pendingRefreshTimer then
            pendingRefreshTimer:Cancel()
        end

        pendingRefreshTimer = NewTimer(REFRESH_DELAY_SECONDS, function()
            pendingRefreshTimer = nil
            updateCell()
        end)
    end

    eventFrame:RegisterEvent("PLAYER_ENTERING_WORLD")
    eventFrame:RegisterEvent("SPELLS_CHANGED")
    eventFrame:SetScript("OnEvent", requestRefresh)
end

insert(addonTable.FrameInitFuncs, InitFrame)
