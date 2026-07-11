-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local After = C_Timer.After
local CreateNumericRuleFormatter = C_StringUtil.CreateNumericRuleFormatter
local CreateFrame = CreateFrame
local Immediate = Enum.StatusBarInterpolation.Immediate
local RemainingTime = Enum.StatusBarTimerDirection.RemainingTime
local UIParent = UIParent

-- 插件级变量定义/引用
local GetUIScaleFactor = addonTable.GetUIScaleFactor

-- 本地变量定义
local AURA_BUTTON_BORDER_STYLE_COLOR = 1
local AURA_BUTTON_WIDTH = 36
local AURA_BUTTON_HEIGHT = 48
local ICON_SIZE = 24
local COUNT_SIZE = 24
local DURATION_BAR_WIDTH = 12
local DURATION_BAR_HEIGHT = 48
local COUNT_FONT_SIZE = 18
local FILTER_STRING = "PLAYER|HELPFUL"
local PIX_NUM_FONT = "Interface\\AddOns\\" .. addonName .. "\\media\\PixNum.ttf"
local AURA_BORDER_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga"
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local PLAYER_BUFF_SLOTS = {
    { key = "mark_of_the_wild", spellIDs = { [1126] = true, [1128] = true } },
    { key = "germination", spellIDs = { [155777] = true } },
    { key = "rejuvenation", spellIDs = { [774] = true, [778] = true } },
    { key = "regrowth", spellIDs = { [8936] = true, [8938] = true } },
    { key = "wild_growth", spellIDs = { [48438] = true } },
    { key = "lifebloom", spellIDs = { [33763] = true } },
    { key = "omen_of_clarity", spellIDs = { [16870] = true } },
}
local APPLICATION_COUNT_FORMATTER = CreateNumericRuleFormatter()

APPLICATION_COUNT_FORMATTER:SetBreakpoints({
    { threshold = 0, format = "" },
    { threshold = 1, format = "%d" },
    { threshold = 10, format = "*" },
})

-- 代码部分
local function GetDemoSize(size)
    return GetUIScaleFactor(size)
end

local function InitializeAuraButton(auraButton)
    auraButton:SetSize(GetDemoSize(AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))

    auraButton.Icon = auraButton:CreateTexture(nil, "BACKGROUND")
    auraButton.Icon:SetSize(GetDemoSize(ICON_SIZE), GetDemoSize(ICON_SIZE))
    auraButton.Icon:SetPoint("TOPLEFT", auraButton, "TOPLEFT", 0, 0)
    auraButton:SetIcon(auraButton.Icon)

    auraButton.AuraBorder = auraButton:CreateTexture(nil, "OVERLAY")
    auraButton.AuraBorder:SetTexture(AURA_BORDER_TEXTURE)
    auraButton.AuraBorder:SetAllPoints(auraButton.Icon)
    auraButton:SetAuraBorder(auraButton.AuraBorder, {
        showWhenHarmful = false,
        showWhenHelpful = true,
        style = AURA_BUTTON_BORDER_STYLE_COLOR,
    })

    auraButton.Count = auraButton:CreateFontString(nil, "OVERLAY")
    auraButton.Count:SetSize(GetDemoSize(COUNT_SIZE), GetDemoSize(COUNT_SIZE))
    auraButton.Count:SetPoint("BOTTOMLEFT", auraButton, "BOTTOMLEFT", 0, 0)
    auraButton.Count:SetFont(PIX_NUM_FONT, GetDemoSize(COUNT_FONT_SIZE), "MONOCHROME")
    auraButton.Count:SetJustifyH("CENTER")
    auraButton.Count:SetJustifyV("MIDDLE")
    auraButton:SetApplicationCount(auraButton.Count, { formatter = APPLICATION_COUNT_FORMATTER })

    auraButton.DurationBar = CreateFrame("StatusBar", nil, auraButton)
    auraButton.DurationBar:SetSize(GetDemoSize(DURATION_BAR_WIDTH), GetDemoSize(DURATION_BAR_HEIGHT))
    auraButton.DurationBar:SetPoint("TOPRIGHT", auraButton, "TOPRIGHT", 0, 0)
    auraButton.DurationBar:SetOrientation("VERTICAL")
    auraButton.DurationBar:SetStatusBarTexture(WHITE_TEXTURE)
    auraButton.DurationBar:SetStatusBarColor(1, 1, 1, 1)

    auraButton.DurationBar.Background = auraButton.DurationBar:CreateTexture(nil, "BACKGROUND")
    auraButton.DurationBar.Background:SetAllPoints(auraButton.DurationBar)
    auraButton.DurationBar.Background:SetColorTexture(0, 0, 0, 1)

    auraButton:SetDurationBar(auraButton.DurationBar, {
        interpolation = Immediate,
        direction = RemainingTime,
    })
end

local function CreateDemoFrame()
    local frame = CreateFrame("Frame", addonName .. "AuraSlotDemoFrame", UIParent)
    frame:SetPoint("CENTER", UIParent, "CENTER", 0, 0)
    frame:SetSize(
        GetDemoSize(#PLAYER_BUFF_SLOTS * AURA_BUTTON_WIDTH),
        GetDemoSize(AURA_BUTTON_HEIGHT)
    )
    frame:SetFrameStrata("HIGH")
    frame:SetFrameLevel(100)

    frame.Background = frame:CreateTexture(nil, "BACKGROUND")
    frame.Background:SetAllPoints(frame)
    frame.Background:SetColorTexture(0, 0, 0, 0.65)

    local container = CreateFrame("AuraContainer", nil, frame, "CustomAuraContainerTemplate")
    container:SetPoint("TOPLEFT", frame, "TOPLEFT", 0, 0)
    container:SetUnit("player")

    for slotIndex, slotInfo in ipairs(PLAYER_BUFF_SLOTS) do
        local auraButton = container:AddAuraSlot(slotInfo.key, FILTER_STRING, {
            candidateFilters = {
                includeSpellIDs = slotInfo.spellIDs,
            },
            initializeFrame = InitializeAuraButton,
        })
        auraButton:SetPoint(
            "TOPLEFT",
            frame,
            "TOPLEFT",
            GetDemoSize((slotIndex - 1) * AURA_BUTTON_WIDTH),
            0
        )
    end
end

After(0, CreateDemoFrame)
