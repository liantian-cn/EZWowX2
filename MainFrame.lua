local addonName, addonTable = ...
local log                   = addonTable.logging
local fontFile, _, _        = GameFontNormal:GetFont()



-- UI缩放计算函数，用于将设计像素转换为实际游戏中的像素值
-- @param pixelValue 设计像素值
-- @return 转换后的实际像素值
local function GetUIScaleFactor(pixelValue)
    local _, physicalHeight = GetPhysicalScreenSize()
    local logicalHeight = GetScreenHeight()
    return (pixelValue * logicalHeight) / physicalHeight
end








addonTable.SPELL_CD_MAX      = 16
addonTable.SpellCD           = {}

addonTable.SPELL_CHARGE_MAX  = 5
addonTable.SpellChargeCD     = {}

addonTable.PLAYER_BUFF_MAX   = 28

addonTable.PLAYER_DEBUFF_MAX = 11
addonTable.TARGET_DEBUFF_MAX = 11


addonTable.PARTY_AURA_MAX = 6
for i = 1, 4 do
    local UnitKey = string.format("%s%d", "party", i)
    addonTable[UnitKey .. "BuffIcon"] = {}
    addonTable[UnitKey .. "BuffCurve"] = {}
    addonTable[UnitKey .. "DebuffIcon"] = {}
    addonTable[UnitKey .. "DebuffCurve"] = {}
end



-- 初始化插件的主函数
-- 创建插件的主框架以及所有子框架，包括玩家状态、冷却时间、增益/减益效果等显示区域
local function InitializeMainFrame()
    -- 计算UI元素尺寸
    addonTable.nodeSize = GetUIScaleFactor(32)
    local node_size = addonTable.nodeSize
    -- 创建主框架
    addonTable.MainFrame = CreateFrame("Frame", addonName .. "MainFrame", UIParent)
    addonTable.MainFrame:SetPoint("TOPRIGHT", UIParent, "TOPRIGHT", 0, 0)
    addonTable.MainFrame:SetSize(node_size * 30, node_size * 12)
    addonTable.MainFrame:SetFrameStrata("TOOLTIP")
    addonTable.MainFrame:SetFrameLevel(900)
    addonTable.MainFrame:Show()

    addonTable.MainFrameTexture = addonTable.MainFrame:CreateTexture(nil, "BACKGROUND")
    addonTable.MainFrameTexture:SetAllPoints()
    addonTable.MainFrameTexture:SetColorTexture(0, 0, 0, 1)
    addonTable.MainFrameTexture:Show()


    addonTable.PlayerBuffFrame = CreateFrame("Frame", addonName .. "PlayerBuffFrame", addonTable.MainFrame)
    addonTable.PlayerBuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerBuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 1 * node_size, -1 * node_size)
    addonTable.PlayerBuffFrame:SetSize(node_size * addonTable.PLAYER_BUFF_MAX, node_size * 2)
    addonTable.PlayerBuffFrame:Show()

    if addonTable.DEBUG then
        addonTable.PlayerBuffFrameTexture = addonTable.PlayerBuffFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerBuffFrameTexture:SetAllPoints()
        addonTable.PlayerBuffFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerBuffFrameTexture:Show()
    end


    addonTable.PlayerStatusFrame = CreateFrame("Frame", addonName .. "PlayerStatusFrame", addonTable.MainFrame)
    addonTable.PlayerStatusFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerStatusFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 1 * node_size, -3 * node_size)
    addonTable.PlayerStatusFrame:SetSize(1 * node_size, 2 * node_size)
    addonTable.PlayerStatusFrame:Show()

    if addonTable.DEBUG then
        addonTable.PlayerStatusFrameTexture = addonTable.PlayerStatusFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerStatusFrameTexture:SetAllPoints()
        addonTable.PlayerStatusFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 1)
        addonTable.PlayerStatusFrameTexture:Show()
    end

    addonTable.PlayerSpellCDFrame = CreateFrame("Frame", addonName .. "PlayerSpellCDFrame", addonTable.MainFrame)
    addonTable.PlayerSpellCDFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerSpellCDFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 2 * node_size, -3 * node_size)
    addonTable.PlayerSpellCDFrame:SetSize(node_size * addonTable.SPELL_CD_MAX, 2 * node_size)
    addonTable.PlayerSpellCDFrame:Show()

    if addonTable.DEBUG then
        addonTable.PlayerSpellCDFrameTexture = addonTable.PlayerSpellCDFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerSpellCDFrameTexture:SetAllPoints()
        addonTable.PlayerSpellCDFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
        addonTable.PlayerSpellCDFrameTexture:Show()
    end

    addonTable.PlayerChargeFrame = CreateFrame("Frame", addonName .. "PlayerChargeFrame", addonTable.MainFrame)
    addonTable.PlayerChargeFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerChargeFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 18 * node_size, -3 * node_size)
    addonTable.PlayerChargeFrame:SetSize(node_size * addonTable.SPELL_CHARGE_MAX, 2 * node_size)
    addonTable.PlayerChargeFrame:Show()
    if addonTable.DEBUG then
        addonTable.PlayerChargeFrameTexture = addonTable.PlayerChargeFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerChargeFrameTexture:SetAllPoints()
        addonTable.PlayerChargeFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
        addonTable.PlayerChargeFrameTexture:Show()
    end


    addonTable.PlayerDebuffFrame = CreateFrame("Frame", addonName .. "PlayerDebuffFrame", addonTable.MainFrame)
    addonTable.PlayerDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.PlayerDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 1 * node_size, -5 * node_size)
    addonTable.PlayerDebuffFrame:SetSize(node_size * addonTable.PLAYER_DEBUFF_MAX, node_size * 2)
    addonTable.PlayerDebuffFrame:Show()

    if addonTable.DEBUG then
        addonTable.PlayerDebuffFrameTexture = addonTable.PlayerDebuffFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.PlayerDebuffFrameTexture:SetAllPoints()
        addonTable.PlayerDebuffFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
        addonTable.PlayerDebuffFrameTexture:Show()
    end


    addonTable.TargetDebuffFrame = CreateFrame("Frame", addonName .. "TargetDebuffFrame", addonTable.MainFrame)
    addonTable.TargetDebuffFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.TargetDebuffFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 12 * node_size, -5 * node_size)
    addonTable.TargetDebuffFrame:SetSize(node_size * addonTable.TARGET_DEBUFF_MAX, node_size * 2)
    addonTable.TargetDebuffFrame:Show()

    if addonTable.DEBUG then
        addonTable.TargetDebuffFrameTexture = addonTable.TargetDebuffFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.TargetDebuffFrameTexture:SetAllPoints()
        addonTable.TargetDebuffFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
        addonTable.TargetDebuffFrameTexture:Show()
    end


    addonTable.MiscFrame = CreateFrame("Frame", addonName .. "MiscFrame", addonTable.MainFrame)
    addonTable.MiscFrame:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
    addonTable.MiscFrame:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", 23 * node_size, -3 * node_size)
    addonTable.MiscFrame:SetSize(node_size * 6, node_size * 3)
    addonTable.MiscFrame:Show()

    if addonTable.DEBUG then
        addonTable.MiscFrameTexture = addonTable.MiscFrame:CreateTexture(nil, "BACKGROUND")
        addonTable.MiscFrameTexture:SetAllPoints()
        addonTable.MiscFrameTexture:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
        addonTable.MiscFrameTexture:Show()
    end


    for i = 1, 4 do
        local UnitKey = string.format("%s%d", "party", i)





        addonTable["PartyFrame" .. UnitKey] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey, addonTable.MainFrame)
        addonTable["PartyFrame" .. UnitKey]:SetFrameLevel(addonTable.MainFrame:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey]:SetPoint("TOPLEFT", addonTable.MainFrame, "TOPLEFT", (7 * i - 6) * node_size, -7 * node_size)
        addonTable["PartyFrame" .. UnitKey]:SetSize(node_size * 7, node_size * 4)
        addonTable["PartyFrame" .. UnitKey]:Show()


        addonTable["PartyFrame" .. UnitKey .. "StatusFrame"] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey .. "StatusFrame", addonTable["PartyFrame" .. UnitKey])
        addonTable["PartyFrame" .. UnitKey .. "StatusFrame"]:SetFrameLevel(addonTable["PartyFrame" .. UnitKey]:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey .. "StatusFrame"]:SetPoint("TOPLEFT", addonTable["PartyFrame" .. UnitKey], "TOPLEFT", 0, 0)
        addonTable["PartyFrame" .. UnitKey .. "StatusFrame"]:SetSize(node_size * 1, node_size * 4)
        addonTable["PartyFrame" .. UnitKey .. "StatusFrame"]:Show()

        if addonTable.DEBUG then
            addonTable["PartyFrame" .. UnitKey .. "StatusFrameTexture"] = addonTable["PartyFrame" .. UnitKey .. "StatusFrame"]:CreateTexture(nil, "BACKGROUND")
            addonTable["PartyFrame" .. UnitKey .. "StatusFrameTexture"]:SetAllPoints()
            addonTable["PartyFrame" .. UnitKey .. "StatusFrameTexture"]:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
            addonTable["PartyFrame" .. UnitKey .. "StatusFrameTexture"]:Show()
        end

        addonTable["PartyFrame" .. UnitKey .. "BuffFrame"] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey .. "BuffFrame", addonTable["PartyFrame" .. UnitKey])
        addonTable["PartyFrame" .. UnitKey .. "BuffFrame"]:SetFrameLevel(addonTable["PartyFrame" .. UnitKey]:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey .. "BuffFrame"]:SetPoint("TOPLEFT", addonTable["PartyFrame" .. UnitKey], "TOPLEFT", 1 * node_size, 0)
        addonTable["PartyFrame" .. UnitKey .. "BuffFrame"]:SetSize(node_size * 6, node_size * 2)
        addonTable["PartyFrame" .. UnitKey .. "BuffFrame"]:Show()

        if addonTable.DEBUG then
            addonTable["PartyFrame" .. UnitKey .. "BuffFrameTexture"] = addonTable["PartyFrame" .. UnitKey .. "BuffFrame"]:CreateTexture(nil, "BACKGROUND")
            addonTable["PartyFrame" .. UnitKey .. "BuffFrameTexture"]:SetAllPoints()
            addonTable["PartyFrame" .. UnitKey .. "BuffFrameTexture"]:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
            addonTable["PartyFrame" .. UnitKey .. "BuffFrameTexture"]:Show()
        end

        addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"] = CreateFrame("Frame", addonName .. "PartyFrame" .. UnitKey .. "DebuffFrame", addonTable["PartyFrame" .. UnitKey])
        addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"]:SetFrameLevel(addonTable["PartyFrame" .. UnitKey]:GetFrameLevel() + 1)
        addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"]:SetPoint("TOPLEFT", addonTable["PartyFrame" .. UnitKey], "TOPLEFT", 1 * node_size, -2 * node_size)
        addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"]:SetSize(node_size * 6, node_size * 2)
        addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"]:Show()

        if addonTable.DEBUG then
            addonTable["PartyFrame" .. UnitKey .. "DebuffFrameTexture"] = addonTable["PartyFrame" .. UnitKey .. "DebuffFrame"]:CreateTexture(nil, "BACKGROUND")
            addonTable["PartyFrame" .. UnitKey .. "DebuffFrameTexture"]:SetAllPoints()
            addonTable["PartyFrame" .. UnitKey .. "DebuffFrameTexture"]:SetColorTexture(math.random(), math.random(), math.random(), 0.5)
            addonTable["PartyFrame" .. UnitKey .. "DebuffFrameTexture"]:Show()
        end
    end

    log("MainFrame created")
end

table.insert(addonTable.FrameInitFuncs, InitializeMainFrame)









local function InitializeTargetDebuffFrame2()
    addonTable.CreateAuraSequence("target", "HARMFUL|PLAYER", 11, "TargetDebuff", addonTable.TargetDebuffFrame, Enum.UnitAuraSortRule.Default, Enum.UnitAuraSortDirection.Normal)
end
table.insert(addonTable.FrameInitFuncs, InitializeTargetDebuffFrame2)
