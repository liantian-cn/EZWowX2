-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local After = C_Timer.After
local CreateFrame = CreateFrame
local Immediate = Enum.StatusBarInterpolation.Immediate
local RemainingTime = Enum.StatusBarTimerDirection.RemainingTime
local UIParent = UIParent

-- 插件级变量定义/引用
local GetUIScaleFactor = addonTable.GetUIScaleFactor

-- 本地变量定义
local MAX_BUFFS = 12
local AURA_BUTTON_BORDER_STYLE_COLOR = 1
local SIZE = {
    NODE_SIZE = 4,
}

local SCALE = 4

SIZE.CELL_SIZE = SIZE.NODE_SIZE
SIZE.PIXEL_SIZE = SIZE.NODE_SIZE

local AURA_BUTTON_WIDTH = 5 * SIZE.NODE_SIZE
local AURA_BUTTON_HEIGHT = 8 * SIZE.NODE_SIZE
local ICON_SIZE = 4 * SIZE.NODE_SIZE
local COUNT_SIZE = 4 * SIZE.NODE_SIZE
local DURATION_BAR_WIDTH = SIZE.NODE_SIZE
local DURATION_BAR_HEIGHT = 8 * SIZE.NODE_SIZE
local COUNT_FONT_SIZE = 6
local PIX_NUM_FONT = "Interface\\AddOns\\" .. addonName .. "\\media\\PixNum.ttf"
local DEBUFF_BORDER_TEXTURE = "Interface\\Buttons\\UI-Debuff-Overlays"
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local ROW_GAP = SIZE.NODE_SIZE

-- 代码部分
local function GetDemoSize(size)
    return GetUIScaleFactor(size * SCALE)
end

local function CreateAuraButton(parent, auraIndex, auraBorderOptions)
    local auraButton = CreateFrame("AuraButton", nil, parent, "CustomAuraButtonTemplate")
    auraButton:SetSize(GetDemoSize(AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))
    auraButton:SetPoint("TOPLEFT", parent, "TOPLEFT", GetDemoSize((auraIndex - 1) * AURA_BUTTON_WIDTH), 0)

    auraButton.Icon = auraButton:CreateTexture(nil, "BACKGROUND")
    auraButton.Icon:SetSize(GetDemoSize(ICON_SIZE), GetDemoSize(ICON_SIZE))
    auraButton.Icon:SetPoint("TOPLEFT", auraButton, "TOPLEFT", 0, 0)
    auraButton:SetIcon(auraButton.Icon)

    if auraBorderOptions then
        auraButton.AuraBorder = auraButton:CreateTexture(nil, "OVERLAY")
        auraButton.AuraBorder:SetTexture(DEBUFF_BORDER_TEXTURE)
        auraButton.AuraBorder:SetTexCoord(0.296875, 0.5703125, 0, 0.515625)
        auraButton.AuraBorder:SetAllPoints(auraButton.Icon)
        auraButton:SetAuraBorder(auraButton.AuraBorder, auraBorderOptions)
    end

    auraButton.DurationBar = CreateFrame("StatusBar", nil, auraButton)
    auraButton.DurationBar:SetSize(GetDemoSize(DURATION_BAR_WIDTH), GetDemoSize(DURATION_BAR_HEIGHT))
    auraButton.DurationBar:SetPoint("TOPRIGHT", auraButton, "TOPRIGHT", 0, 0)
    auraButton.DurationBar:SetOrientation("VERTICAL")
    auraButton.DurationBar:SetStatusBarTexture(WHITE_TEXTURE)
    auraButton.DurationBar:SetStatusBarColor(1, 1, 1, 1)

    auraButton.DurationBar.Background = auraButton.DurationBar:CreateTexture(nil, "BACKGROUND")
    auraButton.DurationBar.Background:SetAllPoints(auraButton.DurationBar)
    auraButton.DurationBar.Background:SetColorTexture(0, 0, 0, 1)

    auraButton:SetDurationBar(auraButton.DurationBar, { interpolation = Immediate, direction = RemainingTime })

    auraButton.Count = auraButton:CreateFontString(nil, "OVERLAY")
    auraButton.Count:SetSize(GetDemoSize(COUNT_SIZE), GetDemoSize(COUNT_SIZE))
    auraButton.Count:SetPoint("BOTTOMLEFT", auraButton, "BOTTOMLEFT", 0, 0)
    auraButton.Count:SetFont(PIX_NUM_FONT, GetDemoSize(COUNT_FONT_SIZE), "")
    auraButton.Count:SetJustifyH("CENTER")
    auraButton.Count:SetJustifyV("MIDDLE")
    auraButton:SetApplicationCount(auraButton.Count, {})

    parent:AddAuraFrame(auraButton)
end

local function CreateAuraRow(parent, filterString, yOffset, auraBorderOptions)
    local container = CreateFrame("AuraContainer", nil, parent, "CustomAuraContainerTemplate")
    container:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -GetDemoSize(yOffset))
    container:SetSize(GetDemoSize(MAX_BUFFS * AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))
    container:SetUnit("player")
    container:AddAuraFilter(filterString, { maxFrameCount = MAX_BUFFS })

    for auraIndex = 1, MAX_BUFFS do
        CreateAuraButton(container, auraIndex, auraBorderOptions)
    end

    return container
end

local function CreateDemoFrame()
    local frame = CreateFrame("Frame", addonName .. "DemoAuraFrame", UIParent)
    frame:SetPoint("CENTER", UIParent, "CENTER", 0, 0)
    frame:SetSize(
        GetDemoSize(MAX_BUFFS * AURA_BUTTON_WIDTH),
        GetDemoSize((AURA_BUTTON_HEIGHT * 2) + ROW_GAP)
    )
    frame:SetFrameStrata("HIGH")
    frame:SetFrameLevel(100)
    frame:Show()

    frame.bg = frame:CreateTexture(nil, "BACKGROUND")
    frame.bg:SetAllPoints(frame)
    frame.bg:SetColorTexture(0, 0, 0, 0.65)

    CreateAuraRow(frame, "HELPFUL", 0, {
        showWhenHarmful = false,
        showWhenHelpful = true,
        style = AURA_BUTTON_BORDER_STYLE_COLOR,
    })
    CreateAuraRow(frame, "HARMFUL", AURA_BUTTON_HEIGHT + ROW_GAP, {
        showWhenHarmful = true,
        showWhenHelpful = false,
        style = AURA_BUTTON_BORDER_STYLE_COLOR,
    })
end

After(0, CreateDemoFrame)
