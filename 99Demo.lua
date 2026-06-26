-- 命名空间声明
local addonName, addonTable = ...

-- WOW API 缓存
local After = C_Timer.After
local CreateFrame = CreateFrame
local GetAuraDataByIndex = C_UnitAuras.GetAuraDataByIndex
local UIParent = UIParent

-- 插件级变量定义/引用
local GetUIScaleFactor = addonTable.GetUIScaleFactor

-- 本地变量定义
local MAX_BUFFS = 8

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

    local buffArea = CreateFrame("Frame", nil, frame)
    buffArea:SetPoint("TOPLEFT", frame, "TOPLEFT", 0, 0)
    buffArea:SetSize(GetUIScaleFactor(256), GetUIScaleFactor(32))

    frame.icons = {}
    for buffIndex = 1, MAX_BUFFS do
        local icon = buffArea:CreateTexture(nil, "ARTWORK")
        icon:SetPoint("LEFT", buffArea, "LEFT", GetUIScaleFactor((buffIndex - 1) * 32), 0)
        icon:SetSize(GetUIScaleFactor(32), GetUIScaleFactor(32))
        icon:Hide()
        frame.icons[buffIndex] = icon
    end

    function frame:RefreshBuffs()
        for buffIndex = 1, MAX_BUFFS do
            local aura = GetAuraDataByIndex("player", buffIndex, "HELPFUL")
            local icon = self.icons[buffIndex]
            if aura and aura.icon then
                icon:SetTexture(aura.icon)
                icon:Show()
            else
                icon:Hide()
            end
        end
    end

    frame:RegisterEvent("PLAYER_ENTERING_WORLD")
    frame:RegisterUnitEvent("UNIT_AURA", "player")
    frame:SetScript("OnEvent", function(self)
        self:RefreshBuffs()
    end)
    frame:RefreshBuffs()
end

After(0, CreateDemoFrame)
