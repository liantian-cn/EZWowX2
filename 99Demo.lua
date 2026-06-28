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
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"

-- 代码部分
local function GetDemoSize(size)
    return GetUIScaleFactor(size * SCALE)
end

local function CreateDemoFrame()
    local frame = CreateFrame("Frame", addonName .. "DemoBuffFrame", UIParent)
    frame:SetPoint("CENTER", UIParent, "CENTER", 0, 0)
    frame:SetSize(GetDemoSize(MAX_BUFFS * AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))
    frame:SetFrameStrata("HIGH")
    frame:SetFrameLevel(100)
    frame:Show()

    frame.bg = frame:CreateTexture(nil, "BACKGROUND")
    frame.bg:SetAllPoints(frame)
    frame.bg:SetColorTexture(0, 0, 0, 0.65)

    local container = CreateFrame("AuraContainer", nil, frame, "CustomAuraContainerTemplate")
    container:SetPoint("TOPLEFT", frame, "TOPLEFT", 0, 0)
    container:SetSize(GetDemoSize(MAX_BUFFS * AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))
    container:SetUnit("player")
    container:AddAuraFilter("HELPFUL", { maxFrameCount = MAX_BUFFS })

    for buffIndex = 1, MAX_BUFFS do
        local auraButton = CreateFrame("AuraButton", nil, container, "CustomAuraButtonTemplate")
        auraButton:SetSize(GetDemoSize(AURA_BUTTON_WIDTH), GetDemoSize(AURA_BUTTON_HEIGHT))
        auraButton:SetPoint("TOPLEFT", container, "TOPLEFT", GetDemoSize((buffIndex - 1) * AURA_BUTTON_WIDTH), 0)

        auraButton.Icon = auraButton:CreateTexture(nil, "OVERLAY")
        auraButton.Icon:SetSize(GetDemoSize(ICON_SIZE), GetDemoSize(ICON_SIZE))
        auraButton.Icon:SetPoint("TOPLEFT", auraButton, "TOPLEFT", 0, 0)
        auraButton:SetIcon(auraButton.Icon)

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

        container:AddAuraFrame(auraButton)
    end
end

After(0, CreateDemoFrame)
