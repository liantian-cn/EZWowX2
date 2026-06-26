-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local After = C_Timer.After
local CreateFrame = CreateFrame
local UIParent = UIParent

-- 插件级变量定义/引用
local GetUIScaleFactor = addonTable.GetUIScaleFactor

-- 本地变量定义
local MAX_BUFFS = 12

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
    container:SetSize(GetUIScaleFactor(256), GetUIScaleFactor(32))
    container:SetUnit("player")
    container:AddAuraFilter("HELPFUL", { maxFrameCount = MAX_BUFFS })

    for buffIndex = 1, MAX_BUFFS do
        local auraButton = CreateFrame("AuraButton", nil, container, "CustomAuraButtonTemplate")
        auraButton:SetSize(GetUIScaleFactor(32), GetUIScaleFactor(32))
        auraButton:SetPoint("TOPLEFT", container, "TOPLEFT", GetUIScaleFactor((buffIndex - 1) * 32), 0)

        auraButton.Icon = auraButton:CreateTexture(nil, "OVERLAY")
        auraButton.Icon:SetAllPoints(auraButton)
        auraButton:SetIcon(auraButton.Icon)

        container:AddAuraFrame(auraButton)
    end
end

After(0, CreateDemoFrame)
