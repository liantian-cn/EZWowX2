-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local After = C_Timer.After
local CreateColor = CreateColor
local CreateColorCurve = C_CurveUtil.CreateColorCurve
local CreateFrame = CreateFrame
local Linear = Enum.LuaCurveType.Linear
local RemainingDuration = Enum.DurationTextBindingProperty.RemainingDuration
local UIParent = UIParent

-- 插件级变量定义/引用
local GetUIScaleFactor = addonTable.GetUIScaleFactor

-- 本地变量定义
local MAX_BUFFS = 12
local ICON_SIZE = 32
local REMAINING_BLOCK_SIZE = 16
local REMAINING_UPDATE_INTERVAL = 0.1
local WHITE_TEXTURE = "Interface\\Buttons\\WHITE8X8"

local remainingCurve = CreateColorCurve()
remainingCurve:SetType(Linear)
remainingCurve:AddPoint(0.0, CreateColor(0, 0, 0, 1))
remainingCurve:AddPoint(5.0, CreateColor(100 / 255, 100 / 255, 100 / 255, 1))
remainingCurve:AddPoint(30.0, CreateColor(150 / 255, 150 / 255, 150 / 255, 1))
remainingCurve:AddPoint(155.0, CreateColor(200 / 255, 200 / 255, 200 / 255, 1))
remainingCurve:AddPoint(375.0, CreateColor(1, 1, 1, 1))

-- 代码部分
local function UpdateRemainingBlocks(buttons)
    for buttonIndex = 1, #buttons do
        local auraButton = buttons[buttonIndex]
        local color = auraButton.DurationTextBinding:GetFormattedTextColor()

        if color then
            auraButton.RemainingBlock:SetVertexColor(color:GetRGBA())
        else
            auraButton.RemainingBlock:SetVertexColor(0, 0, 0, 1)
        end
    end
end

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

    local auraButtons = {}
    for buffIndex = 1, MAX_BUFFS do
        local auraButton = CreateFrame("AuraButton", nil, container, "CustomAuraButtonTemplate")
        auraButton:SetSize(GetUIScaleFactor(ICON_SIZE), GetUIScaleFactor(ICON_SIZE))
        auraButton:SetPoint("TOPLEFT", container, "TOPLEFT", GetUIScaleFactor((buffIndex - 1) * ICON_SIZE), 0)

        auraButton.Icon = auraButton:CreateTexture(nil, "OVERLAY")
        auraButton.Icon:SetAllPoints(auraButton)
        auraButton:SetIcon(auraButton.Icon)

        auraButton.RemainingBlock = auraButton:CreateTexture(nil, "ARTWORK")
        auraButton.RemainingBlock:SetTexture(WHITE_TEXTURE)
        auraButton.RemainingBlock:SetSize(GetUIScaleFactor(REMAINING_BLOCK_SIZE), GetUIScaleFactor(REMAINING_BLOCK_SIZE))
        auraButton.RemainingBlock:SetPoint("TOP", auraButton, "BOTTOM", 0, 0)
        auraButton.RemainingBlock:SetVertexColor(0, 0, 0, 1)

        auraButton.DurationText = auraButton:CreateFontString(nil, "ARTWORK")
        auraButton.DurationText:SetPoint("CENTER", auraButton.RemainingBlock, "CENTER", 0, 0)
        auraButton.DurationText:SetAlpha(0)
        auraButton:SetDurationText(auraButton.DurationText)
        auraButton.DurationTextBinding:SetTextColorCurve(remainingCurve, RemainingDuration)

        auraButtons[buffIndex] = auraButton
        container:AddAuraFrame(auraButton)
    end

    frame.remainingUpdateElapsed = 0
    frame:SetScript("OnUpdate", function(self, elapsed)
        self.remainingUpdateElapsed = self.remainingUpdateElapsed + elapsed
        if self.remainingUpdateElapsed < REMAINING_UPDATE_INTERVAL then
            return
        end

        self.remainingUpdateElapsed = 0
        UpdateRemainingBlocks(auraButtons)
    end)
end

After(0, CreateDemoFrame)
