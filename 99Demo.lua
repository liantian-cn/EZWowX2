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
local ICON_SIZE = 32
local REMAINING_BLOCK_SIZE = 32
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"

-- 代码部分
local function CreateDemoFrame()
    local frame = CreateFrame("Frame", addonName .. "DemoBuffFrame", UIParent)
    frame:SetPoint("CENTER", UIParent, "CENTER", 0, 0)
    frame:SetSize(GetUIScaleFactor(400), GetUIScaleFactor(200))
    frame:SetFrameStrata("HIGH")
    frame:SetFrameLevel(100)
    frame:Show()

    frame.bg = frame:CreateTexture(nil, "BACKGROUND")
    frame.bg:SetAllPoints(frame)
    frame.bg:SetColorTexture(0, 0, 0, 0.65)

    local container = CreateFrame("AuraContainer", nil, frame, "CustomAuraContainerTemplate")
    container:SetPoint("TOPLEFT", frame, "TOPLEFT", 0, 0)
    container:SetSize(GetUIScaleFactor(MAX_BUFFS * ICON_SIZE), GetUIScaleFactor(ICON_SIZE + REMAINING_BLOCK_SIZE))
    container:SetUnit("player")
    container:AddAuraFilter("HELPFUL", { maxFrameCount = MAX_BUFFS })

    for buffIndex = 1, MAX_BUFFS do
        local auraButton = CreateFrame("AuraButton", nil, container, "CustomAuraButtonTemplate")
        auraButton:SetSize(GetUIScaleFactor(ICON_SIZE), GetUIScaleFactor(ICON_SIZE))
        auraButton:SetPoint("TOPLEFT", container, "TOPLEFT", GetUIScaleFactor((buffIndex - 1) * ICON_SIZE), 0)

        auraButton.Icon = auraButton:CreateTexture(nil, "OVERLAY")
        auraButton.Icon:SetAllPoints(auraButton)
        auraButton:SetIcon(auraButton.Icon)

        auraButton.DurationBar = CreateFrame("StatusBar", nil, auraButton)
        auraButton.DurationBar:SetSize(GetUIScaleFactor(REMAINING_BLOCK_SIZE), GetUIScaleFactor(REMAINING_BLOCK_SIZE))
        auraButton.DurationBar:SetPoint("TOP", auraButton, "BOTTOM", 0, 0)
        auraButton.DurationBar:SetOrientation("HORIZONTAL")
        auraButton.DurationBar:SetStatusBarTexture(WHITE_TEXTURE)
        auraButton.DurationBar:SetStatusBarColor(1, 1, 1, 1)

        auraButton.DurationBar.Background = auraButton.DurationBar:CreateTexture(nil, "BACKGROUND")
        auraButton.DurationBar.Background:SetAllPoints(auraButton.DurationBar)
        auraButton.DurationBar.Background:SetColorTexture(0, 0, 0, 1)

        auraButton:SetDurationBar(auraButton.DurationBar, { interpolation = Immediate, direction = RemainingTime })

        container:AddAuraFrame(auraButton)
    end
end

After(0, CreateDemoFrame)
