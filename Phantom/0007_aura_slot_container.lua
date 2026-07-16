-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local CreateNumericRuleFormatter = C_StringUtil.CreateNumericRuleFormatter
local CreateFrame = CreateFrame
local Immediate = Enum.StatusBarInterpolation.Immediate
local RemainingTime = Enum.StatusBarTimerDirection.RemainingTime

-- 插件级变量定义/引用

-- 本地变量定义
local AURA_BUTTON_BORDER_STYLE_COLOR = 1
local SLOT_KEY_PREFIX = "slot_"
local PIX_NUM_FONT = "Interface\\AddOns\\" .. addonName .. "\\media\\PixNum.ttf"
local AURA_BORDER_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga"
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local APPLICATION_COUNT_FORMATTER = CreateNumericRuleFormatter()

APPLICATION_COUNT_FORMATTER:SetBreakpoints({
    { threshold = 0, format = "" },
    { threshold = 1, format = "%d" },
    { threshold = 10, format = "*" },
})

-- 代码部分
local function CreateSpellIDMap(spellIDs)
    local includeSpellIDs = {}

    for _, spellID in ipairs(spellIDs) do
        includeSpellIDs[spellID] = true
    end

    return includeSpellIDs
end

local function InitializeAuraButton(auraButton, SIZE, classification, slotIndex)
    local r = classification / 255
    local g = slotIndex / 255

    auraButton:SetSize(3 * SIZE.CELL, 4 * SIZE.CELL)

    auraButton.Icon = auraButton:CreateTexture(nil, "BACKGROUND")
    auraButton.Icon:SetSize(2 * SIZE.CELL, 2 * SIZE.CELL)
    auraButton.Icon:SetPoint("TOPLEFT", auraButton, "TOPLEFT", 0, 0)
    auraButton:SetIcon(auraButton.Icon)

    auraButton.AuraBorder = auraButton:CreateTexture(nil, "OVERLAY")
    auraButton.AuraBorder:SetTexture(AURA_BORDER_TEXTURE)
    auraButton.AuraBorder:SetAllPoints(auraButton.Icon)
    auraButton:SetAuraBorder(auraButton.AuraBorder, {
        showWhenHarmful = true,
        showWhenHelpful = true,
        style = AURA_BUTTON_BORDER_STYLE_COLOR,
    })

    auraButton.Count = auraButton:CreateFontString(nil, "OVERLAY")
    auraButton.Count:SetSize(2 * SIZE.CELL, 2 * SIZE.CELL)
    auraButton.Count:SetPoint("BOTTOMLEFT", auraButton, "BOTTOMLEFT", 0, 0)
    auraButton.Count:SetFont(PIX_NUM_FONT, SIZE.FONT, "MONOCHROME")
    auraButton.Count:SetTextColor(r, g, 1, 1)
    auraButton.Count:SetJustifyH("CENTER")
    auraButton.Count:SetJustifyV("MIDDLE")
    auraButton:SetApplicationCount(auraButton.Count, { formatter = APPLICATION_COUNT_FORMATTER })

    auraButton.DurationBar = CreateFrame("StatusBar", nil, auraButton)
    auraButton.DurationBar:SetSize(SIZE.CELL, 4 * SIZE.CELL)
    auraButton.DurationBar:SetPoint("TOPRIGHT", auraButton, "TOPRIGHT", 0, 0)
    auraButton.DurationBar:SetOrientation("VERTICAL")
    auraButton.DurationBar:SetStatusBarTexture(WHITE_TEXTURE)
    auraButton.DurationBar:SetStatusBarColor(r, g, 1, 1)

    auraButton.DurationBar.Background = auraButton.DurationBar:CreateTexture(nil, "BACKGROUND")
    auraButton.DurationBar.Background:SetAllPoints(auraButton.DurationBar)
    auraButton.DurationBar.Background:SetColorTexture(r, g, 0, 1)

    auraButton:SetDurationBar(auraButton.DurationBar, {
        interpolation = Immediate,
        direction = RemainingTime,
    })
end

function addonTable.CreateAuraSlotContainer(options)
    local SIZE = addonTable.SIZE
    local parent = addonTable.MartixFrame
    local container = CreateFrame("AuraContainer", nil, parent, "CustomAuraContainerTemplate")

    container:SetPoint("TOPLEFT", parent, "TOPLEFT", options.x * SIZE.CELL, -(options.y - 1) * SIZE.CELL)
    container:SetUnit(options.unitToken)

    for slotIndex, slotInfo in ipairs(options.slots) do
        local index = slotIndex
        local auraButton = container:AddAuraSlot(SLOT_KEY_PREFIX .. index, options.filterString, {
            candidateFilters = {
                includeSpellIDs = CreateSpellIDMap(slotInfo.spellIDs),
            },
            initializeFrame = function(frame)
                InitializeAuraButton(frame, SIZE, options.classification, index)
            end,
        })
        auraButton:SetPoint("TOPLEFT", container, "TOPLEFT", (index - 1) * 3 * SIZE.CELL, 0)
    end

    return container
end
