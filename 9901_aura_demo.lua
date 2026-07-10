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
local MAX_BUFFS = 12
local AURA_BUTTON_BORDER_STYLE_COLOR = 1
local SIZE = {
    NODE_SIZE = 4,
}

local SCALE = 1

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
local AURA_BORDER_TEXTURE = "Interface\\AddOns\\" .. addonName .. "\\media\\aura\\aura_border_32_4px.tga"
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"
local ROW_GAP = SIZE.NODE_SIZE
local APPLICATION_COUNT_FORMATTER = CreateNumericRuleFormatter()

APPLICATION_COUNT_FORMATTER:SetBreakpoints({
    { threshold = 0, format = "" },
    { threshold = 1, format = "%d" },
    { threshold = 10, format = "*" },
})

-- 代码部分
local function GetDemoSize(size)
    return GetUIScaleFactor(size * SCALE)
end

local function InitializeAuraButton(auraButton, auraBorderOptions)
    auraButton:SetSize(GetDemoSize(AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))

    auraButton.Icon = auraButton:CreateTexture(nil, "BACKGROUND")
    auraButton.Icon:SetSize(GetDemoSize(ICON_SIZE), GetDemoSize(ICON_SIZE))
    auraButton.Icon:SetPoint("TOPLEFT", auraButton, "TOPLEFT", 0, 0)
    auraButton:SetIcon(auraButton.Icon)

    if auraBorderOptions then
        auraButton.AuraBorder = auraButton:CreateTexture(nil, "OVERLAY")
        auraButton.AuraBorder:SetTexture(AURA_BORDER_TEXTURE)
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
    auraButton:SetApplicationCount(auraButton.Count, { formatter = APPLICATION_COUNT_FORMATTER })
end

local function CreateAuraRow(parent, groupKey, filterString, yOffset, auraBorderOptions)
    local container = CreateFrame("AuraContainer", nil, parent, "CustomAuraContainerTemplate")
    container:SetPoint("TOPLEFT", parent, "TOPLEFT", 0, -GetDemoSize(yOffset))
    container:SetUnit("player")
    container:AddAuraGroup(groupKey, filterString, {
        maxFrameCount = MAX_BUFFS,
        initializeFrame = function(auraButton)
            InitializeAuraButton(auraButton, auraBorderOptions)
        end,
    })

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

    CreateAuraRow(frame, "helpful", "HELPFUL", 0, {
        showWhenHarmful = false,
        showWhenHelpful = true,
        style = AURA_BUTTON_BORDER_STYLE_COLOR,
    })
    CreateAuraRow(frame, "harmful", "HARMFUL", AURA_BUTTON_HEIGHT + ROW_GAP, {
        showWhenHarmful = true,
        showWhenHelpful = false,
        style = AURA_BUTTON_BORDER_STYLE_COLOR,
    })
end

After(0, CreateDemoFrame)
